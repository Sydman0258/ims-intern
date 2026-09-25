from rest_framework.decorators import api_view
from rest_framework.response import Response

from customer.models import CustomerPurchase
from product.models import Product
from tenant.models import RetailUnit


@api_view(["GET"])
def dashboard(request):
    tenant = request.user.tenant_profile

    products = (
        Product.objects
        .filter(retail_unit__tenant=tenant)
        .select_related("retail_unit", "retail_unit__mall")
        .order_by("name")
    )

    retail_units = (
        RetailUnit.objects
        .filter(tenant=tenant)
        .select_related("mall")
    )

    recent_purchases = (
        CustomerPurchase.objects
        .filter(tenant=tenant)
        .select_related("customer", "retail_unit")
        .order_by("-purchase_date")[:8]
    )

    purchase_count = (
        CustomerPurchase.objects
        .filter(tenant=tenant)
        .count()
    )

    return Response({
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
        },
        "malls": [
            {
                "id": mall.id,
                "name": mall.name,
            }
            for mall in tenant.malls.order_by("name")
        ],
        "retail_units": [
            {
                "id": retail_unit.id,
                "title": retail_unit.title,
                "mall": retail_unit.mall.name,
            }
            for retail_unit in retail_units
        ],
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock_quantity,
                "retail_unit": product.retail_unit.title,
            }
            for product in products
        ],
        "recent_purchases": [
            {
                "id": purchase.id,
                "customer": purchase.customer.name,
                "retail_unit": purchase.retail_unit.title if purchase.retail_unit else None,
                "total": purchase.total_amount,
                "date": purchase.purchase_date,
            }
            for purchase in recent_purchases
        ],
        "purchase_count": purchase_count,
    })
