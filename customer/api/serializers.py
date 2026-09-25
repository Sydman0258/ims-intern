from rest_framework import serializers

from customer.models import Customer, CustomerPurchase, CustomerPurchaseItem


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
