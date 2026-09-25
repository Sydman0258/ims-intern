from django.urls import path
from .views import mall_list, mall_detail

urlpatterns = [
    path("", mall_list, name="mall_list"),
    path("<int:mall_id>/", mall_detail, name="mall_detail"),
]
