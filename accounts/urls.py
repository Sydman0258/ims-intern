from django.urls import path

from . import views
# from . import jwt_views

app_name = "accounts"

urlpatterns = [
    # Template-based auth (class-based)
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),


]
