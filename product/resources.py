from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget,ManyToManyWidget
from tenant.models import RetailUnit
from .models import Product, Category, Tags


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
