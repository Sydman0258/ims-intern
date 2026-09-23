from django.urls import path

from . import views

app_name = "mall"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:mall_id>/", views.mall_detail, name="mall_detail"),
    path("<int:mall_id>/tenants/assign/", views.assign_tenant, name="assign_tenant"),
    path("<int:mall_id>/tenants/create/", views.create_tenant, name="create_tenant"),
    path("<int:mall_id>/tenants/<int:tenant_id>/", views.tenant_detail, name="tenant_detail"),
    path("<int:mall_id>/tenants/<int:tenant_id>/remove/", views.remove_tenant, name="remove_tenant"),
    path("<int:mall_id>/retail-units/assign/", views.assign_retail_unit, name="assign_retail_unit"),
    path("<int:mall_id>/payments/", views.payment_overview, name="payment_overview"),
    path("<int:mall_id>/units/<int:unit_id>/lease-action/", views.lease_action, name="lease_action"),
]
