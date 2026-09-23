from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import Role
from customer.models import CustomerPayment, CustomerPurchase
from customer.services import InsufficientStock, create_offline_purchase
from product.models import Product

from .forms import OfflineSaleForm, ProductForm, RetailUnitForm
from .models import RetailUnit, Tenant


def _get_tenant(user):
    """Return the Tenant profile for a tenant user, or None."""
    if user.role != Role.TENANT:
        return None
    try:
        return user.tenant_profile
    except Tenant.DoesNotExist:
        return None


class DashboardView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        # stash it so get() can use it
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        tenant = self.tenant
        products = (
            Product.objects.filter(retail_unit__tenant=tenant)
            .select_related("retail_unit", "retail_unit__mall")
            .order_by("name")
        )
        context = {
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
        return render(request, "tenant/dashboard.html", context)


class AddRetailUnitView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        messages.info(
            request,
            "Retail stores are assigned by the mall manager. Once assigned, you can add products to them.",
        )
        return redirect("tenant:dashboard")


class AddProductView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        tenant = self.tenant
        if not RetailUnit.objects.filter(tenant=tenant).exists():
            messages.warning(
                request,
                "No retail store assigned yet. Wait for the mall manager to assign one, then add products.",
            )
            return redirect("tenant:add_retail_unit")

        form = ProductForm(tenant=tenant)
        return render(
            request,
            "tenant/add_products.html",
            {"tenant": tenant, "form": form},
        )

    def post(self, request):
        tenant = self.tenant
        if not RetailUnit.objects.filter(tenant=tenant).exists():
            messages.warning(
                request,
                "No retail store assigned yet. Wait for the mall manager to assign one, then add products.",
            )
            return redirect("tenant:add_retail_unit")

        form = ProductForm(request.POST, tenant=tenant)
        if form.is_valid():
            product = form.save()
            messages.success(
                request,
                f'Product "{product.name}" added to {product.retail_unit.title}.',
            )
            return redirect("tenant:dashboard")
        return render(
            request,
            "tenant/add_products.html",
            {"tenant": tenant, "form": form},
        )


class RecordSaleView(View):
    """Tenant records an offline / in-store purchase."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = OfflineSaleForm(tenant=self.tenant)
        return render(
            request,
            "tenant/record_sale.html",
            {"tenant": self.tenant, "form": form},
        )

    def post(self, request):
        tenant = self.tenant
        form = OfflineSaleForm(request.POST, tenant=tenant)
        if form.is_valid():
            try:
                purchase = create_offline_purchase(
                    tenant=tenant,
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
            else:
                messages.success(
                    request,
                    f"Sale recorded: {form.cleaned_data['quantity']} × "
                    f"{form.cleaned_data['product'].name} "
                    f"(₹{purchase.total_amount}) at {form.cleaned_data['retail_unit'].title}.",
                )
                return redirect("tenant:purchase_detail", pk=purchase.pk)
        return render(
            request,
            "tenant/record_sale.html",
            {"tenant": tenant, "form": form},
        )


class PaymentHistoryView(View):
    """Full payment / purchase history for this tenant's shops."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        tenant = self.tenant
        purchases = (
            CustomerPurchase.objects.filter(tenant=tenant)
            .select_related("customer", "retail_unit")
            .prefetch_related("items__product", "payments")
            .order_by("-purchase_date")
        )

        paginator = Paginator(purchases, 20)
        page = paginator.get_page(request.GET.get("page"))

        payments = CustomerPayment.objects.filter(purchase__tenant=tenant)
        total_received = sum((p.amount for p in payments), start=0) or 0

        context = {
            "tenant": tenant,
            "page_obj": page,
            "purchases": page,
            "total_received": total_received,
            "purchase_count": purchases.count(),
        }
        return render(request, "tenant/payment_history.html", context)


class PurchaseDetailView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        tenant = _get_tenant(request.user)
        if tenant is None:
            return redirect("accounts:login")
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        purchase = get_object_or_404(
            CustomerPurchase.objects.select_related("customer", "tenant", "retail_unit")
            .prefetch_related("items__product", "payments"),
            pk=pk,
            tenant=self.tenant,
        )
        return render(
            request,
            "tenant/purchase_detail.html",
            {"tenant": self.tenant, "purchase": purchase},
        )


class ProductsByRetailUnitView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        tenant = _get_tenant(request.user)
        if tenant is None:
            return JsonResponse({"error": "Unauthorized"}, status=403)
        self.tenant = tenant
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        retail_unit_id = request.GET.get("retail_unit")

        if not retail_unit_id:
            return JsonResponse({"products": []})

        products = Product.objects.filter(
            retail_unit_id=retail_unit_id,
            retail_unit__tenant=self.tenant,
            stock_quantity__gt=0,
        ).order_by("name")

        return JsonResponse({
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "stock": product.stock_quantity,
                }
                for product in products
            ]
        })
