from rest_framework.decorators import api_view
from rest_framework.response import Response

from customer.models import Customer, CustomerPurchase

from .serializers import (
    CustomerSerializer,
    PurchaseDetailSerializer,
    PurchaseListSerializer,
)


@api_view(["GET"])
def customer_list(request):
    customers = Customer.objects.order_by("name")
    return Response({"customers": CustomerSerializer(customers, many=True).data})


@api_view(["GET"])
def purchase_list(request):
    purchases = (
        CustomerPurchase.objects
        .select_related("customer", "tenant", "retail_unit")
        .order_by("-purchase_date")
    )

    tenant_id = request.query_params.get("tenant")
    if tenant_id:
        purchases = purchases.filter(tenant_id=tenant_id)

    return Response({"purchases": PurchaseListSerializer(purchases, many=True).data})


@api_view(["GET"])
def purchase_detail(request, pk):
    try:
        purchase = (
            CustomerPurchase.objects
            .select_related("customer", "tenant", "retail_unit")
            .prefetch_related("items__product")
            .get(pk=pk)
        )
    except CustomerPurchase.DoesNotExist:
        return Response({"error": "Purchase not found"}, status=404)

    return Response(PurchaseDetailSerializer(purchase).data)
