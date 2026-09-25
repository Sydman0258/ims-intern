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
