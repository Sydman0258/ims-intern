from rest_framework import serializers

from mall.models import Mall
from tenant.models import Tenant, RetailUnit


class MallListSerializer(serializers.ModelSerializer):
    tenant_count = serializers.IntegerField(read_only=True)
    unit_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Mall
        fields = [
            "id",
            "name",
            "floors",
            "total_shops",
            "num_leased",
            "tenant_count",
            "unit_count",
        ]


class MallBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mall
        fields = ["id", "name", "floors", "total_shops", "num_leased"]


class TenantInMallSerializer(serializers.ModelSerializer):
    unit_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tenant
        fields = ["id", "name", "email", "phone", "unit_count"]


class RetailUnitInMallSerializer(serializers.ModelSerializer):
    tenant = serializers.CharField(source="tenant.name", allow_null=True, read_only=True)
    lease_status = serializers.CharField(source="lease_status_label", read_only=True)

    class Meta:
        model = RetailUnit
        fields = [
            "id",
            "title",
            "leased",
            "tenant",
            "monthly_rent",
            "lease_status",
        ]
