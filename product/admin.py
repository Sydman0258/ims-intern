from django.contrib import admin
from .models import Product

@admin.register
class ProductsAdmin(admin.ModelAdmin):
    list_display=("name","description","price","stock_quantity","status","created_at")
# Register your models here.
