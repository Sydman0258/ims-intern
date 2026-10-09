from django.db.models import Count, Q, Sum
from customer.models import CustomerPayment, CustomerPurchase
from mall.api.pagination import MallPaginationView
from product.models import Product
from rest_framework import viewsets,generics,status,serializers
from rest_framework.response import Response

from accounts.api.permissions import IsMallStaff,IsAdminRole
from mall.models import Mall
from mall.api.serializers import (
    MallBriefSerializer,
    MallCreateSerializer,
    MallListSerializer,
    MallReadSerializer,
    MallUpdateSerializer,
    RetailUnitInMallSerializer,
    TenantInMallSerializer,
)
from tenant.api.serializers import (
    TenantBriefSerializer
)
from tenant.models import LeasePayment, RetailUnit,Tenant


class MallCreateAndTenant(generics.CreateAPIView): # type: ignore
    permission_classes=[IsAdminRole]
    serializer_class=MallCreateSerializer


class MallListWithTenant(generics.ListAPIView):
    permission_classes=[IsAdminRole]
    serializer_class=MallReadSerializer   
    pagination_class=MallPaginationView

    queryset = Mall.objects.select_related(
    "user"
).prefetch_related(
    "retail_unit__tenant"
)        

class UpdateMallWithTenant(generics.UpdateAPIView):
    permission_classes=[IsAdminRole]
    serializer_class=MallUpdateSerializer
    queryset = Mall.objects.all()



class MallDelete(generics.DestroyAPIView):
    permission_classes = [IsAdminRole]

    queryset = Mall.objects.select_related(
        "user"
    ).prefetch_related(
        "retail_unit__tenant"
    )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response(
            {
                "detail": "MALL DELETED MOFO."
            },
            status=status.HTTP_200_OK
        )

class TenantProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "email", "phone"]

class ExistingTenantList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    queryset = Tenant.objects.order_by("name")
    serializer_class = TenantProfileListSerializer
    pagination_class=MallPaginationView
            
class MallViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsMallStaff]
    serializer_class = MallListSerializer
    lookup_url_kwarg = "mall_id"
    pagination_class=MallPaginationView


    def get_queryset(self):
        return (
            Mall.objects
            .annotate(
                tenant_count=Count("tenants", distinct=True),
                unit_count=Count("retail_unit", distinct=True),
            )
            .order_by("name")
        )

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


    