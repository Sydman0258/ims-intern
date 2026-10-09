from rest_framework import serializers

from accounts.models import User, Role
from tenant.models import Tenant


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "fullname",
            "role",
        ]
        read_only_fields = ["id"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "fullname", "password", "role"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        # Mirror Django admin: tenant users need a Tenant profile
        if user.role == Role.TENANT:
            if not Tenant.objects.filter(user=user).exists():
                unlinked = Tenant.objects.filter(
                    user__isnull=True,
                    email=user.email,
                ).first()
                if unlinked:
                    unlinked.user = user
                    unlinked.save(update_fields=["user"])
                else:
                    Tenant.objects.create(
                        user=user,
                        name=user.fullname or user.email,
                        email=user.email,
                    )

        return user


class AdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "email",
            "fullname",
            "role",
        ]
        read_only_fields = ["id", "role"]

    def create(self, validated_data):
        return User.objects.create_user(
            role=Role.ADMIN,
            **validated_data
        )


class TenantSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "email",
            "fullname",
            "role",
            "created_At"
        ]
        read_only_fields = ["id", "role"]

    def create(self, validated_data):
        return User.objects.create_user(
            role=Role.TENANT,
            **validated_data
        )


class MallManagerSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "email",
            "fullname",
            "role",
        ]
        read_only_fields = ["id", "role"]

    def create(self, validated_data):
        return User.objects.create_user(
            role=Role.MALL_MANAGER,
            **validated_data
        )