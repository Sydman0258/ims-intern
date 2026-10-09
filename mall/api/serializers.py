from mall.api.pagination import MallPaginationView
from rest_framework import serializers

from mall.models import Mall
from tenant.models import Tenant, RetailUnit
from tenant.api.serializers import RetailCreateSerializer, RetailReadSerializer, RetailUpdateSerializer, TenantCreateSerializer



class MallListSerializer(serializers.ModelSerializer):
      tenant_count = serializers.IntegerField(read_only=True)
      unit_count = serializers.IntegerField(read_only=True)    

      class Meta:
            model=Mall
            fields=[
                  "id","name", "floors","total_shops","num_leased","tenant_count","unit_count"
            ]
# class MallListSerializer(serializers.Serializer):
   
#     id=serializers.IntegerField(read_only=True)
#     name=serializers.CharField(max_length=225)
#     floors=serializers.IntegerField()
#     total_shops=serializers.IntegerField()
#     num_leased=serializers.IntegerField()
#     tenant_count = serializers.IntegerField(read_only=True)
#     unit_count = serializers.IntegerField(read_only=True)    
  


class MallBriefSerializer(serializers.ModelSerializer):

      class Meta:
            model=Mall
            fields=[
                  "id","name","floors","total_shops","num_leased"
            ]

# class MallBriefSerializer(serializers.Serializer):

#         id=serializers.IntegerField(read_only=True)
#         name=serializers.CharField(max_length=225)
#         floors=serializers.IntegerField()
#         total_shops=serializers.IntegerField()
#         num_leased=serializers.IntegerField()
   
class TenantInMallSerializer(serializers.ModelSerializer):
    unit_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "unit_count", 
        ]

# class TenantInMallSerializer(serializers.Serializer):
#     unit_count = serializers.IntegerField(read_only=True)
#     id=serializers.IntegerField(read_only=True)
#     name=serializers.CharField(max_length=225)
#     email = serializers.CharField(max_length=255)
#     phone=serializers.IntegerField()

class RetailUnitInMallSerializer(serializers.ModelSerializer):
    tenant = serializers.CharField(source="tenant.name", allow_null=True, read_only=True)
    lease_status = serializers.CharField(source="lease_status_label", read_only=True)

    class Meta:
        model = RetailUnit
        fields = [
            "id",
            "title",
            "leased",
            "monthly_rent",
            "tenant",
            "lease_status",
        ]

# class RetailUnitInMallSerializer(serializers.Serializer):
#     tenant = serializers.CharField(source="tenant.name", allow_null=True, read_only=True)
#     lease_status = serializers.CharField(source="lease_status_label", read_only=True)
#     id=serializers.IntegerField(read_only=True)
#     title=serializers.CharField(max_length=225)
#     leased=serializers.BooleanField(default=True)
#     monthly_rent=serializers.DecimalField(max_digits=12,decimal_places=2)

class MallCreateSerializer(serializers.ModelSerializer):
    retail_units = RetailCreateSerializer(
        many=True,
        source="retail_unit"
    )

    class Meta:
        model = Mall
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "floors",
            "total_shops",
            "num_leased",
            "retail_units",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "num_leased",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        retail_units_data = validated_data.pop("retail_unit")

        mall = Mall.objects.create(**validated_data)

        for retail_unit_data in retail_units_data:
            RetailUnit.objects.create(
                mall=mall,
                **retail_unit_data
            )

        return mall
    def update(self, instance, validated_data):
        retail_units_data = validated_data.pop("retail_unit", [])

        # Update Mall
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update RetailUnits
        for retail_unit_data in retail_units_data:
            retail_unit_id = retail_unit_data.pop("id", None)

            tenant_data = retail_unit_data.pop("tenant", None)

            if retail_unit_id:
                retail_unit = RetailUnit.objects.get(
                    id=retail_unit_id,
                    mall=instance
                )

                # Update RetailUnit fields
                for attr, value in retail_unit_data.items():
                    setattr(retail_unit, attr, value)

                # Update Tenant
                if tenant_data:
                    tenant = retail_unit.tenant

                    if tenant:
                        for attr, value in tenant_data.items():
                            setattr(tenant, attr, value)

                        tenant.save()

                retail_unit.save()

        return instance
class MallUpdateSerializer(serializers.ModelSerializer):
    retail_units = RetailUpdateSerializer(
        many=True,
        source="retail_unit"
    )

    class Meta:
        model = Mall
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "floors",
            "total_shops",
            "num_leased",
            "retail_units",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "num_leased",
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):

        retail_units_data = validated_data.pop("retail_unit", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if retail_units_data is not None:
            kept_ids = []

        for unit_data in retail_units_data:
            unit_data = dict(unit_data)
            retail_unit_id = unit_data.pop("id", None)
            # PrimaryKeyRelatedField → Tenant instance or None
            tenant = unit_data.pop("tenant", None)

            if retail_unit_id:
                retail_unit = RetailUnit.objects.get(id=retail_unit_id, mall=instance)
                for attr, value in unit_data.items():
                    setattr(retail_unit, attr, value)
                retail_unit.tenant = tenant  # existing only, or None to unassign
                retail_unit.save()
            else:
                retail_unit = RetailUnit.objects.create(
                    mall=instance,
                    tenant=tenant,
                    **unit_data,
                )

            kept_ids.append(retail_unit.id)

        instance.retail_unit.exclude(id__in=kept_ids).delete()

        return instance

class MallReadSerializer(serializers.ModelSerializer):
    retail_units=RetailReadSerializer(many=True,source="retail_unit")
    class Meta:
             model = Mall
             fields = [
                 "id",
                 "name",
                 "email",
                 "phone",
                 "floors",
                 "total_shops",
                 "num_leased",
                 "retail_units",
                 "created_at",
                 "updated_at",
                 
             ]
             read_only_fields = [
                 "id",
                 "num_leased",
                 "created_at",
                 "updated_at",
             ]