from django.contrib import admin
from .models import (
    Customer,
    CustomerPurchase,
    CustomerPurchaseItem,
    CustomerPayment,
    CustomerReview,
    CustomerReviewItem,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "phone")


class CustomerPurchaseItemInline(admin.TabularInline):
    model = CustomerPurchaseItem
    extra = 0


class CustomerPaymentInline(admin.TabularInline):
    model = CustomerPayment
    extra = 0


@admin.register(CustomerPurchase)
class CustomerPurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "tenant", "purchase_date", "total_amount", "full_paid")
    list_filter = ("full_paid", "tenant")
    search_fields = ("customer__name", "tenant__name")
    inlines = [CustomerPurchaseItemInline, CustomerPaymentInline]


@admin.register(CustomerPurchaseItem)
class CustomerPurchaseItemAdmin(admin.ModelAdmin):
    list_display = ("purchase", "product", "quantity", "unit_price", "total_price")


@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = ("purchase", "amount", "payment_method", "payment_status", "payment_date")
    list_filter = ("payment_status", "payment_method")


class CustomerReviewItemInline(admin.TabularInline):
    model = CustomerReviewItem
    extra = 0


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "tenant", "rating", "review_date", "status")
    list_filter = ("rating", "status")
    inlines = [CustomerReviewItemInline]


@admin.register(CustomerReviewItem)
class CustomerReviewItemAdmin(admin.ModelAdmin):
    list_display = ("review", "product")