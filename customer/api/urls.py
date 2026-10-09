from rest_framework.routers import SimpleRouter
from customer.api.views import RecordSale
from django.urls import path

from .views import CustomerViewSet, PurchaseViewSet

router = SimpleRouter()
router.register(r"", CustomerViewSet, basename="customer")
router.register(r"purchases", PurchaseViewSet, basename="purchase")

urlpatterns=[
    path("sales/", RecordSale.as_view(), name="record-sale"),

]
urlpatterns += router.urls
