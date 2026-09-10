# from rest_framework.permissions import BasePermission


# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated
#             and request.user.role == "admin"
#         )


# class IsOwner(BasePermission):
#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated
#             and request.user.role == "owner"
#         )


# class IsCustomer(BasePermission):
#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated
#             and request.user.role == "customer"
#         )


# class IsAdminOrReadOnly(BasePermission):
#     def has_permission(self, request, view):
#         if request.method in ["GET", "HEAD", "OPTIONS"]:
#             return True

#         return (
#             request.user.is_authenticated
#             and request.user.role == "admin"
#         )

