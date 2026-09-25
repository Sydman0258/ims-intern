from django.urls import path
from .views import customer_list, purchase_list, purchase_detail

urlpatterns = [
    path("", customer_list, name="customer_list"),
    path("purchases/", purchase_list, name="purchase_list"),
    path("purchases/<int:pk>/", purchase_detail, name="purchase_detail"),
]
