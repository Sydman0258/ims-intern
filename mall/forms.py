from datetime import timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from tenant.models import RetailUnit, Tenant

User = get_user_model()


class CreateTenantForm(forms.Form):
    """Mall manager creates a tenant and optionally a login account."""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Shop / tenant name"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tenant@example.com"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
    )
    create_login = forms.BooleanField(
        required=False,
        initial=True,
        label="Create login account for this tenant",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    password = forms.CharField(
        required=False,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Temporary password (min 6 chars)"}
        ),
        help_text="Required if creating a login account.",
    )

    def clean(self):
        cleaned = super().clean()
        create_login = cleaned.get("create_login")
        email = cleaned.get("email")
        password = cleaned.get("password")

        if create_login:
            if not email:
                self.add_error("email", "Email is required to create a login account.")
            if not password:
                self.add_error("password", "Password is required to create a login account.")
            elif email and User.objects.filter(email__iexact=email).exists():
                self.add_error("email", "A user with this email already exists.")
        return cleaned

    def save(self, mall):
        """Create Tenant, optionally User, and assign to the mall."""
        with transaction.atomic():
            user = None
            if self.cleaned_data.get("create_login"):
                user = User.objects.create_user(
                    email=self.cleaned_data["email"],
                    password=self.cleaned_data["password"],
                    fullname=self.cleaned_data["name"],
                    role=Role.TENANT,
                )

            tenant = Tenant.objects.create(
                user=user,
                name=self.cleaned_data["name"],
                email=self.cleaned_data.get("email") or None,
                phone=self.cleaned_data.get("phone") or None,
            )
            tenant.malls.add(mall)
            return tenant


class AssignRetailUnitForm(forms.ModelForm):
    """Mall assigns a retail unit to a tenant of this mall, with lease details."""

    lease_months = forms.IntegerField(
        min_value=1,
        initial=12,
        label="Lease duration (months)",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    class Meta:
        model = RetailUnit
        fields = ["title", "tenant", "monthly_rent"]
        labels = {
            "title": "Retail unit name / number",
            "tenant": "Assign to tenant",
            "monthly_rent": "Monthly lease amount (₹)",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Unit A-12 or Fashion Hub",
                }
            ),
            "tenant": forms.Select(attrs={"class": "form-select"}),
            "monthly_rent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "e.g. 25000"}
            ),
        }

    def __init__(self, *args, mall=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.mall = mall
        if mall is not None:
            self.fields["tenant"].queryset = mall.tenants.order_by("name")
            self.fields["tenant"].empty_label = "Select tenant"
        self.fields["tenant"].required = True
        self.fields["title"].required = True
        self.fields["monthly_rent"].required = False

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get("title")
        if self.mall and title:
            title = title.strip()
            cleaned["title"] = title
            clash = RetailUnit.objects.filter(mall=self.mall, title__iexact=title)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error("title", f"{self.mall.name} already has a unit with this name.")
        return cleaned

    def save(self, commit=True):
        unit = super().save(commit=False)
        unit.mall = self.mall
        unit.leased = True
        unit.leased_date = timezone.localdate()
        months = self.cleaned_data.get("lease_months") or 12
        unit.leased_tenure = months
        unit.renewal_date = timezone.localdate() + timedelta(days=30 * months)
        unit.status = "Active"
        if unit.monthly_rent is None:
            unit.monthly_rent = Decimal("0")
        if commit:
            unit.save()
            # RetailUnit.save also adds mall to tenant.malls
        return unit
