from django.urls import path
from rest_framework.routers import SimpleRouter

from accounts.jwt_views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    CookieTokenLogoutView,
    MeView as JwtMeView,
)
from .views import (
    UserViewSet,
    AdminList,
    TenantList,
    MallManagerList,
)

router = SimpleRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("login/", CookieTokenObtainPairView.as_view(), name="api-login"),
    path("logout/", CookieTokenLogoutView.as_view(), name="api-logout"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="api-refresh"),
    path("me/", JwtMeView.as_view(), name="api-me"),
    path("admins/", AdminList.as_view(), name="admin-list"),
    path("tenants/", TenantList.as_view(), name="tenant-list"),
    path("mall-managers/", MallManagerList.as_view(), name="mall-manager-list"),
] + router.urls