from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.views import View

from accounts.models import Role

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


class HomeView(View):
    """Send authenticated users to their role dashboard; others to login."""

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.role == Role.ADMIN:
                return redirect("/admin/")

            if request.user.role == Role.TENANT:
                return redirect("tenant:dashboard")

            if request.user.role == Role.MALL_MANAGER:
                return redirect("mall:index")

        return redirect("accounts:login")


urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    path("admin/", admin.site.urls),

    # API
    path("api/tenant/", include("tenant.api.urls")),
    path("api/mall/", include("mall.api.urls")),
    path("api/product/", include("product.api.urls")),
    path("api/customer/", include("customer.api.urls")),
    path("api/accounts/", include("accounts.api.urls")),


    path("mall-manager/", include("mall.urls", namespace="mall")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("tenant/", include("tenant.urls", namespace="tenant")),
    path("customer/", include("customer.urls", namespace="customer")),

    # OpenAPI documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]