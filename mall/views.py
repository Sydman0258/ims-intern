from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, FormView

from accounts.mixins import MallStaffRequiredMixin
from customer.models import CustomerPayment, CustomerPurchase
from product.models import Product
from tenant.models import LeasePayment, RetailUnit, Tenant

from .forms import CreateTenantForm, AssignRetailUnitForm
from .models import Mall


class MallIndexView(MallStaffRequiredMixin, ListView):
    """List all malls. Click one to open its detail dashboard."""

    model = Mall
    template_name = "mall/index.html"
    context_object_name = "malls"

    def get_queryset(self):
        return Mall.objects.annotate(
            tenant_count=Count("tenants", distinct=True),
            unit_count=Count("retail_unit", distinct=True),
        ).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = timezone.localdate()
        return ctx


class MallDetailView(MallStaffRequiredMixin, DetailView):
    """Dashboard for one specific mall: tenants, units, lease status."""

    model = Mall
    template_name = "mall/mall_detail.html"
    context_object_name = "mall"
    pk_url_kwarg = "mall_id"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mall = self.object

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
        expired_count = sum(1 for u in units if u.is_lease_expired)

        ctx.update(
            {
                "tenants": tenants,
                "retail_units": units,
                "leased_count": units.filter(leased=True).count(),
                "expired_count": expired_count,
                # Tenants NOT yet in this mall → top "Assign existing tenant" form
                "available_tenants": Tenant.objects.exclude(malls=mall).order_by("name"),
                # Tenants ALREADY in this mall → used when re-assigning a free unit
                "mall_tenants": tenants,
                "purchase_count": purchases.count(),
                "payment_total": payment_total,
                "lease_total": lease_total,
                "product_count": Product.objects.filter(retail_unit__mall=mall).count(),
                "today": timezone.localdate(),
                "floors": mall.floors,
            }
        )
        return ctx


class AssignTenantView(MallStaffRequiredMixin, View):
    """Assign an existing tenant to this mall (top form on mall detail)."""

    http_method_names = ["post"]

    def post(self, request, mall_id):
        mall = get_object_or_404(Mall, pk=mall_id)
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


class RemoveTenantView(MallStaffRequiredMixin, View):
    """Remove a tenant from this mall (only if they have no units here)."""

    http_method_names = ["post"]

    def post(self, request, mall_id, tenant_id):
        mall = get_object_or_404(Mall, pk=mall_id)
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


class CreateTenantView(MallStaffRequiredMixin, FormView):
    """Create a new tenant and assign them to this mall."""

    template_name = "mall/create_tenant.html"
    form_class = CreateTenantForm

    def dispatch(self, request, *args, **kwargs):
        self.mall = get_object_or_404(Mall, pk=kwargs["mall_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mall"] = self.mall
        return ctx

    def form_valid(self, form):
        tenant = form.save(self.mall)
        msg = f'Tenant "{tenant.name}" created and assigned to {self.mall.name}.'
        if tenant.user_id:
            msg += f" Login: {tenant.user.email}"
        messages.success(self.request, msg)
        return redirect("mall:mall_detail", mall_id=self.mall.id)


class AssignRetailUnitView(MallStaffRequiredMixin, FormView):
    """Create a new retail unit and assign it to a tenant of this mall."""

    template_name = "mall/assign_retail_unit.html"
    form_class = AssignRetailUnitForm

    def dispatch(self, request, *args, **kwargs):
        self.mall = get_object_or_404(Mall, pk=kwargs["mall_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["mall"] = self.mall
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mall"] = self.mall
        return ctx

    def form_valid(self, form):
        unit = form.save()
        messages.success(
            self.request,
            f'Retail store "{unit.title}" assigned to {unit.tenant.name} '
            f"(₹{unit.monthly_rent or 0}/mo, renews {unit.renewal_date or '—'}).",
        )
        return redirect("mall:mall_detail", mall_id=self.mall.id)


class ReassignUnitView(MallStaffRequiredMixin, View):
    """
    Re-assign an existing (unleased) retail unit to a tenant that already
    belongs to this mall.  This is what you use after clicking "End lease".
    """

    http_method_names = ["post"]

    def post(self, request, mall_id, unit_id):
        mall = get_object_or_404(Mall, pk=mall_id)
        unit = get_object_or_404(RetailUnit, pk=unit_id, mall=mall)

        if unit.leased and unit.tenant_id:
            messages.error(request, "This unit is still leased. End the lease first.")
            return redirect("mall:mall_detail", mall_id=mall.id)

        tenant_id = request.POST.get("tenant", "")
        if not tenant_id.isdigit():
            messages.error(request, "Please choose a tenant.")
            return redirect("mall:mall_detail", mall_id=mall.id)

        tenant = get_object_or_404(Tenant, pk=tenant_id, malls=mall)

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
                pass  # keep previous rent

        unit.tenant = tenant
        unit.leased = True
        unit.leased_date = timezone.localdate()
        unit.leased_tenure = months
        unit.renewal_date = timezone.localdate() + timedelta(days=30 * months)
        unit.status = "Active"
        unit.save()

        messages.success(
            request,
            f'"{unit.title}" has been assigned to {tenant.name} until {unit.renewal_date}.',
        )
        return redirect("mall:mall_detail", mall_id=mall.id)


class TenantDetailView(MallStaffRequiredMixin, DetailView):
    """View one tenant under this mall: units, products, payments."""

    template_name = "mall/tenant_detail.html"
    context_object_name = "tenant"
    pk_url_kwarg = "tenant_id"

    def get_queryset(self):
        self.mall = get_object_or_404(Mall, pk=self.kwargs["mall_id"])
        return self.mall.tenants.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mall = self.mall
        tenant = self.object
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

        ctx.update(
            {
                "mall": mall,
                "units": units,
                "products": products,
                "purchases": purchases,
                "payment_total": payment_total,
                "lease_payments": lease_payments,
                "today": timezone.localdate(),
            }
        )
        return ctx


class PaymentOverviewView(MallStaffRequiredMixin, DetailView):
    """Sales payments + lease payments for this mall."""

    model = Mall
    template_name = "mall/payment_overview.html"
    context_object_name = "mall"
    pk_url_kwarg = "mall_id"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mall = self.object
        tenant_ids = list(mall.tenants.values_list("id", flat=True))
        purchases = (
            CustomerPurchase.objects.filter(tenant_id__in=tenant_ids)
            .select_related("customer", "tenant", "retail_unit")
            .prefetch_related("payments")
            .order_by("-purchase_date")
        )

        paginator = Paginator(purchases, 25)
        page = paginator.get_page(self.request.GET.get("page"))

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

        ctx.update(
            {
                "page_obj": page,
                "purchases": page,
                "payment_total": payment_total,
                "purchase_count": purchases.count(),
                "lease_payments": lease_payments,
                "lease_total": lease_total,
            }
        )
        return ctx


class LeaseActionView(MallStaffRequiredMixin, View):
    """
    Action when a retail unit lease has expired (or is about to).
    Supported actions: renew, end, mark_pending.
    """

    http_method_names = ["post"]

    def post(self, request, mall_id, unit_id):
        mall = get_object_or_404(Mall, pk=mall_id)
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
            # Fully release the unit so it can be assigned to someone else
            unit.leased = False
            unit.tenant = None
            unit.status = "Available"
            unit.renewal_date = None
            unit.leased_date = None
            unit.leased_tenure = None
            unit.save(
                update_fields=[
                    "leased",
                    "tenant",
                    "status",
                    "renewal_date",
                    "leased_date",
                    "leased_tenure",
                    "updated_at",
                ]
            )
            messages.success(
                request,
                f'Lease for "{unit.title}" has been ended. You can now assign it to another tenant.',
            )

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