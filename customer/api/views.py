from rest_framework.decorators import api_view
from rest_framework.response import Response

from customer.models import Customer, CustomerPurchase


@api_view(["GET"])
def customer_list(request):
    customers = Customer.objects.order_by("name")

    return Response({
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
            }
            for c in customers
        ]
    })


@api_view(["GET"])
def purchase_list(request):
    purchases = (
        CustomerPurchase.objects
        .select_related("customer", "tenant", "retail_unit")
        .order_by("-purchase_date")
    )

    # optional filters
    tenant_id = request.query_params.get("tenant")
    if tenant_id:
        purchases = purchases.filter(tenant_id=tenant_id)

    return Response({
        "purchases": [
            {
                "id": p.id,
                "customer": p.customer.name,
                "tenant": p.tenant.name,
                "retail_unit": p.retail_unit.title if p.retail_unit else None,
                "total": p.total_amount,
                "full_paid": p.full_paid,
                "date": p.purchase_date,
            }
            for p in purchases
        ]
    })


@api_view(["GET"])
def purchase_detail(request, pk):
    try:
        p = (
            CustomerPurchase.objects
            .select_related("customer", "tenant", "retail_unit")
            .prefetch_related("items__product")
            .get(pk=pk)
        )
    except CustomerPurchase.DoesNotExist:
        return Response({"error": "Purchase not found"}, status=404)

    return Response({
        "id": p.id,
        "customer": p.customer.name,
        "tenant": p.tenant.name,
        "retail_unit": p.retail_unit.title if p.retail_unit else None,
        "total": p.total_amount,
        "full_paid": p.full_paid,
        "date": p.purchase_date,
        "items": [
            {
                "product": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in p.items.all()
        ],
    })
