from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, FormView, DetailView,DeleteView
from django.shortcuts import get_object_or_404
from accounts.mixins import TenantRequiredMixin
from customer.models import CustomerPayment, CustomerPurchase
from customer.services import InsufficientStock, create_offline_purchase
from product.models import Product
from django.urls import reverse_lazy

from .forms import OfflineSaleForm, ProductForm
from .models import RetailUnit


class DashboardView(TenantRequiredMixin, TemplateView):
    template_name = "tenant/dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()
        if self.tenant is None:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.tenant
        products = (
            Product.objects.filter(retail_unit__tenant=tenant)
            .select_related("retail_unit", "retail_unit__mall")
            .order_by("name")
        )
        ctx.update(
            {
                "tenant": tenant,
                "malls": tenant.malls.order_by("name"),
                "retail_units": RetailUnit.objects.filter(tenant=tenant).select_related("mall"),
                "products": products,
                "recent_purchases": (
                    CustomerPurchase.objects.filter(tenant=tenant)
                    .select_related("customer", "retail_unit")
                    .order_by("-purchase_date")[:8]
                ),
                "purchase_count": CustomerPurchase.objects.filter(tenant=tenant).count(),
            }
        )
        return ctx


class AddRetailUnitView(TenantRequiredMixin, View):
    """Retail units are assigned by the mall manager, not created by tenants."""

    def get(self, request):
        tenant = self.get_tenant()
        if tenant is None:
            return redirect("accounts:login")
        messages.info(
            request,
            "Retail stores are assigned by the mall manager. Once assigned, you can add products to them.",
        )
        return redirect("tenant:dashboard")


class AddProductView(TenantRequiredMixin, FormView):
    template_name = "tenant/add_products.html"
    form_class = ProductForm

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()
        if self.tenant is None:
            return redirect("accounts:login")
        if not RetailUnit.objects.filter(tenant=self.tenant).exists():
            messages.warning(
                request,
                "No retail store assigned yet. Wait for the mall manager to assign one, then add products.",
            )
            return redirect("tenant:add_retail_unit")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenant"] = self.tenant
        return ctx

    def form_valid(self, form):
        product = form.save()
        messages.success(
            self.request,
            f'Product "{product.name}" added to {product.retail_unit.title}.',
        )
        return redirect("tenant:dashboard")

class EditProductView(TenantRequiredMixin, FormView):
    model = Product
    template_name = "tenant/edit_products.html"
    form_class = ProductForm

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()

        if self.tenant is None:
            return redirect("accounts:login")

        if not RetailUnit.objects.filter(tenant=self.tenant).exists():
            messages.warning(
                request,
                "No retail store assigned yet. Wait for the mall manager to assign one, then edit products.",
            )
            return redirect("tenant:add_retail_unit")

        self.product = get_object_or_404(
            Product,
            pk=kwargs["pk"],
            retail_unit__tenant=self.tenant,
        )

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.tenant
        kwargs["instance"] = self.product
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenant"] = self.tenant
        return ctx

    def form_valid(self, form):
        product = form.save()

        messages.success(
            self.request,
            f'Product "{product.name}" edited in {product.retail_unit.title}.',
        )

        return redirect("tenant:dashboard")
class DeleteProductView(TenantRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("tenant:dashboard")

    def get_queryset(self):
        tenant = self.get_tenant()
        return Product.objects.filter(retail_unit__tenant=tenant)


class RecordSaleView(TenantRequiredMixin, FormView):
    """Tenant records an offline / in-store purchase."""

    template_name = "tenant/record_sale.html"
    form_class = OfflineSaleForm

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()
        if self.tenant is None:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenant"] = self.tenant
        return ctx

    def form_valid(self, form):
        try:
            purchase = create_offline_purchase(
                tenant=self.tenant,
                retail_unit=form.cleaned_data["retail_unit"],
                name=form.cleaned_data["customer_name"],
                phone=form.cleaned_data["customer_phone"],
                items=[
                    {
                        "product_id": form.cleaned_data["product"].pk,
                        "quantity": form.cleaned_data["quantity"],
                    }
                ],
                payment_method=form.cleaned_data["payment_method"],
            )
        except InsufficientStock as exc:
            form.add_error("quantity", str(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            f"Sale recorded: {form.cleaned_data['quantity']} × "
            f"{form.cleaned_data['product'].name} "
            f"(₹{purchase.total_amount}) at {form.cleaned_data['retail_unit'].title}.",
        )
        return redirect("tenant:purchase_detail", pk=purchase.pk)


class PaymentHistoryView(TenantRequiredMixin, TemplateView):
    """Full payment / purchase history for this tenant's shops."""

    template_name = "tenant/payment_history.html"

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()
        if self.tenant is None:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.tenant
        purchases = (
            CustomerPurchase.objects.filter(tenant=tenant)
            .select_related("customer", "retail_unit")
            .prefetch_related("items__product", "payments")
            .order_by("-purchase_date")
        )

        paginator = Paginator(purchases, 20)
        page = paginator.get_page(self.request.GET.get("page"))

        payments = CustomerPayment.objects.filter(purchase__tenant=tenant)
        total_received = sum((p.amount for p in payments), start=0) or 0

        ctx.update(
            {
                "tenant": tenant,
                "page_obj": page,
                "purchases": page,
                "total_received": total_received,
                "purchase_count": purchases.count(),
            }
        )
        return ctx


class PurchaseDetailView(TenantRequiredMixin, DetailView):
    """Detail of one purchase belonging to this tenant."""

    template_name = "tenant/purchase_detail.html"
    context_object_name = "purchase"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        self.tenant = self.get_tenant()
        if self.tenant is None:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            CustomerPurchase.objects.filter(tenant=self.tenant)
            .select_related("customer", "tenant", "retail_unit")
            .prefetch_related("items__product", "payments")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenant"] = self.tenant
        return ctx


class ProductsByRetailUnitView(TenantRequiredMixin, View):
    """JSON endpoint: products available in a given retail unit."""

    def get(self, request):
        tenant = self.get_tenant()
        if tenant is None:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        retail_unit_id = request.GET.get("retail_unit")
        if not retail_unit_id:
            return JsonResponse({"products": []})

        products = Product.objects.filter(
            retail_unit_id=retail_unit_id,
            retail_unit__tenant=tenant,
            stock_quantity__gt=0,
        ).order_by("name")

        return JsonResponse(
            {
                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "stock": product.stock_quantity,
                    }
                    for product in products
                ]
            }
        )
