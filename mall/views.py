from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Role
from customer.models import CustomerPayment, CustomerPurchase
from product.models import Product
from tenant.models import LeasePayment, RetailUnit, Tenant

from .forms import CreateTenantForm, AssignRetailUnitForm
from .models import Mall


def _is_mall_staff(user):
    """Mall managers and admins can access mall management."""
    return user.is_authenticated and user.role in (Role.MALL_MANAGER, Role.ADMIN)


def _get_mall_or_404(mall_id):
    return get_object_or_404(Mall, pk=mall_id)


@login_required
def index(request):
    """List all malls. Click one to open its detail dashboard."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    malls = Mall.objects.annotate(
        tenant_count=Count("tenants", distinct=True),
        unit_count=Count("retail_unit", distinct=True),
    ).order_by("name")

    context = {
        "malls": malls,
        "today": timezone.localdate(),
    }
    return render(request, "mall/index.html", context)


@login_required
def mall_detail(request, mall_id):
    """Dashboard for one specific mall: tenants, units, lease status."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)

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
        CustomerPayment.objects.filter(purchase__tenant_id__in=tenant_ids).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    lease_total = (
        LeasePayment.objects.filter(
            retail_unit__mall=mall, status="paid"
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    total_shops=10
    floors=10
    
    expired_count = sum(1 for u in units if u.is_lease_expired)

    context = {
        "mall": mall,
        "tenants": tenants,
        "retail_units": units,
        "leased_count": units.filter(leased=True).count(),
        "expired_count": expired_count,
        "available_tenants": Tenant.objects.exclude(malls=mall).order_by("name"),
        "purchase_count": purchases.count(),
        "payment_total": payment_total,
        "lease_total": lease_total,
        "product_count": Product.objects.filter(
            retail_unit__mall=mall
        ).count(),
        "today": timezone.localdate(),
        "total_shops":total_shops,
        "floors":floors
    }
    return render(request, "mall/mall_detail.html", context)


@login_required
@require_POST
def assign_tenant(request, mall_id):
    """Assign an existing tenant to this mall."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)
    tenant_id = request.POST.get("tenant", "")
    if not tenant_id.isdigit():
        messages.error(request, "Please choose a tenant to assign.")
        return redirect("mall:mall_detail", mall_id=mall.id)

    tenant = get_object_or_404(Tenant, pk=tenant_id)
    if mall.tenants.filter(pk=tenant.pk).exists():
        messages.info(request, f"{tenant.name} is already assigned to {mall.name}.")
    else:
        mall.tenants.add(tenant)
        messages.success(request, f"{tenant.name} is now assigned to {mall.name}.")
    return redirect("mall:mall_detail", mall_id=mall.id)


@login_required
@require_POST
def remove_tenant(request, mall_id, tenant_id):
    """Remove a tenant from this mall (only if they have no units here)."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)
    tenant = get_object_or_404(mall.tenants, pk=tenant_id)
    if RetailUnit.objects.filter(mall=mall, tenant=tenant).exists():
        messages.error(
            request,
            f"{tenant.name} still has retail units in {mall.name}, so it can't be removed.",
        )
    else:
        mall.tenants.remove(tenant)
        messages.success(request, f"{tenant.name} was removed from {mall.name}.")
    return redirect("mall:mall_detail", mall_id=mall.id)


@login_required
def create_tenant(request, mall_id):
    """Create a new tenant and assign them to this mall."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)

    if request.method == "POST":
        form = CreateTenantForm(request.POST)
        if form.is_valid():
            tenant = form.save(mall)
            msg = f'Tenant "{tenant.name}" created and assigned to {mall.name}.'
            if tenant.user_id:
                msg += f" Login: {tenant.user.email}"
            messages.success(request, msg)
            return redirect("mall:mall_detail", mall_id=mall.id)
    else:
        form = CreateTenantForm()

    return render(
        request,
        "mall/create_tenant.html",
        {"mall": mall, "form": form},
    )


@login_required
def assign_retail_unit(request, mall_id):
    """Mall assigns a retail store (unit) to a tenant already linked to this mall."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)

    if request.method == "POST":
        form = AssignRetailUnitForm(request.POST, mall=mall)
        if form.is_valid():
            unit = form.save()
            messages.success(
                request,
                f'Retail store "{unit.title}" assigned to {unit.tenant.name} '
                f"(₹{unit.monthly_rent or 0}/mo, renews {unit.renewal_date or '—'}).",
            )
            return redirect("mall:mall_detail", mall_id=mall.id)
    else:
        form = AssignRetailUnitForm(mall=mall)

    return render(
        request,
        "mall/assign_retail_unit.html",
        {"mall": mall, "form": form},
    )


@login_required
def tenant_detail(request, mall_id, tenant_id):
    """View one tenant under this mall: units, products, payments."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)
    tenant = get_object_or_404(mall.tenants, pk=tenant_id)
    units = RetailUnit.objects.filter(mall=mall, tenant=tenant).order_by("title")
    products = (
        Product.objects.filter(retail_unit__tenant=tenant, retail_unit__mall=mall)
        .select_related("retail_unit")
        .order_by("name")
    )
    purchases = (
        CustomerPurchase.objects.filter(tenant=tenant)
        .select_related("customer", "retail_unit")
        .prefetch_related("payments", "items__product")
        .order_by("-purchase_date")[:50]
    )
    payment_total = (
        CustomerPayment.objects.filter(purchase__tenant=tenant).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    lease_payments = LeasePayment.objects.filter(
        retail_unit__mall=mall, retail_unit__tenant=tenant
    ).select_related("retail_unit")[:30]

    return render(
        request,
        "mall/tenant_detail.html",
        {
            "mall": mall,
            "tenant": tenant,
            "units": units,
            "products": products,
            "purchases": purchases,
            "payment_total": payment_total,
            "lease_payments": lease_payments,

            "today": timezone.localdate(),
        },
    )


@login_required
def payment_overview(request, mall_id):
    """Sales payments + lease payments for this mall."""
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)
    tenant_ids = list(mall.tenants.values_list("id", flat=True))
    purchases = (
        CustomerPurchase.objects.filter(tenant_id__in=tenant_ids)
        .select_related("customer", "tenant", "retail_unit")
        .prefetch_related("payments")
        .order_by("-purchase_date")
    )

    paginator = Paginator(purchases, 25)
    page = paginator.get_page(request.GET.get("page"))

    payment_total = (
        CustomerPayment.objects.filter(purchase__tenant_id__in=tenant_ids).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    lease_payments = (
        LeasePayment.objects.filter(retail_unit__mall=mall)
        .select_related("retail_unit", "retail_unit__tenant")
        .order_by("-period_end")[:50]
    )
    lease_total = (
        LeasePayment.objects.filter(
            retail_unit__mall=mall, status="paid"
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return render(
        request,
        "mall/payment_overview.html",
        {
            "mall": mall,
            "page_obj": page,
            "purchases": page,
            "payment_total": payment_total,
            "purchase_count": purchases.count(),
            "lease_payments": lease_payments,
            "lease_total": lease_total,
        },
    )


@login_required
@require_POST
def lease_action(request, mall_id, unit_id):
    """
    Action when a retail unit lease has expired (or is about to).
    Supported actions: renew, end, mark_pending.
    On renew: optional months + monthly_rent (lease amount).
    """
    if not _is_mall_staff(request.user):
        return redirect("accounts:login")

    mall = _get_mall_or_404(mall_id)
    unit = get_object_or_404(RetailUnit, pk=unit_id, mall=mall)
    action = request.POST.get("action", "")

    if action == "renew":
        months = request.POST.get("months", "12")
        try:
            months = max(1, int(months))
        except ValueError:
            months = 12

        rent_raw = request.POST.get("monthly_rent", "").strip()
        if rent_raw:
            try:
                unit.monthly_rent = Decimal(rent_raw)
            except (InvalidOperation, ValueError):
                messages.warning(request, "Invalid lease amount; kept previous rent.")

        base = unit.renewal_date or timezone.localdate()
        if base < timezone.localdate():
            base = timezone.localdate()
        unit.leased = True
        unit.leased_date = unit.leased_date or timezone.localdate()
        unit.leased_tenure = months
        unit.renewal_date = base + timedelta(days=30 * months)
        unit.status = "Active"
        unit.save()
        rent_note = f" at ₹{unit.monthly_rent}/mo" if unit.monthly_rent else ""
        messages.success(
            request,
            f'Lease for "{unit.title}" renewed until {unit.renewal_date}{rent_note}.',
        )
    elif action == "end":
        unit.leased = False
        unit.status = "Lease ended"
        unit.save(update_fields=["leased", "status", "updated_at"])
        messages.success(request, f'Lease for "{unit.title}" marked as ended.')
    elif action == "mark_pending":
        unit.status = "Renewal pending"
        unit.save(update_fields=["status", "updated_at"])
        messages.info(request, f'"{unit.title}" marked as renewal pending.')
    else:
        messages.error(request, "Unknown lease action.")

    next_url = request.POST.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect("mall:mall_detail", mall_id=mall.id)
