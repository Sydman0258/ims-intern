from django.urls import path

from .views import (
    AddProduct,
    AddRetailUnit,
    Dashboard,
    EditProduct,
    PaymentHistory,
    ProductsByRetailUnit,
    PurchaseDetail,
    RecordSale,
)

urlpatterns = [
    path("dashboard/", Dashboard.as_view(), name="dashboard"),
    path("add-retail-unit/", AddRetailUnit.as_view(), name="add_retail_unit"),

    path("products/", AddProduct.as_view(), name="add_product"),
    path("products/<int:pk>/", EditProduct.as_view(), name="edit_product"),
    path(
        "products-by-retail-unit/",
        ProductsByRetailUnit.as_view(),
        name="products_by_retail_unit",
    ),

    path("record-sale/", RecordSale.as_view(), name="record_sale"),
    path("payments/", PaymentHistory.as_view(), name="payment_history"),
    path("purchases/<int:pk>/", PurchaseDetail.as_view(), name="purchase_detail"),
]
