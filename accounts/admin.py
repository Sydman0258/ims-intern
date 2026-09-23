# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User,Role
from tenant.models import Tenant
from mall.models import Mall


class UserAdmin(BaseUserAdmin):
    model = User
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
    filter_horizontal = ("groups", "user_permissions",)

    def save_model(self, request, obj, form, change):
     super().save_model(request, obj, form, change)

     if obj.role == Role.TENANT:
        if Tenant.objects.filter(user=obj).exists():
            return

        unlinked_tenant = Tenant.objects.filter(
            user__isnull=True,
            email=obj.email
        ).first()

        if unlinked_tenant:
            unlinked_tenant.user = obj
            unlinked_tenant.save(update_fields=["user"])
            return

        Tenant.objects.create(
            user=obj,
            name=obj.fullname or obj.email,
            email=obj.email,
        )

     elif obj.role == Role.MALL_MANAGER:
        if Mall.objects.filter(user=obj).exists():
            return

        unlinked_mall = Mall.objects.filter(
            user__isnull=True,
            email=obj.email
        ).first()

        if unlinked_mall:
            unlinked_mall.user = obj
            unlinked_mall.save(update_fields=["user"])
            return

        name = obj.fullname or obj.email
        if Mall.objects.filter(name=name).exists():
            name = f"{name} ({obj.email})"

        Mall.objects.create(
            user=obj,
            name=name,
            email=obj.email,
            floors=0,
            total_shops=0,
        )

admin.site.register(User, UserAdmin)