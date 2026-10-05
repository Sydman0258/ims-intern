from django.contrib.auth import authenticate, logout
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.permissions import IsAdminRole
from accounts.models import User, Role
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


class UserList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = UserSerializer
    queryset=User.objects.all().order_by("fullname")
    

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)

    #     return Response({
    #         "users": serializer.data
    #     })


class UserDetail(generics.RetrieveAPIView):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_url_kwarg = "user_id"

    

class UserCreate(generics.CreateAPIView):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer




class AdminList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminSerializer

    def get_queryset(self):
        return (
            User.objects
            .filter(role=Role.ADMIN)
            .order_by("fullname")
        )

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)

    #     return Response({
    #         "admins": serializer.data
    #     })


class TenantList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = TenantSerializer

    def get_queryset(self):
        return (
            User.objects
            .filter(role=Role.TENANT)
            .order_by("fullname")
        )

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)

    #     return Response({
    #         "tenants": serializer.data
    #     })


class MallManagerList(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = MallManagerSerializer

    def get_queryset(self):
        return (
            User.objects
            .filter(role=Role.MALL_MANAGER)
            .order_by("fullname")
        )


    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)

    #     return Response({
    #         "mall_managers": serializer.data
    #     })