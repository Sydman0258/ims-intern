from rest_framework import serializers

from mall.models import Mall
from tenant.models import Tenant, RetailUnit




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

