from django.db import models

from tenant.models import Tenant

class Product(models.Model):
    shop = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
