from rest_framework import serializers

from customer.models import CustomerPurchase
from mall.models import Mall
from product.models import Product
from tenant.models import RetailUnit, Tenant
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from customer.services import create_offline_purchase, InsufficientStock


class TenantBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name"]

class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "name",
            "email",
            "phone",
        ]

class TenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "email",
            "phone",
        ]
        read_only_fields = ["id"]
class RetailCreateSerializer(serializers.ModelSerializer):
    # tenant=TenantCreateSerializer()

    class Meta:
        model=RetailUnit
        fields=[
            "id",
            "title",
            "leased_date",
            "leased_tenure",
            "renewal_date",
            "monthly_rent",
            # "tenant"
        ]
        # read_only_fields = ["id"]

class RetailUpdateSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = RetailUnit
        fields = [
            "id",
            "title",
            "leased_date",
            "leased_tenure",
            "renewal_date",
            "monthly_rent",
            "tenant",
        ]
        extra_kwargs = {
            "id": {"read_only": False, "required": False},
            "leased_date": {"required": False, "allow_null": True},
            "leased_tenure": {"required": False, "allow_null": True},
            "renewal_date": {"required": False, "allow_null": True},
            "monthly_rent": {"required": False, "allow_null": True},
        }
class RetailReadSerializer(serializers.ModelSerializer):
    tenant=TenantCreateSerializer()

    class Meta:
        model=RetailUnit
        fields=[
            "id",
            "title",
            "leased_date",
            "leased_tenure",
            "renewal_date",
            "monthly_rent",
            "tenant"
        ]
        read_only_fields = ["id"]
    



class MallBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mall
        fields = ["id", "name"]


class RetailUnitSerializer(serializers.ModelSerializer):
    mall = serializers.CharField(source="mall.name", read_only=True)

    class Meta:
        model = RetailUnit
        fields = ["id", "title", "mall"]


class ProductSerializer(serializers.ModelSerializer):
    retail_unit = serializers.CharField(source="retail_unit.title", read_only=True)
    stock = serializers.IntegerField(source="stock_quantity", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name","image", "stock", "retail_unit","price"]


def ensure_retail_unit_belongs_to_tenant(serializer, tenant):
   
    retail_unit = serializer.validated_data.get("retail_unit")

    if retail_unit is not None and retail_unit.tenant_id != tenant.pk:
        raise serializers.ValidationError(
            {"retail_unit": ["Invalid retail unit."]}
        )



class ProductWriteSerializer(serializers.ModelSerializer):
    retail_unit = serializers.PrimaryKeyRelatedField(
        queryset=RetailUnit.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "retail_unit",
            "name",
            "image",
            "description",
            "price",
            "stock_quantity",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_retail_unit(self, value):
        request = self.context.get("request")
        tenant = getattr(
            getattr(request, "user", None),
            "tenant_profile",
            None
        )

        if tenant is None:
            raise serializers.ValidationError(
                "User does not have a tenant profile."
            )

        if value.tenant_id != tenant.id:
            raise serializers.ValidationError(
                "This retail unit does not belong to your tenant."
            )

        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Price cannot be negative."
            )
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )
        return value


class RetailUnitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailUnit
        fields = [
            "id",
            "mall",
            "title",
            "leased_date",
            "leased_tenure",
            "renewal_date",
            "monthly_rent",
        ]

    def validate_leased_tenure(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Lease tenure must be a positive number of months.")
        return value

    def validate_monthly_rent(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Monthly rent cannot be negative.")
        return value

    def validate(self, attrs):
        leased_date = attrs.get("leased_date")
        renewal_date = attrs.get("renewal_date")
        if leased_date and renewal_date and renewal_date <= leased_date:
            raise serializers.ValidationError(
                {"renewal_date": "Renewal date must be after the lease start date."}
            )

        mall = attrs.get("mall")
        title = attrs.get("title")
        if mall and title and RetailUnit.objects.filter(mall=mall, title__iexact=title).exists():
            raise serializers.ValidationError(
                {"title": "A unit with this title already exists in this mall."}
            )
        return attrs


class RetailUnitDetailSerializer(serializers.ModelSerializer):
    mall = MallBriefSerializer(read_only=True)
    lease_status = serializers.CharField(source="lease_status_label", read_only=True)

    class Meta:
        model = RetailUnit
        fields = [
            "id",
            "title",
            "mall",
            "leased",
            "leased_date",
            "leased_tenure",
            "renewal_date",
            "monthly_rent",
            "lease_status",
        ]