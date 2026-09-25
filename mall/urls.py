from django.urls import path

from . import views

app_name = "mall"

urlpatterns = [
    path("", views.MallIndexView.as_view(), name="index"),
    path("<int:mall_id>/", views.MallDetailView.as_view(), name="mall_detail"),

    # Tenant management
    path(
        "<int:mall_id>/create-tenant/",
        views.CreateTenantView.as_view(),
        name="create_tenant",
    ),
    path(
        "<int:mall_id>/assign-tenant/",
        views.AssignTenantView.as_view(),
        name="assign_tenant",
    ),
    path(
        "<int:mall_id>/remove-tenant/<int:tenant_id>/",
        views.RemoveTenantView.as_view(),
        name="remove_tenant",
    ),
    path(
        "<int:mall_id>/tenant/<int:tenant_id>/",
        views.TenantDetailView.as_view(),
        name="tenant_detail",
    ),

    # Retail unit
    path(
        "<int:mall_id>/assign-retail-unit/",
        views.AssignRetailUnitView.as_view(),
        name="assign_retail_unit",
    ),
    # Re-assign an existing free unit after ending a lease
    path(
        "<int:mall_id>/unit/<int:unit_id>/reassign/",
        views.ReassignUnitView.as_view(),
        name="reassign_unit",
    ),

    # Lease actions
    path(
        "<int:mall_id>/unit/<int:unit_id>/lease-action/",
        views.LeaseActionView.as_view(),
        name="lease_action",
    ),

    # Payments
    path(
        "<int:mall_id>/payments/",
        views.PaymentOverviewView.as_view(),
        name="payment_overview",
    ),
]