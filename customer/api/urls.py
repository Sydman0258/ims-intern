from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CustomerList, PurchaseViewSet

router = DefaultRouter()
router.register(r"purchases", PurchaseViewSet, basename="purchase")

urlpatterns = [
    path("", CustomerList.as_view(), name="customer_list"),
] + router.urls