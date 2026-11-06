

from django_filters import rest_framework as filters

from product.models import Product


class ProductFilter(filters.FilterSet):
    min_price=filters.NumberFilter(field_name="price",lookup_expr='gte')
    max_price=filters.NumberFilter(field_name="price",lookup_expr='lte')
    min_stock=filters.NumberFilter(field_name="stock_quantity", lookup_expr='gte')
    max_Stock=filters.NumberFilter(field_name="stock_quantity",lookup_expr="lte")
    retail_unit=filters.NumberFilter(field_name="retail_unit_id",lookup_expr="exact")
    category=filters.CharFilter(field_name="category__name",lookup_expr='exact')


    class Meta:
        model=Product
        fields=["name","stock_quantity","price","category"]
