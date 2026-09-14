# ims/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("mall.urls", namespace="mall")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("tenant/", include("tenant.urls", namespace="tenant")),
    path("customer/", include("customer.urls", namespace="customer")),
]