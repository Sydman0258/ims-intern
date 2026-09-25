from rest_framework.decorators import api_view
from rest_framework.response import Response

from product.models import Product

from .serializers import ProductDetailSerializer, ProductListSerializer


@api_view(["GET"])
def product_list(request):
    products = (
        Product.objects
        .select_related("retail_unit", "retail_unit__mall", "retail_unit__tenant")
        .order_by("name")
    )

    retail_unit_id = request.query_params.get("retail_unit")
    if retail_unit_id:
        products = products.filter(retail_unit_id=retail_unit_id)

    return Response({"products": ProductListSerializer(products, many=True).data})


@api_view(["GET"])
def product_detail(request, pk):
    try:
        product = (
            Product.objects
            .select_related("retail_unit", "retail_unit__mall", "retail_unit__tenant")
            .get(pk=pk)
        )
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    return Response(ProductDetailSerializer(product).data)
