from django.contrib.auth import authenticate, logout
from accounts.api.pagination import UserPaginationView
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters

from accounts.api.permissions import IsAdminRole
from accounts.models import User, Role
# from tenant.models import Tenant
from accounts.api.serializers import (
    LoginSerializer,
    UserSerializer,
    UserCreateSerializer,
    AdminSerializer,
    TenantSerializer,
    MallManagerSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all().order_by("fullname")
    lookup_url_kwarg = "user_id"
    pagination_class=UserPaginationView
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer


class AdminList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminSerializer
    queryset= User.objects.filter(role=Role.ADMIN).order_by("fullname")
    

class TenantFilter(filters.FilterSet):
    name=filters.CharFilter(field_name="fullname")
    email=filters.CharFilter(field_name="email")
    created_At=filters.DateFilter(field_name="created_At")

    class Meta:
        model=User
        fields={
            'fullname':['exact'],
            'email':['exact'],
            'created_At':['exact']
        }

class TenantList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = TenantSerializer
    filterset_class=TenantFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_queryset(self):
        queryset = User.objects.filter(
            role=Role.TENANT
        ).order_by("fullname")

        # name = self.request.query_params.get("name")
        # email = self.request.query_params.get("email")
        # created_at = self.request.query_params.get("created_At")
        # updated_at = self.request.query_params.get("updated_at")

        # if name:
        #     queryset = queryset.filter(fullname__icontains=name)

        # if email:
        #     queryset = queryset.filter(email__icontains=email)

        # if created_at:
        #     queryset = queryset.filter(created_At__date=created_at)

        # # if updated_at:
        # #     queryset = queryset.filter(updated_at__date=updated_at)

        return queryset 


class MallManagerList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = MallManagerSerializer
    queryset= User.objects.filter(role=Role.MALL_MANAGER).order_by("fullname")
