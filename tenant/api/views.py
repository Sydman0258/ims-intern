from rest_framework.decorators import api_view
from rest_framework.response import Response

from customer.models import CustomerPurchase
from product.models import Product
from tenant.models import RetailUnit

from .serializers import (
    MallBriefSerializer,
    ProductSerializer,
    RecentPurchaseSerializer,
    RetailUnitSerializer,
    TenantBriefSerializer,
)


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

    purchase_count = CustomerPurchase.objects.filter(tenant=tenant).count()

    return Response({
        "tenant": TenantBriefSerializer(tenant).data,
        "malls": MallBriefSerializer(tenant.malls.order_by("name"), many=True).data,
        "retail_units": RetailUnitSerializer(retail_units, many=True).data,
        "products": ProductSerializer(products, many=True).data,
        "recent_purchases": RecentPurchaseSerializer(recent_purchases, many=True).data,
        "purchase_count": purchase_count,
    })
