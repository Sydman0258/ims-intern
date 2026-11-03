
from django.contrib import admin
from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget,ManyToManyWidget
from import_export.admin import ImportExportModelAdmin

from .models import Product, Category, Tags
from tenant.models import RetailUnit


class ProductResource(resources.ModelResource):

    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(Category, "name")
    )

    retail_unit = fields.Field(
        column_name="retail_unit",
        attribute="retail_unit",
        widget=ForeignKeyWidget(RetailUnit, "title")
    )

    tags=fields.Field(
        column_name="tags",
        attribute="tags",
        widget=ManyToManyWidget(Tags,field="name",separator=", ")
    )
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "image",
            "category",
            "stock_quantity",
            "retail_unit",
            "price",
            "status",
            "tags"
        )


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