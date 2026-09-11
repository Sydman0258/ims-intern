from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    TENANT = "tenant", "tenant"
    CUSTOMER = "customer", "Customer"
    MALL="mall","Mall"


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email,
            password,
            **extra_fields
        )

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    fullname = models.CharField(max_length=250)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CUSTOMER
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore

    def __str__(self):
        return self.email



class AdminManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.ADMIN)


class tenantManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.TENANT)


class CustomerManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.CUSTOMER)

class MallManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.MALL)
    


class Admin(User):
    objects = AdminManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.role = Role.ADMIN
        super().save(*args, **kwargs)


class tenant(User):
    objects = tenantManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.role = Role.TENANT
        self.is_tenant = True
        super().save(*args, **kwargs)


class Customer(User):
    objects = CustomerManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.role = Role.CUSTOMER
        super().save(*args, **kwargs)

class Mall(User):
    objects=MallManager()

    class Meta:
        proxy = True

    def save(self,*args,**kwargs):
        self.role=Role.MALL
        super().save(*args,**kwargs)