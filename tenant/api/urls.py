# from django.urls import path
# from rest_framework.routers import DefaultRouter

# from .views import (
#     AddRetailUnit,
#     Dashboard,
#     ProductCreate,
#     ProductDelete,
#     ProductDetail,
#     ProductList,
#     ProductUpdate,
#     RecordSale,
#     ProductViewsets
# )

# urlpatterns = [
#     path("dashboard/", Dashboard.as_view(), name="dashboard"),
#     path("retail-units/add/", AddRetailUnit.as_view(), name="add-retail-unit"),
#     path("products/", ProductList.as_view(), name="product-list"),
#     path("products/create/", ProductCreate.as_view(), name="product-create"),
#     path("products/<int:pk>/", ProductDetail.as_view(), name="product-detail"),
#     path("products/<int:pk>/update/", ProductUpdate.as_view(), name="product-update"),
#     path("products/<int:pk>/delete/", ProductDelete.as_view(), name="product-delete"),
#     path("sales/", RecordSale.as_view(), name="record-sale"),
#     path()
# ]
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AddRetailUnit,
    Dashboard,
    ProductViewModelSet,
    # RecordSale,
)

router = DefaultRouter()
router.register(r"products", ProductViewModelSet, basename="product")

urlpatterns = [
    path("dashboard/", Dashboard.as_view(), name="dashboard"),
    path("retail-units/add/", AddRetailUnit.as_view(), name="add-retail-unit"),
]

urlpatterns += router.urls