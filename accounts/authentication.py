
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):


    def authenticate(self, request):
        raw_token = request.COOKIES.get(
            getattr(settings, "JWT_ACCESS_COOKIE", "access_token")
        )
        if raw_token is None:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
        else:
            raw_token = raw_token.encode("utf-8") if isinstance(raw_token, str) else raw_token

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None

        return self.get_user(validated_token), validated_token
