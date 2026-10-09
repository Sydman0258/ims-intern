from customer.services import InsufficientStock, create_offline_purchase
from product.models import Product
from rest_framework import serializers

from customer.models import Customer, CustomerPurchase, CustomerPurchaseItem
from tenant.models import RetailUnit


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "email"]


class PurchaseItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = CustomerPurchaseItem
        fields = ["product", "quantity", "unit_price", "total_price"]


class PurchaseListSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="customer.name", read_only=True)
    tenant = serializers.CharField(source="tenant.name", read_only=True)
    retail_unit = serializers.CharField(
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
            "customer",
            "tenant",
            "retail_unit",
            "total",
            "full_paid",
            "date",
        ]


class PurchaseDetailSerializer(PurchaseListSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)

    class Meta(PurchaseListSerializer.Meta):
        fields = PurchaseListSerializer.Meta.fields + ["items"]

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

class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=[
            "id","name","stock"
        ]
class RecordPurchaseItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = serializers.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        tenant = getattr(
            getattr(request, "user", None),
            "tenant_profile",
            None
        )

        if tenant is not None:
            self.fields["product"].queryset = (
                Product.objects
                .filter(retail_unit__tenant=tenant)
                .select_related("retail_unit")
                .order_by("name")
            )

class RecordPurchaseWriteSerializer(serializers.ModelSerializer):

    retail_unit = serializers.PrimaryKeyRelatedField(
        queryset=RetailUnit.objects.none(), write_only=True
    )
    customer_name = serializers.CharField(max_length=100, write_only=True)
    customer_phone = serializers.CharField(max_length=20, write_only=True)
    items = RecordPurchaseItemWriteSerializer(many=True, write_only=True)
    payment_method = serializers.ChoiceField(
        choices=[
            ("cash", "Cash"),
            ("card", "Card"),
            ("upi", "UPI"),
            ("other", "Other"),
        ],
        write_only=True,
        default="cash",
    )

    # Read-only response fields
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
            "items",
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

    def validate(self, attrs):
        unit = attrs.get("retail_unit")
        items = attrs.get("items", [])

        if not items:
            raise serializers.ValidationError({"items": "At least one item is required."})

        for item in items:
            product = item["product"]
            qty = item["quantity"]

            if product.retail_unit_id != unit.id:
                raise serializers.ValidationError(
                    {"items": f"Product '{product.name}' does not belong to the selected retail unit."}
                )
            if product.stock_quantity < qty:
                raise serializers.ValidationError(
                    {"items": f"Only {product.stock_quantity} of '{product.name}' in stock."}
                )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        tenant = request.user.tenant_profile

        items_data = validated_data.pop("items")
        customer_name = validated_data.pop("customer_name")
        customer_phone = validated_data.pop("customer_phone")
        payment_method = validated_data.pop("payment_method", "cash")
        retail_unit = validated_data.pop("retail_unit")

        # Convert to the format your service expects
        service_items = [
            {"product_id": item["product"].pk, "quantity": item["quantity"]}
            for item in items_data
        ]

        try:
            return create_offline_purchase(
                tenant=tenant,
                retail_unit=retail_unit,
                name=customer_name,
                phone=customer_phone,
                items=service_items,
                payment_method=payment_method,
            )
        except InsufficientStock as exc:
            raise serializers.ValidationError({"items": [str(exc)]})