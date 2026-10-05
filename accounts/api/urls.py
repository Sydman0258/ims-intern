from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    UserList,
    UserDetail,
    UserCreate,
    AdminList,
    TenantList,
    MallManagerList,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", LogoutView.as_view(), name="api-logout"),
    path("me/", MeView.as_view(), name="api-me"),

    path("users/", UserList.as_view(), name="user-list"),
    path("users/create/", UserCreate.as_view(), name="user-create"),
    path("users/<int:user_id>/", UserDetail.as_view(), name="user-detail"),

    path("admins/", AdminList.as_view(), name="admin-list"),
    path("tenants/", TenantList.as_view(), name="tenant-list"),
    path("mall-managers/", MallManagerList.as_view(), name="mall-manager-list"),
]