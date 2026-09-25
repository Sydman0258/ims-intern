from django.urls import path

from . import views

app_name = "tenant"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/add-product/", views.AddProductView.as_view(), name="add_product"),
    path("dashboard/edit-products/<int:pk>", views.EditProductView.as_view(), name="edit_products"),
    path(
        "products/<int:pk>/delete/",
        views.DeleteProductView.as_view(),
        name="delete_product",
    ),
    path(
        "dashboard/add-retail-unit/",
        views.AddRetailUnitView.as_view(),
        name="add_retail_unit",
    ),
    path("dashboard/record-sale/", views.RecordSaleView.as_view(), name="record_sale"),
    path(
        "dashboard/payments/",
        views.PaymentHistoryView.as_view(),
        name="payment_history",
    ),
    path(
        "dashboard/purchases/<int:pk>/",
        views.PurchaseDetailView.as_view(),
        name="purchase_detail",
    ),
    path(
        "products-by-retail-unit/",
        views.ProductsByRetailUnitView.as_view(),
        name="products_by_retail_unit",
    ),
  
]
