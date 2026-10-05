from rest_framework import serializers

from customer.models import CustomerPurchase
from mall.models import Mall
from product.models import Product
from tenant.models import RetailUnit, Tenant


class TenantBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name"]


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
        fields = ["id", "name", "stock", "retail_unit"]


def ensure_retail_unit_belongs_to_tenant(serializer, tenant):
   
    retail_unit = serializer.validated_data.get("retail_unit")

    if retail_unit is not None and retail_unit.tenant_id != tenant.pk:
        raise serializers.ValidationError(
            {"retail_unit": ["Invalid retail unit."]}
        )
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ProductWriteSerializer(serializers.ModelSerializer):
    retail_unit = serializers.PrimaryKeyRelatedField(
        queryset=RetailUnit.objects.none()
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "retail_unit",
            "name",
            "description",
            "price",
            "stock_quantity",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = getattr(getattr(request, "user", None), "tenant_profile", None)

        if tenant is not None:
            self.fields["retail_unit"].queryset = RetailUnit.objects.filter(
                tenant=tenant
            )

    def validate_price(self, value):
        if value < 0:
            raise ValidationError("Price cannot be negative.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise ValidationError("Stock cannot be negative.")
        return value

    # def validate(self, attrs):
    #     request = self.context.get("request")
    #     tenant = getattr(getattr(request, "user", None), "tenant_profile", None)

    #     if not RetailUnit.objects.filter(tenant=tenant).exists():
    #         raise ValidationError({"detail": "No retail store assigned yet."})

    #     retail_unit = attrs.get("retail_unit")
    #     if retail_unit and retail_unit.tenant_id != tenant.pk:
    #         raise ValidationError({"retail_unit": ["Invalid retail unit."]})

    #     return attrs

    # def create(self, validated_data):
    #     return Product.objects.create(**validated_data)   

class RecentPurchaseSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="customer.name", read_only=True)
    retail_unit = serializers.CharField(
        source="retail_unit.title", allow_null=True, read_only=True
    )
    total = serializers.DecimalField(
        source="total_amount", max_digits=12, decimal_places=2, read_only=True
    )
    date = serializers.DateTimeField(source="purchase_date", read_only=True)

    class Meta:
        model = CustomerPurchase
        fields = ["id", "customer", "retail_unit", "total", "date"]

class RecordPurchaseWriteSerializer(serializers.ModelSerializer):
    """Write serializer for POST /api/tenant/record-sale/."""

    retail_unit = serializers.PrimaryKeyRelatedField(
        queryset=RetailUnit.objects.none(), write_only=True
    )
    customer_name = serializers.CharField(max_length=100, write_only=True)
    customer_phone = serializers.CharField(max_length=20, write_only=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(), write_only=True
    )
    quantity = serializers.IntegerField(min_value=1, write_only=True)
    payment_method = serializers.ChoiceField(
        choices=[
            ("Cash", "Cash"),
            ("Card", "Card"),
            ("UPI", "UPI"),
            ("Other", "Other"),
        ],
        write_only=True,
        default="Cash",
    )

    customer = serializers.CharField(source="customer.name", read_only=True)
    retail_unit_display = serializers.CharField(
        source="retail_unit.title", allow_null=True, read_only=True
    )
    total = serializers.DecimalField(
        source="total_amount", max_digits=12, decimal_places=2, read_only=True
    )
    date = serializers.DateTimeField(source="purchase_date", read_only=True)

    class Meta:
        model = CustomerPurchase
        fields = [
            "id",
            "retail_unit",
            "customer_name",
            "customer_phone",
            "product",
            "quantity",
            "payment_method",
            "customer",
            "retail_unit_display",
            "total",
            "date",
        ]
        read_only_fields = ["id", "customer", "retail_unit_display", "total", "date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        tenant = getattr(getattr(request, "user", None), "tenant_profile", None)

        if tenant is not None:
            self.fields["retail_unit"].queryset = (
                RetailUnit.objects
                .filter(tenant=tenant)
                .select_related("mall")
                .order_by("title")
            )
            self.fields["product"].queryset = (
                Product.objects
                .filter(retail_unit__tenant=tenant, stock_quantity__gt=0)
                .select_related("retail_unit")
                .order_by("name")
            )

    def validate(self, attrs):
        unit = attrs.get("retail_unit")
        product = attrs.get("product")
        qty = attrs.get("quantity")

        if unit and product and product.retail_unit_id != unit.id:
            raise serializers.ValidationError(
                {"product": "This product does not belong to the selected retail store."}
            )
        if product and qty and product.stock_quantity < qty:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock_quantity} in stock."}
            )
        return attrs

    def create(self, validated_data):          # ← THIS is what was missing
        from customer.services import create_offline_purchase, InsufficientStock

        request = self.context["request"]
        tenant = request.user.tenant_profile

        product = validated_data.pop("product")
        quantity = validated_data.pop("quantity")
        customer_name = validated_data.pop("customer_name")
        customer_phone = validated_data.pop("customer_phone")
        payment_method = validated_data.pop("payment_method", "Cash")
        retail_unit = validated_data.pop("retail_unit")

        try:
            return create_offline_purchase(
                tenant=tenant,
                retail_unit=retail_unit,
                name=customer_name,
                phone=customer_phone,
                items=[{"product_id": product.pk, "quantity": quantity}],
                payment_method=payment_method,
            )
        except InsufficientStock as exc:
            raise serializers.ValidationError({"quantity": [str(exc)]})
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