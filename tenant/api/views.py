from django.db.models import ProtectedError, Sum

from rest_framework import generics, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.api.permissions import IsTenantWithProfile
from customer.models import CustomerPayment, CustomerPurchase
from customer.services import InsufficientStock, create_offline_purchase
from product.models import Product
from tenant.forms import OfflineSaleForm
from tenant.models import RetailUnit

from .serializers import (
    MallBriefSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    RecentPurchaseSerializer,
    RecordPurchaseWriteSerializer,
    RetailUnitSerializer,
    TenantBriefSerializer,
)


def ensure_retail_unit_belongs_to_tenant(serializer, tenant):

    retail_unit = serializer.validated_data.get("retail_unit")

    if retail_unit is not None and retail_unit.tenant_id != tenant.pk:
        raise serializers.ValidationError(
            {"retail_unit": ["Invalid retail unit."]}
        )


class Dashboard(generics.GenericAPIView):
    permission_classes = [IsTenantWithProfile]

    def get(self, request):
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
            .prefetch_related("items__product", "payments")
            .order_by("-purchase_date")[:8]
        )

        purchase_count = (
            CustomerPurchase.objects
            .filter(tenant=tenant)
            .count()
        )

        return Response({
            "tenant": TenantBriefSerializer(tenant).data,
            "malls": MallBriefSerializer(
                tenant.malls.order_by("name"),
                many=True
            ).data,
            "retail_units": RetailUnitSerializer(
                retail_units,
                many=True
            ).data,
            "products": ProductSerializer(
                products,
                many=True
            ).data,
            "recent_purchases": RecentPurchaseSerializer(
                recent_purchases,
                many=True
            ).data,
            "purchase_count": purchase_count,
        })


class AddRetailUnit(generics.GenericAPIView):
    permission_classes = [IsTenantWithProfile]

    def get(self, request):
        tenant = request.user.tenant_profile

        return Response({
            "detail": (
                "Retail stores are assigned by the mall manager. "
                "Once assigned, you can add products to them."
            ),
            "has_retail_unit": (
                RetailUnit.objects
                .filter(tenant=tenant)
                .exists()
            ),
        })


class AddProduct(generics.CreateAPIView):
    permission_classes = [IsTenantWithProfile]
    serializer_class = ProductWriteSerializer


class EditProduct(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTenantWithProfile]

    def get_queryset(self):
        tenant = self.request.user.tenant_profile

        return (
            Product.objects
            .filter(retail_unit__tenant=tenant)
            .select_related("retail_unit")
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductWriteSerializer

        return ProductSerializer    
class RecordSale(generics.CreateAPIView):
    permission_classes = [IsTenantWithProfile]
    serializer_class = RecordPurchaseWriteSerializer
    
    # def create(self, request, *args, **kwargs):
    #     tenant = request.user.tenant_profile

    #     form = OfflineSaleForm(
    #         request.data,
    #         tenant=tenant,
    #     )

    #     if not form.is_valid():
    #         return Response(
    #             form.errors.get_json_data(),
    #             status=400,
    #         )

    #     try:
    #         purchase = create_offline_purchase(
    #             tenant=tenant,
    #             retail_unit=form.cleaned_data["retail_unit"],
    #             name=form.cleaned_data["customer_name"],
    #             phone=form.cleaned_data["customer_phone"],
    #             items=[
    #                 {
    #                     "product_id": form.cleaned_data["product"].pk,
    #                     "quantity": form.cleaned_data["quantity"],
    #                 }
    #             ],
    #             payment_method=form.cleaned_data["payment_method"],
    #         )

    #     except InsufficientStock as exc:
    #         return Response(
    #             {"quantity": [str(exc)]},
    #             status=400,
    #         )

        # return Response(
        #     RecentPurchaseSerializer(purchase).data,
        #     status=status.HTTP_201_CREATED,
        # )


class PaymentHistoryPagination(PageNumberPagination):
    page_size = 20


class PaymentHistory(generics.ListAPIView):
    permission_classes = [IsTenantWithProfile]
    serializer_class = RecentPurchaseSerializer
    pagination_class = PaymentHistoryPagination

    def get_queryset(self):
        tenant = self.request.user.tenant_profile

        return (
            CustomerPurchase.objects
            .filter(tenant=tenant)
            .select_related(
                "customer",
                "retail_unit",
            )
            .prefetch_related(
                "items__product",
                "payments",
            )
            .order_by("-purchase_date")
        )

    # def list(self, request, *args, **kwargs):
    #     response = super().list(request, *args, **kwargs)

    #     tenant = request.user.tenant_profile

    #     total_received = (
    #         CustomerPayment.objects
    #         .filter(purchase__tenant=tenant)
    #         .aggregate(total=Sum("amount"))["total"]
    #         or 0
    #     )

    #     response.data["total_received"] = total_received

    #     return response


class PurchaseDetail(generics.RetrieveAPIView):
    permission_classes = [IsTenantWithProfile]
    serializer_class = RecentPurchaseSerializer
    
    def get_queryset(self):
        tenant = self.request.user.tenant_profile

        return (
            CustomerPurchase.objects
            .filter(tenant=tenant)
            .select_related(
                "customer",
                "tenant",
                "retail_unit",
            )
            .prefetch_related(
                "items__product",
                "payments",
            )
        )


class ProductsByRetailUnit(generics.ListAPIView):
    permission_classes = [IsTenantWithProfile]
    serializer_class = ProductSerializer

    def get_queryset(self):
        tenant = self.request.user.tenant_profile

        try:
            retail_unit_id = int(self.request.query_params.get("retail_unit"))
        except (TypeError, ValueError):
            return Product.objects.none()

        return (
            Product.objects
            .filter(
                retail_unit_id=retail_unit_id,
                retail_unit__tenant=tenant,
                stock_quantity__gt=0,
            )
            .select_related("retail_unit")
            .order_by("name")
        )