from django.db import models

from tenant.models import RetailUnit


class Product(models.Model):
    """Products belong to a retail store (unit), not the tenant company."""

    retail_unit = models.ForeignKey(
        RetailUnit,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def tenant(self):
        return self.retail_unit.tenant

    @property
    def shop(self):
        """Backward-compatible alias used in older code."""
        return self.retail_unit.tenant
