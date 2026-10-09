

from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import Role


def _set_jwt_cookies(response, access_token, refresh_token=None):
    """Attach HTTP-only JWT cookies to a Response."""
    access_cookie = getattr(settings, "JWT_ACCESS_COOKIE", "access_token")
    refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE", "refresh_token")
    access_max_age = int(
        getattr(settings, "SIMPLE_JWT", {}).get(
            "ACCESS_TOKEN_LIFETIME", __import__("datetime").timedelta(minutes=30)
        ).total_seconds()
    )
    refresh_max_age = int(
        getattr(settings, "SIMPLE_JWT", {}).get(
            "REFRESH_TOKEN_LIFETIME", __import__("datetime").timedelta(days=7)
        ).total_seconds()
    )
    secure = not settings.DEBUG
    samesite = "Lax"

    response.set_cookie(
        access_cookie,
        access_token,
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            refresh_cookie,
            refresh_token,
            max_age=refresh_max_age,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path="/",
        )
    return response


def _clear_jwt_cookies(response):
    access_cookie = getattr(settings, "JWT_ACCESS_COOKIE", "access_token")
    refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE", "refresh_token")
    response.delete_cookie(access_cookie, path="/")
    response.delete_cookie(refresh_cookie, path="/")
    return response


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Embed role claim for convenience
    refresh["role"] = user.role
    refresh["email"] = user.email
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class CookieTokenObtainPairView(APIView):
    """
    Login with email + password.
    Returns user info in body and sets JWT cookies.
    Also establishes a Django session so template views keep working.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = _tokens_for_user(user)

        # Also create a session for template-based views
        from django.contrib.auth import login
        login(request, user)

        data = {
            "user": {
                "id": user.pk,
                "email": user.email,
                "fullname": user.fullname,
                "role": user.role,
            },
            "redirect": _redirect_path_for_role(user.role),
            "csrfToken": get_token(request),
        }
        response = Response(data, status=status.HTTP_200_OK)
        return _set_jwt_cookies(response, tokens["access"], tokens["refresh"])


class CookieTokenRefreshView(APIView):
    """Refresh the access token using the refresh_token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie = getattr(settings, "JWT_REFRESH_COOKIE", "refresh_token")
        raw = request.COOKIES.get(refresh_cookie) or request.data.get("refresh")
        if not raw:
            return Response(
                {"detail": "Refresh token not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(raw)
            access = str(refresh.access_token)
        except (TokenError, InvalidToken):
            response = Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return _clear_jwt_cookies(response)

        response = Response({"detail": "Token refreshed."}, status=status.HTTP_200_OK)
        return _set_jwt_cookies(response, access)


class CookieTokenLogoutView(APIView):
    """Clear JWT cookies and destroy the session."""

    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        return _clear_jwt_cookies(response)


class MeView(APIView):
    """Return the currently authenticated user (session or JWT cookie)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.pk,
                "email": user.email,
                "fullname": getattr(user, "fullname", ""),
                "role": user.role,
            }
        )


def _redirect_path_for_role(role):
    if role == Role.ADMIN:
        return "/admin/"
    if role == Role.TENANT:
        return "/tenant/dashboard/"
    if role == Role.MALL_MANAGER:
        return "/mall-manager/"
    return "/accounts/login/"
