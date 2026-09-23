from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "retail_unit",
        "price",
        "stock_quantity",
        "status",
        "created_at",
    )
    list_filter = ("retail_unit__mall",)
    search_fields = ("name", "retail_unit__title")
    raw_id_fields = ("retail_unit",)
