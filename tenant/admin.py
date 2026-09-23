from django.contrib import admin, messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html
from django.utils.crypto import get_random_string

from accounts.models import Role, User
from .models import Tenant, RetailUnit, LeasePayment


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "mall_list", "user_link", "created_at")
    list_filter = ("malls", "created_at")
    search_fields = ("name", "email", "phone", "user__email", "user__fullname")
    raw_id_fields = ("user",)
    filter_horizontal = ("malls",)
    actions = [
        "send_email_to_selected_tenants",
        "create_user_and_send_credentials",
    ]

    fieldsets = (
        (None, {
            "fields": ("name", "email", "phone"),
        }),
        ("Malls", {
            "fields": ("malls",),
            "description": "The malls this tenant is assigned to. "
                           "The tenant can add retail units in these malls.",
        }),
        ("User account link", {
            "fields": ("user",),
            "description": (
                "Link this tenant to an existing User (role must be 'tenant'). "
                "Leave blank if the tenant has no login yet. "
                "Prefer using the action 'Create user account & email login credentials' "
                "instead of creating the user manually."
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("malls")

    def mall_list(self, obj):
        return ", ".join(m.name for m in obj.malls.all()) or "—"
    mall_list.short_description = "Malls"

    def user_link(self, obj):
        if obj.user_id:
            return format_html(
                '<a href="/admin/accounts/user/{}/change/">{}</a>',
                obj.user_id,
                obj.user.email,
            )
        return "—"
    user_link.short_description = "Linked user"

    @admin.action(description="Send email to selected tenants")
    def send_email_to_selected_tenants(self, request, queryset):
        subject = "Message from Mall Management System"
        body = (
            "Hello,\n\n"
            "This is a notification from the Mall Management System.\n\n"
            "Please log in to your tenant dashboard for more details.\n\n"
            "Regards,\nMall Admin"
        )

        sent = 0
        skipped = 0
        for tenant in queryset:
            recipient = tenant.email or (tenant.user.email if tenant.user_id else None)
            if not recipient:
                skipped += 1
                continue
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                sent += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to send to {recipient}: {e}",
                    level=messages.ERROR,
                )

        if sent:
            self.message_user(
                request,
                f"Successfully sent email to {sent} tenant(s).",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} tenant(s) with no email address.",
                level=messages.WARNING,
            )

    @admin.action(description="Create user account & email login credentials")
    def create_user_and_send_credentials(self, request, queryset):
        """
        For each selected tenant:
        - If no user is linked → create a new User (role=tenant) with a random password.
        - If a user is already linked → reset the password to a new random one.
        - Email the login credentials (email + password) to the tenant.
        """
        created = 0
        reset = 0
        failed = 0

        for tenant in queryset:
            recipient = tenant.email
            if not recipient:
                self.message_user(
                    request,
                    f"Tenant '{tenant.name}' has no email address. Skipped.",
                    level=messages.WARNING,
                )
                failed += 1
                continue

            temp_password = get_random_string(length=10)

            try:
                if tenant.user_id:
                    user = tenant.user
                    user.set_password(temp_password)
                    user.role = Role.TENANT
                    user.save()
                    action_type = "reset"
                else:
                    if User.objects.filter(email=recipient).exists():
                        self.message_user(
                            request,
                            f"A user with email {recipient} already exists. "
                            f"Link it manually to tenant '{tenant.name}'.",
                            level=messages.ERROR,
                        )
                        failed += 1
                        continue

                    user = User.objects.create_user(
                        email=recipient,
                        password=temp_password,
                        fullname=tenant.name,
                        role=Role.TENANT,
                    )
                    tenant.user = user
                    tenant.save(update_fields=["user"])
                    action_type = "created"

                subject = "Your Mall Management System login credentials"
                body = (
                    f"Hello {tenant.name},\n\n"
                    f"An account has been created for you on the Mall Management System.\n\n"
                    f"Login details:\n"
                    f"  Email (username): {recipient}\n"
                    f"  Temporary password: {temp_password}\n\n"
                    f"Please log in and change your password after first login.\n\n"
                    f"Regards,\nMall Admin"
                )

                send_mail(
                    subject=subject,
                    message=body,
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
                    f"Failed for tenant '{tenant.name}' ({recipient}): {e}",
                    level=messages.ERROR,
                )
                failed += 1

        if created:
            self.message_user(
                request,
                f"Created user account and emailed credentials for {created} tenant(s).",
                level=messages.SUCCESS,
            )
        if reset:
            self.message_user(
                request,
                f"Reset password and emailed new credentials for {reset} tenant(s).",
                level=messages.SUCCESS,
            )
        if failed and not (created or reset):
            self.message_user(
                request,
                "No credentials were sent. Check the error messages above.",
                level=messages.ERROR,
            )


@admin.register(RetailUnit)
class RetailUnitAdmin(admin.ModelAdmin):
    list_display = ("title", "mall", "tenant", "leased", "renewal_date", "monthly_rent", "status")
    list_filter = ("leased", "status", "mall")
    search_fields = ("title", "tenant__name", "mall__name")
    raw_id_fields = ("tenant", "mall")

@admin.register(LeasePayment)
class LeasePaymentAdmin(admin.ModelAdmin):
    list_display = ("retail_unit", "amount", "period_start", "period_end", "status", "paid_on")
    list_filter = ("status",)
    search_fields = ("retail_unit__title", "notes")
    raw_id_fields = ("retail_unit",)
