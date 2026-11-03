from django.db import models
from tenant.models import RetailUnit


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Tags(models.Model):
    name=models.CharField(max_length=100,blank=True)

    def __str__(self):
        return self.name
class Product(models.Model):

    retail_unit = models.ForeignKey(
        RetailUnit,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    tags=models.ManyToManyField(
        Tags,
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