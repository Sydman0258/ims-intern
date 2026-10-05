from django.db.models import Count, Q, Sum
from customer.models import CustomerPayment, CustomerPurchase
from product.models import Product
from rest_framework import generics
from rest_framework.response import Response



from accounts.api.permissions import IsMallStaff
from mall.models import Mall
from mall.api.serializers import (
    MallBriefSerializer,
    MallListSerializer,
    RetailUnitInMallSerializer,
    TenantInMallSerializer,
)
from tenant.models import LeasePayment, RetailUnit


class MallList(generics.ListAPIView):
    permission_classes = [IsMallStaff]
    serializer_class = MallListSerializer

    def get_queryset(self):
        return (
            Mall.objects
            .annotate(
                tenant_count=Count("tenants", distinct=True),
                unit_count=Count("retail_unit", distinct=True),
            )
            .order_by("name")
        )

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response({"malls": serializer.data})


class MallDetail(generics.RetrieveAPIView):
    permission_classes = [IsMallStaff]
    serializer_class=MallListSerializer
    queryset = Mall.objects.all()

    lookup_url_kwarg = "mall_id"

    def retrieve(self, request, *args, **kwargs):
        mall = self.get_object()

        units = (
            RetailUnit.objects
            .filter(mall=mall)
            .select_related("tenant")
            .order_by("title")
        )
        tenants = (
            mall.tenants
            .annotate(
                unit_count=Count("retail_unit", filter=Q(retail_unit__mall=mall))
            )
            .order_by("name")
        )

        tenant_ids = list(tenants.values_list("id", flat=True))
        purchases = CustomerPurchase.objects.filter(tenant_id__in=tenant_ids)
        payment_total = (
            CustomerPayment.objects
            .filter(purchase__tenant_id__in=tenant_ids)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )
        lease_total = (
            LeasePayment.objects
            .filter(retail_unit__mall=mall, status="paid")
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expired_count = sum(1 for u in units if u.is_lease_expired)

        return Response({
            "mall": MallBriefSerializer(mall).data,
            "tenants": TenantInMallSerializer(tenants, many=True).data,
            "retail_units": RetailUnitInMallSerializer(units, many=True).data,
            "leased_count": units.filter(leased=True).count(),
            "expired_count": expired_count,
            "purchase_count": purchases.count(),
            "payment_total": payment_total,
            "lease_total": lease_total,
            "product_count": Product.objects.filter(retail_unit__mall=mall).count(),
        })
