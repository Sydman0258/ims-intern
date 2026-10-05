from rest_framework.permissions import BasePermission

from accounts.models import Role


class _RolePermission(BasePermission):
    allowed_roles: tuple = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in self.allowed_roles
        )


class IsAdminRole(_RolePermission):
    """Users whose role is 'admin'."""
    allowed_roles = (Role.ADMIN,)
    message = "Admin role required."


class IsMallStaff(_RolePermission):
    """Admins and mall managers (mirrors MallStaffRequiredMixin)."""
    allowed_roles = (Role.ADMIN, Role.MALL_MANAGER)
    message = "Admin or mall manager role required."


class IsTenantWithProfile(BasePermission):
    
    message = "Tenant account with a tenant profile required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.role == Role.TENANT):
            return False
        return hasattr(user, "tenant_profile")
