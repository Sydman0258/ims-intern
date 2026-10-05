from rest_framework import serializers

from accounts.models import User, Role


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
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "email",
            "fullname",
            "password",
            "role",
        ]

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data
        )


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