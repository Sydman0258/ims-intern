# """
# JWT authentication that reads tokens from HTTP-only cookies.

# Cookie names (configurable via settings):
#   - access_token
#   - refresh_token
# """

# # from rest_framework_simplejwt.authentication import JWTAuthentication
# # from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from django.conf import settings


# class CookieJWTAuthentication(JWTAuthentication):
#     """
#     Authenticate using a JWT access token stored in an HTTP-only cookie.
#     Falls back to the Authorization header if the cookie is absent
#     (useful for API clients / Swagger).
#     """

#     def authenticate(self, request):
#         # Prefer cookie, then fall back to Authorization header
#         raw_token = request.COOKIES.get(
#             getattr(settings, "JWT_ACCESS_COOKIE", "access_token")
#         )
#         if raw_token is None:
#             header = self.get_header(request)
#             if header is None:
#                 return None
#             raw_token = self.get_raw_token(header)
#             if raw_token is None:
#                 return None
#         else:
#             raw_token = raw_token.encode("utf-8") if isinstance(raw_token, str) else raw_token

#         try:
#             validated_token = self.get_validated_token(raw_token)
#         except (InvalidToken, TokenError):
#             return None

#         return self.get_user(validated_token), validated_token
