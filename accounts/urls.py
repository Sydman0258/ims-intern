from django.urls import path

from . import views
# from . import jwt_views

app_name = "accounts"

urlpatterns = [
    # Template-based auth (class-based)
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # JWT cookie API endpoints
    # path("api/login/", jwt_views.CookieTokenObtainPairView.as_view(), name="api_login"),
    # path("api/logout/", jwt_views.CookieTokenLogoutView.as_view(), name="api_logout"),
    # path("api/refresh/", jwt_views.CookieTokenRefreshView.as_view(), name="api_refresh"),
    # path("api/me/", jwt_views.MeView.as_view(), name="api_me"),
]
