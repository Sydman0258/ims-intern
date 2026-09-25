"""
Reusable mixins for class-based views: login + role checks.
Works with both session auth and CookieJWTAuthentication.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from .models import Role


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restrict access to users whose role is in `allowed_roles`.
    Subclasses set: allowed_roles = (Role.ADMIN, Role.MALL_MANAGER)
    """

    allowed_roles = ()
    login_url = "accounts:login"

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        raise PermissionDenied("You do not have permission to access this page.")


class MallStaffRequiredMixin(RoleRequiredMixin):
    """Mall managers and admins."""
    allowed_roles = (Role.MALL_MANAGER, Role.ADMIN)


class TenantRequiredMixin(RoleRequiredMixin):
    """Tenant users only."""
    allowed_roles = (Role.TENANT,)

    def get_tenant(self):
        """Return the Tenant profile for the current user, or None."""
        from tenant.models import Tenant
        user = self.request.user
        if user.role != Role.TENANT:
            return None
        try:
            return user.tenant_profile
        except Tenant.DoesNotExist:
            return None
