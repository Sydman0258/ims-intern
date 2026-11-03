from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from mall.models import Mall
from tenant.models import RetailUnit, Tenant


def make_mall(name="City Mall"):
    return Mall.objects.create(name=name, floors=3, total_shops=40)


def make_tenant(email="shoes@example.com", name="Shoe Shop", malls=()):
    user = User.objects.create_user(
        email=email, password="pw12345!", fullname=name, role=Role.TENANT
    )
    tenant = Tenant.objects.create(user=user, name=name, email=email)
    tenant.malls.set(malls)
    return user, tenant


class TenantAddRetailUnitViewTests(TestCase):
    """
    Retail units are assigned by the mall manager.
    AddRetailUnitView only informs the tenant and redirects to the dashboard.
    """

    def setUp(self):
        self.mall = make_mall("City Mall")
        self.user, self.tenant = make_tenant(malls=[self.mall])
        self.client.force_login(self.user)
        self.url = reverse("tenant:add_retail_unit")

    def test_get_redirects_to_dashboard(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("tenant:dashboard"))

    def test_post_does_not_create_unit(self):
        # View only implements GET; POST may be 405 or also redirect
        response = self.client.post(
            self.url,
            {"title": "Unit A-12", "mall": self.mall.pk},
        )
        self.assertIn(response.status_code, [302, 405])
        self.assertEqual(RetailUnit.objects.count(), 0)

    def test_dashboard_lists_units_and_malls(self):
        RetailUnit.objects.create(mall=self.mall, tenant=self.tenant, title="Unit Z9")
        response = self.client.get(reverse("tenant:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unit Z9")
        self.assertContains(response, "City Mall")
        # UI no longer has "Add Retail Unit"; products are added instead
        self.assertContains(response, "Add product")

    def test_anonymous_cannot_use_add_retail_unit(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_tenant_role_blocked(self):
        manager = User.objects.create_user(
            "m@example.com", "pw12345!", fullname="Mgr", role=Role.MALL_MANAGER
        )
        self.client.force_login(manager)
        response = self.client.get(self.url)
        # Mixin may redirect to login or return 403
        self.assertIn(response.status_code, [302, 403])


class RetailUnitModelTests(TestCase):
    def test_creating_a_unit_assigns_the_tenant_to_the_mall(self):
        # e.g. an admin creating a unit directly
        mall = make_mall()
        _, tenant = make_tenant()
        self.assertFalse(tenant.malls.exists())
        RetailUnit.objects.create(mall=mall, tenant=tenant, title="B2")
        self.assertEqual(list(tenant.malls.all()), [mall])
        self.assertEqual(list(mall.tenants.all()), [tenant])


# ---------------------------------------------------------------------------
# Extra model + API coverage
# ---------------------------------------------------------------------------

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from product.models import Product
from tenant.models import LeasePayment


class TenantModelTests(TestCase):
    def test_create_tenant_str(self):
        _, tenant = make_tenant(email="model@tenant.test", name="Model Shop")
        self.assertEqual(str(tenant), "Model Shop")
        self.assertIsNotNone(tenant.created_at)

    def test_tenant_email_unique_when_set(self):
        make_tenant(email="unique@tenant.test", name="One")
        with self.assertRaises(Exception):
            Tenant.objects.create(name="Two", email="unique@tenant.test")


class RetailUnitLeaseTests(TestCase):
    def setUp(self):
        self.mall = make_mall("Lease Mall")
        self.user, self.tenant = make_tenant(malls=[self.mall])
        self.unit = RetailUnit.objects.create(
            mall=self.mall,
            tenant=self.tenant,
            title="Lease Unit",
            leased=True,
            leased_date=date(2025, 1, 1),
            leased_tenure=12,
            renewal_date=timezone.localdate() + timedelta(days=60),
            monthly_rent=Decimal("20000.00"),
            status="Active",
        )

    def test_is_lease_expired(self):
        self.unit.renewal_date = timezone.localdate() - timedelta(days=1)
        self.unit.save()
        self.assertTrue(self.unit.is_lease_expired)

    def test_lease_status_not_leased(self):
        self.unit.leased = False
        self.unit.save()
        self.assertEqual(self.unit.lease_status_label, "Not leased")

    def test_lease_payment_create(self):
        payment = LeasePayment.objects.create(
            retail_unit=self.unit,
            amount=Decimal("20000.00"),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            status="paid",
            paid_on=date(2026, 1, 5),
        )
        self.assertEqual(self.unit.lease_payments.count(), 1)
        self.assertIn("Lease payment", str(payment))


class TenantAPITests(APITestCase):
    def setUp(self):
        self.mall = make_mall("API Mall")
        self.user, self.tenant = make_tenant(
            email="api-tenant@test.com", name="API Shop", malls=[self.mall]
        )
        self.unit = RetailUnit.objects.create(
            mall=self.mall, tenant=self.tenant, title="API Unit", leased=True
        )
        self.product = Product.objects.create(
            retail_unit=self.unit,
            name="API Product",
            price=Decimal("500.00"),
            stock_quantity=15,
        )
        self.admin = User.objects.create_user(
            email="admin-tenant-api@test.com",
            password="AdminPass123!",
            fullname="Admin",
            role=Role.ADMIN,
            is_staff=True,
        )

    def test_dashboard_requires_auth(self):
        response = self.client.get("/api/tenant/dashboard/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_tenant_dashboard_ok(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/tenant/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tenant", response.data)
        self.assertIn("products", response.data)
        self.assertIn("retail_units", response.data)

    def test_non_tenant_dashboard_forbidden(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/tenant/dashboard/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_products_list_as_tenant(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/tenant/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_products_list_unauthenticated(self):
        response = self.client.get("/api/tenant/products/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_product_detail_as_tenant(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/tenant/products/{self.product.pk}/")
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND],
        )

    def test_add_retail_unit_api_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/tenant/retail-units/add/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("has_retail_unit", response.data)
