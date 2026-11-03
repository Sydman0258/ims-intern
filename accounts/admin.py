from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import User, Role
from tenant.models import Tenant
from mall.models import Mall


def ensure_profile(obj):
    """Create/link Tenant or Mall profile for a user (idempotent)."""
    if obj.role == Role.TENANT:
        if Tenant.objects.filter(user=obj).exists():
            return
        unlinked = Tenant.objects.filter(user__isnull=True, email=obj.email).first()
        if unlinked:
            unlinked.user = obj
            unlinked.save(update_fields=["user"])
            return
        Tenant.objects.create(user=obj, name=obj.fullname or obj.email, email=obj.email)

    elif obj.role == Role.MALL_MANAGER:
        if Mall.objects.filter(user=obj).exists():
            return
        unlinked = Mall.objects.filter(user__isnull=True, email=obj.email).first()
        if unlinked:
            unlinked.user = obj
            unlinked.save(update_fields=["user"])
            return
        name = obj.fullname or obj.email
        if Mall.objects.filter(name=name).exists():
            name = f"{name} ({obj.email})"
        Mall.objects.create(user=obj, name=name, email=obj.email, floors=0, total_shops=0)


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ("id", "email", "fullname", "role", "is_staff", "is_active", "is_superuser")
        export_order = fields

    def after_init_instance(self, instance, new, row, **kwargs):
        if new:
            instance.set_password("ims123")

    def after_save_instance(self, instance, row, **kwargs):
        # if not kwargs.get("dry_run", False):
            ensure_profile(instance)


class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    model = User
    resource_class = UserResource

    list_filter = ("is_staff", "is_active", "role")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("fullname", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "fullname", "role", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    list_display = ("email", "fullname", "role", "is_staff", "is_active")
    search_fields = ("email", "fullname")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ensure_profile(obj)


admin.site.register(User, UserAdmin)