from rest_framework import generics, viewsets

from accounts.api.permissions import IsMallStaff
from customer.models import Customer, CustomerPurchase

from .serializers import (
    CustomerSerializer,
    PurchaseDetailSerializer,
    PurchaseListSerializer,
)


class CustomerList(generics.ListAPIView):
    permission_classes = [IsMallStaff]
    serializer_class = CustomerSerializer
    queryset = Customer.objects.order_by("name")


class PurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsMallStaff]
    queryset = (
        CustomerPurchase.objects
        .select_related("customer", "tenant", "retail_unit")
        .prefetch_related("items__product")
        .order_by("-purchase_date")
    )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PurchaseDetailSerializer
        return PurchaseListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = self.request.query_params.get("tenant")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs