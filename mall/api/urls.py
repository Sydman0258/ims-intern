from django.urls import path
from .views import MallList, MallDetail

urlpatterns = [
    path("", MallList.as_view(), name="mall_list"),
    path("<int:mall_id>/", MallDetail.as_view(), name="mall_detail"),
]
