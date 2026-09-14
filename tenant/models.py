from django.db import models
from django.conf import settings

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
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RetailUnit(models.Model):
    mall = models.ForeignKey(
        Mall, on_delete=models.CASCADE, related_name="retail_unit")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="retail_unit")
    title = models.CharField(max_length=100)
    leased = models.BooleanField(default=False)
    leased_date = models.DateField(null=True, blank=True)
    leased_tenure = models.IntegerField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
