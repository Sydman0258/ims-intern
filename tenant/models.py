from django.db import models
from django.conf import settings
from django.utils import timezone

from mall.models import Mall


class Tenant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_profile",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=255, null=True, blank=True,unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    malls = models.ManyToManyField(Mall, blank=True, related_name="tenants")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RetailUnit(models.Model):
    mall = models.ForeignKey(
        Mall, on_delete=models.CASCADE, related_name="retail_unit")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.SET_NULL, related_name="retail_unit",blank=True,null=True)
    title = models.CharField(max_length=100)
    leased = models.BooleanField(default=False)
    leased_date = models.DateField(null=True, blank=True)
    leased_tenure = models.IntegerField(
        null=True, blank=True, help_text="Lease duration in months")
    renewal_date = models.DateField(null=True, blank=True)
    monthly_rent = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
     super().save(*args, **kwargs)

     if self.tenant:
        self.tenant.malls.add(self.mall)    

    @property
    def is_lease_expired(self):
        if not self.renewal_date:
            return False
        return self.renewal_date < timezone.localdate()

    @property
    def lease_status_label(self):
        if not self.leased:
            return "Not leased"
        if self.is_lease_expired:
            return "Expired"
        if self.renewal_date:
            days = (self.renewal_date - timezone.localdate()).days
            if days <= 30:
                return f"Expiring in {days} day(s)"
        return self.status or "Active"


class LeasePayment(models.Model):
    """Rent / lease payments paid by a tenant for a retail unit (seen by mall)."""

    retail_unit = models.ForeignKey(
        RetailUnit, on_delete=models.CASCADE, related_name="lease_payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    paid_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
            ("waived", "Waived"),
        ],
        default="pending",
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end", "-created_at"]

    def __str__(self):
        return f"Lease payment #{self.pk} — {self.retail_unit.title}"
