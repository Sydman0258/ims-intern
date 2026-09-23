from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils.html import format_html

from accounts.models import Role, User
from .models import Mall


@admin.register(Mall)
class MallAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "floors", "total_shops", "num_leased", "user_link", "created_at")
    list_filter = ("name", "floors")
    search_fields = ("name", "email", "phone", "user__email", "user__fullname")
    raw_id_fields = ("user",)
    actions = ["create_user_and_send_credentials"]

    fieldsets = (
        (None, {
            "fields": ("name", "email", "phone", "floors", "total_shops", "num_leased"),
        }),
        ("Manager account link", {
            "fields": ("user",),
            "description": (
                "Link this mall to an existing User (role must be 'mall'). "
                "Leave blank if the manager has no login yet. "
                "Prefer the action 'Create manager account & email login credentials'."
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    def user_link(self, obj):
        if obj.user_id:
            return format_html(
                '<a href="/admin/accounts/user/{}/change/">{}</a>',
                obj.user_id,
                obj.user.email,
            )
        return "—"
    user_link.short_description = "Manager account"

    @admin.action(description="Create manager account & email login credentials")
    def create_user_and_send_credentials(self, request, queryset):
        """
        For each selected mall:
        - No user linked   -> create a User (role=mall) with a random password.
        - User already set -> reset the password to a new random one.
        - Email the credentials to the mall's email address.
        """
        created = reset = failed = 0

        for mall in queryset:
            recipient = mall.email
            if not recipient:
                self.message_user(
                    request,
                    f"Mall '{mall.name}' has no email address. Skipped.",
                    level=messages.WARNING,
                )
                failed += 1
                continue

            temp_password = get_random_string(length=10)

            try:
                if mall.user_id:
                    user = mall.user
                    user.set_password(temp_password)
                    user.role = Role.MALL_MANAGER
                    user.save()
                    action_type = "reset"
                else:
                    if User.objects.filter(email=recipient).exists():
                        self.message_user(
                            request,
                            f"A user with email {recipient} already exists. "
                            f"Link it manually to mall '{mall.name}'.",
                            level=messages.ERROR,
                        )
                        failed += 1
                        continue

                    user = User.objects.create_user(
                        email=recipient,
                        password=temp_password,
                        fullname=mall.name,
                        role=Role.MALL_MANAGER,
                    )
                    mall.user = user
                    mall.save(update_fields=["user"])
                    action_type = "created"

                send_mail(
                    subject="Your Mall Management System login credentials",
                    message=(
                        f"Hello {mall.name},\n\n"
                        f"A manager account has been set up for you on the Mall Management System.\n\n"
                        f"Login details:\n"
                        f"  Email (username): {recipient}\n"
                        f"  Temporary password: {temp_password}\n\n"
                        f"Please log in and change your password after first login.\n\n"
                        f"Regards,\nMall Admin"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )

                if action_type == "created":
                    created += 1
                else:
                    reset += 1

            except Exception as e:
                self.message_user(
                    request,
                    f"Failed for mall '{mall.name}' ({recipient}): {e}",
                    level=messages.ERROR,
                )
                failed += 1

        if created:
            self.message_user(request, f"Created manager account and emailed credentials for {created} mall(s).", level=messages.SUCCESS)
        if reset:
            self.message_user(request, f"Reset password and emailed new credentials for {reset} mall(s).", level=messages.SUCCESS)
        if failed and not (created or reset):
            self.message_user(request, "No credentials were sent. Check the error messages above.", level=messages.ERROR)
