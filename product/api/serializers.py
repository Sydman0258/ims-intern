from rest_framework import serializers

from product.models import Product
from tenant.models import RetailUnit


class ProductListSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source="stock_quantity", read_only=True)
    retail_unit = serializers.CharField(
        source="retail_unit.title", allow_null=True, read_only=True
    )
    mall = serializers.CharField(
        source="retail_unit.mall.name", allow_null=True, read_only=True
    )
    tenant = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "status",
            "retail_unit",
            "mall",
            "tenant",
        ]

    def get_tenant(self, obj):
        if obj.retail_unit and obj.retail_unit.tenant:
            return obj.retail_unit.tenant.name
        return None


class ProductDetailSerializer(ProductListSerializer):
    stock = serializers.IntegerField(source="stock_quantity")

    retail_unit_id = serializers.PrimaryKeyRelatedField(
        source="retail_unit",
        queryset=RetailUnit.objects.all(),
        write_only=True,
    )

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["retail_unit_id"]
