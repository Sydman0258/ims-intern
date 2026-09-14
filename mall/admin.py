from django.contrib import admin
from .models import Mall

@admin.register(Mall)
class MallAdmin(admin.ModelAdmin):
    list_display=("name","floors","total_shops","num_leased","created_at")
    list_filter=("name","floors")

# Register your models here.
