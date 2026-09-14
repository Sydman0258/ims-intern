from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.models import Role, User
from .models import RetailUnit, Tenant
from product.models import Product
from customer.models import CustomerPurchase


def register(request):
    """Public self-service signup for a new tenant (shop owner)."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Shop / tenant name is required.")
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exists():
            errors.append("An account with this email already exists.")
        if not password:
            errors.append("Password is required.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            return render(request, "tenant/register.html", {
                "errors": errors,
                "form_data": {"name": name, "email": email, "phone": phone},
            })

        user = User.objects.create_user(
            email=email,
            password=password,
            fullname=name,
            role=Role.TENANT,
        )
        Tenant.objects.create(user=user, name=name, email=email, phone=phone)

        login(request, user)
        messages.success(request, "Tenant account created successfully.")
        return redirect("tenant:dashboard")

    return render(request, "tenant/register.html")


@login_required
def dashboard(request):
    if request.user.role != Role.TENANT:
        return redirect("accounts:login")

    tenant = request.user.tenant_profile

    context = {
        "tenant": tenant,
        "retail_units": RetailUnit.objects.filter(tenant=tenant),
        "products": Product.objects.filter(shop=tenant),
        "recent_purchases": CustomerPurchase.objects.filter(tenant=tenant).order_by("-purchase_date")[:10],
    }
    return render(request, "tenant/dashboard.html", context)