from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.db.models import Count, Q, Sum

from customer.models import CustomerPayment, CustomerPurchase
from product.models import Product
from tenant.models import LeasePayment, RetailUnit, Tenant

from mall.models import Mall


@api_view(["GET"])
def mall_list(request):
    malls = Mall.objects.annotate(
        tenant_count=Count("tenants", distinct=True),
        unit_count=Count("retail_unit", distinct=True),
    ).order_by("name")

    return Response({
        "malls": [
            {
                "id": mall.id,
                "name": mall.name,
                "floors": mall.floors,
                "total_shops": mall.total_shops,
                "num_leased": mall.num_leased,
                "tenant_count": mall.tenant_count,
                "unit_count": mall.unit_count,
            }
            for mall in malls
        ]
    })


@api_view(["GET"])
def mall_detail(request, mall_id):
    try:
        mall = Mall.objects.get(pk=mall_id)
    except Mall.DoesNotExist:
        return Response({"error": "Mall not found"}, status=404)

    units = (
        RetailUnit.objects.filter(mall=mall)
        .select_related("tenant")
        .order_by("title")
    )
    tenants = (
        mall.tenants.annotate(
            unit_count=Count("retail_unit", filter=Q(retail_unit__mall=mall))
        )
        .order_by("name")
    )

    tenant_ids = list(tenants.values_list("id", flat=True))
    purchases = CustomerPurchase.objects.filter(tenant_id__in=tenant_ids)
    payment_total = (
        CustomerPayment.objects.filter(purchase__tenant_id__in=tenant_ids)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    lease_total = (
        LeasePayment.objects.filter(retail_unit__mall=mall, status="paid")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    expired_count = sum(1 for u in units if u.is_lease_expired)

    return Response({
        "mall": {
            "id": mall.id,
            "name": mall.name,
            "floors": mall.floors,
            "total_shops": mall.total_shops,
            "num_leased": mall.num_leased,
        },
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "phone": t.phone,
                "unit_count": t.unit_count,
            }
            for t in tenants
        ],
        "retail_units": [
            {
                "id": u.id,
                "title": u.title,
                "leased": u.leased,
                "tenant": u.tenant.name if u.tenant else None,
                "monthly_rent": u.monthly_rent,
                "lease_status": u.lease_status_label,
            }
            for u in units
        ],
        "leased_count": units.filter(leased=True).count(),
        "expired_count": expired_count,
        "purchase_count": purchases.count(),
        "payment_total": payment_total,
        "lease_total": lease_total,
        "product_count": Product.objects.filter(retail_unit__mall=mall).count(),
    })
