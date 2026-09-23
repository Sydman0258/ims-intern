# customer/urls.py
from django.urls import path
from . import views

app_name = "customer"

urlpatterns = [
    path("", views.shop, name="index"),
    path("purchase/<int:product_id>/", views.purchase, name="purchase"),
    path("receipt/<int:pk>/", views.purchase_detail, name="purchase_detail"),
]
