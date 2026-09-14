from django.contrib import admin
from .models import Tenant, RetailUnit

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display=("name","email","phone","created_at")

@admin.register(RetailUnit)
class RetailUnitAdmin(admin.ModelAdmin):
    list_display=("title","mall","tenant","leased","status")
    list_filter=("leased","status","mall")
