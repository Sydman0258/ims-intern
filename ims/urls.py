from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from accounts.models import Role


def home(request):
    """Send authenticated users to their role dashboard; others to the shop."""

    if request.user.is_authenticated:

        if request.user.role == Role.ADMIN:
            return redirect("/admin/")

        if request.user.role == Role.TENANT:
            return redirect("tenant:dashboard")

        if request.user.role == Role.MALL_MANAGER:
            return redirect("mall:index")

    return redirect("accounts:login")


urlpatterns = [
    path("", home, name="home"),

    path("admin/", admin.site.urls),

    path("mall-manager/", include("mall.urls", namespace="mall")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("tenant/", include("tenant.urls", namespace="tenant")),
    path("customer/", include("customer.urls", namespace="customer")),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]