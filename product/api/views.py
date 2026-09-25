from rest_framework.decorators import api_view
from rest_framework.response import Response

from product.models import Product


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

    return Response({
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock_quantity,
                "status": p.status,
                "retail_unit": p.retail_unit.title if p.retail_unit else None,
                "mall": p.retail_unit.mall.name if p.retail_unit else None,
                "tenant": p.retail_unit.tenant.name if p.retail_unit and p.retail_unit.tenant else None,
            }
            for p in products
        ]
    })


@api_view(["GET"])
def product_detail(request, pk):
    try:
        p = (
            Product.objects
            .select_related("retail_unit", "retail_unit__mall", "retail_unit__tenant")
            .get(pk=pk)
        )
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    return Response({
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock_quantity,
        "status": p.status,
        "retail_unit": p.retail_unit.title if p.retail_unit else None,
        "mall": p.retail_unit.mall.name if p.retail_unit else None,
        "tenant": p.retail_unit.tenant.name if p.retail_unit and p.retail_unit.tenant else None,
    })
