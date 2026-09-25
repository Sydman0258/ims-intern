from django.urls import path

from . import views

app_name = "customer"

urlpatterns = [
    path("", views.ShopView.as_view(), name="index"),
    path("purchase/<int:product_id>/", views.PurchaseView.as_view(), name="purchase"),
    path(
        "receipt/<int:pk>/",
        views.PurchaseDetailView.as_view(),
        name="purchase_detail",
    ),
]
