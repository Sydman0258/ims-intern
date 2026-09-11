# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "fullname", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("fullname",)}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "fullname", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    search_fields = ("email", "fullname")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)


admin.site.register(User, UserAdmin)