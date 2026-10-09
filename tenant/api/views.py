from django.db.models import ProtectedError, Sum

from customer.api.serializers import RecentPurchaseSerializer
from rest_framework import generics, serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters import rest_framework as filters

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


# class ProductViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsTenantWithProfile]
#     http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return (
#             Product.objects
#             .filter(retail_unit__tenant=tenant)
#             .select_related("retail_unit")
#         )

#     def get_serializer_class(self):
#         if self.action in ("create", "update", "partial_update"):
#             return ProductWriteSerializer
#         return ProductSerializer



class PaymentHistoryPagination(PageNumberPagination):
    page_size = 20


# class PurchaseViewSet(viewsets.ReadOnlyModelViewSet):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = RecentPurchaseSerializer
#     pagination_class = PaymentHistoryPagination

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return (
#             CustomerPurchase.objects
#             .filter(tenant=tenant)
#             .select_related(
#                 "customer",
#                 "tenant",
#                 "retail_unit",
#             )
#             .prefetch_related(
#                 "items__product",
#                 "payments",
#             )
#             .order_by("-purchase_date")
#         )


# class ProductsByRetailUnit(generics.ListAPIView):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = ProductSerializer

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile

#         try:
#             retail_unit_id = int(self.request.query_params.get("retail_unit"))
#         except (TypeError, ValueError):
#             return Product.objects.none()

#         return (
#             Product.objects
#             .filter(
#                 retail_unit_id=retail_unit_id,
#                 retail_unit__tenant=tenant,
#                 stock_quantity__gt=0,
#             )
#             .select_related("retail_unit")
#             .order_by("name")
#         )

# class ProductCreate(generics.CreateAPIView):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = ProductWriteSerializer


# class ProductList(generics.ListAPIView):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = ProductSerializer

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return Product.objects.filter(retail_unit__tenant=tenant)


# class ProductUpdate(generics.UpdateAPIView):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = ProductWriteSerializer

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return Product.objects.filter(retail_unit__tenant=tenant)


# class ProductDelete(generics.DestroyAPIView):
#     permission_classes = [IsTenantWithProfile]

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return Product.objects.filter(retail_unit__tenant=tenant)

# class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsTenantWithProfile]
#     serializer_class = ProductWriteSerializer

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return Product.objects.filter(retail_unit__tenant=tenant)



# class ProductViewsets(viewsets.ViewSet):
#     permission_classes=[IsTenantWithProfile]

#     def list(self,request):
#         tenant=self.request.user.tenant_profile
#         queryset=Product.objects.filter(retail_unit__tenant=tenant).order_by("name")
#         serializer=ProductSerializer(queryset,many=True)
#         return Response(serializer.data)

#     def create(self,request):
#         serializer=ProductWriteSerializer(data=request.data,context={"request": request}
# )
#         serializer.is_valid(raise_exception=True)
#         product=serializer.save()
#         return Response(ProductSerializer(product).data)
    

#     def get_queryset(self):
#         tenant = self.request.user.tenant_profile
#         return Product.objects.filter(
#             retail_unit__tenant=tenant
#         )

#     def update(self, request, pk=None):
#         product = self.get_queryset().filter(pk=pk).first()

#         if product is None:
#             return Response(
#                 {"detail": "Product not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = ProductWriteSerializer(
#             product,
#             data=request.data,
#             context={"request": request}
#         )
#         serializer.is_valid(raise_exception=True)
#         product = serializer.save()

#         return Response(ProductSerializer(product).data)

#     def partial_update(self, request, pk=None):
#         product = self.get_queryset().filter(pk=pk).first()

#         if product is None:
#             return Response(
#                 {"detail": "Product not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = ProductWriteSerializer(
#             product,
#             data=request.data,
#             partial=True,
#             context={"request": request}
#         )
#         serializer.is_valid(raise_exception=True)
#         product = serializer.save()

#         return Response(ProductSerializer(product).data)

#     def destroy(self, request, pk=None):
#         product = self.get_queryset().filter(pk=pk).first()

#         if product is None:
#             return Response(
#                 {"detail": "Product not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         product.delete()

#         return Response({"detail":"Its Deleted MOFO"},status=status.HTTP_204_NO_CONTENT)

#     def retrieve(self, request, pk=None):
#      product = self.get_queryset().filter(pk=pk).first()

#      if product is None:
#         return Response(
#             {"detail": "Product not found."},
#             status=status.HTTP_404_NOT_FOUND
#         )

#      serializer = ProductSerializer(product)
#      return Response(serializer.data)


class ProductFilter(filters.FilterSet):
    min_price=filters.NumberFilter(field_name="price",lookup_expr='gte')
    max_price=filters.NumberFilter(field_name="price",lookup_expr='lte')
    min_stock=filters.NumberFilter(field_name="stock_quantity", lookup_expr='gte')
    max_Stock=filters.NumberFilter(field_name="stock_quantity",lookup_expr="lte")
    retail_unit=filters.NumberFilter(field_name="retail_unit_id",lookup_expr="exact")


    class Meta:
        model=Product
        fields=["name","stock_quantity","price"]


class ProductViewModelSet(viewsets.ModelViewSet):
    permission_classes=[IsTenantWithProfile]
    filterset_class=ProductFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_queryset(self):
        tenant = self.request.user.tenant_profile

        queryset = (
            Product.objects
            .filter(retail_unit__tenant=tenant)
            .select_related("retail_unit")
            .order_by("name")
        )

        # retail_unit = self.request.query_params.get("retail_unit")
        # min_price = self.request.query_params.get("min_price")
        # max_price = self.request.query_params.get("max_price")
        # min_stock = self.request.query_params.get("min_stock")
        # max_stock = self.request.query_params.get("max_stock")

        # if retail_unit:
        #     queryset = queryset.filter(retail_unit_id=retail_unit)

        # if min_price:
        #     queryset = queryset.filter(price__gte=min_price)

        # if max_price:
        #     queryset = queryset.filter(price__lte=max_price)

        # if min_stock:
        #     queryset = queryset.filter(stock_quantity__gte=min_stock)

        # if max_stock:
        #     queryset = queryset.filter(stock_quantity__lte=max_stock)

        return queryset
    
    def get_serializer_class(self):
        if self.action in ["create","update","partial_update"]:
            return ProductWriteSerializer
        return ProductSerializer