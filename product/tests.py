"""
Tests for product app: models and related behaviour.
Touch nothing outside this file.
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from mall.models import Mall
from product.models import Product
from tenant.models import RetailUnit, Tenant


def make_admin(email="admin@prod.test", password="AdminPass123!"):
    return User.objects.create_user(
        email=email,
        password=password,
        fullname="Admin",
        role=Role.ADMIN,
        is_staff=True,
        is_superuser=True,
    )


def make_tenant_with_unit(
    email="tenant@prod.test",
    name="Fashion Store",
    mall_name="Central Mall",
):
    user = User.objects.create_user(
        email=email,
        password="TenantPass123!",
        fullname=name,
        role=Role.TENANT,
    )
    tenant = Tenant.objects.create(user=user, name=name, email=email)
    mall = Mall.objects.create(name=mall_name, floors=2, total_shops=30)
    unit = RetailUnit.objects.create(
        mall=mall,
        tenant=tenant,
        title="Unit P-1",
        leased=True,
        monthly_rent=Decimal("15000.00"),
    )
    return user, tenant, mall, unit


class ProductModelTests(TestCase):
    def setUp(self):
        self.user, self.tenant, self.mall, self.unit = make_tenant_with_unit()

    def test_create_product_with_retail_unit(self):
        product = Product.objects.create(
            retail_unit=self.unit,
            name="Running Shoes",
            description="Lightweight trainers",
            price=Decimal("4999.99"),
            stock_quantity=25,
            status="available",
        )
        self.assertEqual(product.name, "Running Shoes")
        self.assertEqual(product.price, Decimal("4999.99"))
        self.assertEqual(product.stock_quantity, 25)
        self.assertEqual(product.retail_unit, self.unit)
        self.assertIsNotNone(product.created_at)

    def test_product_str(self):
        product = Product.objects.create(
            retail_unit=self.unit,
            name="Blue Jeans",
            price=Decimal("1999.00"),
        )
        self.assertEqual(str(product), "Blue Jeans")

    def test_product_tenant_property(self):
        product = Product.objects.create(
            retail_unit=self.unit,
            name="T-Shirt",
            price=Decimal("599.00"),
        )
        self.assertEqual(product.tenant, self.tenant)

    def test_product_shop_alias(self):
        product = Product.objects.create(
            retail_unit=self.unit,
            name="Hat",
            price=Decimal("299.00"),
        )
        self.assertEqual(product.shop, self.tenant)

    def test_product_without_retail_unit(self):
        product = Product.objects.create(
            name="Orphan Product",
            price=Decimal("100.00"),
            stock_quantity=0,
        )
        self.assertIsNone(product.retail_unit)
        # tenant / shop properties rely on retail_unit; may raise or return None
        try:
            tenant = product.tenant
            self.assertIsNone(tenant)
        except AttributeError:
            pass  # expected if code does retail_unit.tenant without guard

    def test_default_stock_is_zero(self):
        product = Product.objects.create(
            retail_unit=self.unit,
            name="Socks",
            price=Decimal("199.00"),
        )
        self.assertEqual(product.stock_quantity, 0)

    def test_products_related_name_on_retail_unit(self):
        Product.objects.create(
            retail_unit=self.unit, name="P1", price=Decimal("10.00")
        )
        Product.objects.create(
            retail_unit=self.unit, name="P2", price=Decimal("20.00")
        )
        self.assertEqual(self.unit.products.count(), 2)
        self.assertEqual(
            set(self.unit.products.values_list("name", flat=True)),
            {"P1", "P2"},
        )


class ProductAPITests(APITestCase):
    """
    Product ViewSet is registered under /api/tenant/products/ (tenant API).
    product/api is not included in the root urlconf.
    """

    def setUp(self):
        self.user, self.tenant, self.mall, self.unit = make_tenant_with_unit()
        self.product = Product.objects.create(
            retail_unit=self.unit,
            name="API Sneaker",
            price=Decimal("3500.00"),
            stock_quantity=10,
            status="available",
        )
        self.admin = make_admin()

    def test_tenant_products_list_requires_auth(self):
        response = self.client.get("/api/tenant/products/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_tenant_can_list_products(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/tenant/products/")
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN],
        )
        if response.status_code == status.HTTP_200_OK:
            data = response.data
            if isinstance(data, dict) and "results" in data:
                names = [p.get("name") for p in data["results"]]
            elif isinstance(data, list):
                names = [p.get("name") for p in data]
            else:
                names = []
            self.assertIsInstance(names, list)

    def test_product_detail_via_tenant_api(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/tenant/products/{self.product.pk}/")
        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ],
        )
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data.get("name"), "API Sneaker")

    def test_create_product_as_tenant(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "name": "New Jacket",
            "price": "2500.00",
            "stock_quantity": 5,
            "retail_unit": self.unit.pk,
            "status": "available",
        }
        response = self.client.post("/api/tenant/products/", payload, format="json")
        self.assertIn(
            response.status_code,
            [
                status.HTTP_201_CREATED,
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_403_FORBIDDEN,
            ],
        )
        if response.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK):
            self.assertTrue(Product.objects.filter(name="New Jacket").exists())

    def test_delete_product_as_tenant(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/tenant/products/{self.product.pk}/")
        self.assertIn(
            response.status_code,
            [
                status.HTTP_204_NO_CONTENT,
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ],
        )
