
from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from product.resources import ProductResource

from .models import Product, Category, Tags




@admin.register(Product)
class ProductsAdmin(ImportExportModelAdmin):

    resource_class = ProductResource

    list_display = (
        "id",
        "name",
        "retail_unit",
        "category",
        "price",
        "stock_quantity",
        "status",
        "created_at",
    )

    list_filter = (
        "retail_unit__mall",
        "category",
        "status",
    )

    search_fields = (
        "name",
        "retail_unit__title",
        "category__name",
    )

    raw_id_fields = ("retail_unit",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):

    list_display = ("id", "name")
    search_fields = ("name",)