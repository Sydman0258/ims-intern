from django.db import models

from tenant.models import Tenant
from product.models import Product
class Customer(models.Model):

    name = models.CharField(max_length=100)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CustomerPurchase(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="purchases")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="purchases") # type: ignore
    purchase_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    full_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Purchase #{self.pk}"


class CustomerPurchaseItem(models.Model):
    purchase = models.ForeignKey(
        CustomerPurchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="purchase_items")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class CustomerPayment(models.Model):
    purchase = models.ForeignKey(
        CustomerPurchase, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=50, null=True, blank=True)
    payment_status = models.CharField(
        max_length=50, null=True, blank=True)
    payment_date = models.DateTimeField()
    transaction_reference = models.CharField(
        max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment #{self.pk}"


class CustomerReview(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="reviews")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="reviews")
    purchase = models.ForeignKey(
        CustomerPurchase, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comment = models.TextField(null=True, blank=True)
    review_date = models.DateTimeField()
    status = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Review #{self.pk} - {self.rating}/5"


class CustomerReviewItem(models.Model):
    review = models.ForeignKey(
        CustomerReview, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="review_items")

    def __str__(self):
        return f"Review #{self.review.pk} - {self.product.name}"
