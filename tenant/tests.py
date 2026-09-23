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


class TenantAddsRetailUnitTests(TestCase):
    def setUp(self):
        self.mall = make_mall("City Mall")
        self.other_mall = make_mall("Other Mall")
        self.user, self.tenant = make_tenant(malls=[self.mall])
        self.client.force_login(self.user)
        self.url = reverse("tenant:add_retail_unit")

    def test_form_only_offers_assigned_malls(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["form"].fields["mall"].queryset), [self.mall])

    def test_tenant_can_add_a_retail_unit(self):
        response = self.client.post(
            self.url,
            {"title": "Unit A-12", "mall": self.mall.pk, "leased": "on",
             "leased_date": "2026-01-01", "leased_tenure": 12, "renewal_date": "2027-01-01",
             "status": "Open"},
        )
        self.assertRedirects(response, reverse("tenant:dashboard"))
        unit = RetailUnit.objects.get()
        self.assertEqual((unit.tenant, unit.mall, unit.title), (self.tenant, self.mall, "Unit A-12"))
        self.assertTrue(unit.leased)
        self.assertEqual(unit.leased_tenure, 12)

    def test_only_title_and_mall_are_required(self):
        self.client.post(self.url, {"title": "Kiosk 1", "mall": self.mall.pk})
        unit = RetailUnit.objects.get()
        self.assertFalse(unit.leased)

    def test_cannot_add_unit_in_a_mall_not_assigned(self):
        response = self.client.post(self.url, {"title": "Sneaky", "mall": self.other_mall.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("mall", response.context["form"].errors)
        self.assertEqual(RetailUnit.objects.count(), 0)
        self.assertFalse(self.tenant.malls.filter(pk=self.other_mall.pk).exists())

    def test_unit_name_must_be_unique_within_a_mall(self):
        _, other = make_tenant("other@example.com", "Other Tenant", malls=[self.mall])
        RetailUnit.objects.create(mall=self.mall, tenant=other, title="A1")
        response = self.client.post(self.url, {"title": "a1", "mall": self.mall.pk})
        self.assertIn("title", response.context["form"].errors)
        self.assertEqual(RetailUnit.objects.count(), 1)

    def test_renewal_cannot_precede_lease_start(self):
        response = self.client.post(
            self.url,
            {"title": "X", "mall": self.mall.pk,
             "leased_date": "2026-06-01", "renewal_date": "2026-01-01"},
        )
        self.assertIn("renewal_date", response.context["form"].errors)

    def test_tenant_without_a_mall_sees_explanation_not_form(self):
        user, _ = make_tenant("new@example.com", "New Tenant")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "not assigned to a mall yet")
        self.assertNotContains(response, 'name="title"')

    def test_dashboard_lists_units_and_malls(self):
        RetailUnit.objects.create(mall=self.mall, tenant=self.tenant, title="Unit Z9")
        response = self.client.get(reverse("tenant:dashboard"))
        self.assertContains(response, "Unit Z9")
        self.assertContains(response, "City Mall")
        self.assertContains(response, "Add Retail Unit")

    def test_other_roles_and_anonymous_cannot_use_the_page(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)  # -> login
        manager = User.objects.create_user("m@example.com", "pw12345!", role=Role.MALL_MANAGER)
        self.client.force_login(manager)
        self.assertRedirects(self.client.get(self.url), reverse("accounts:login"))


class RetailUnitModelTests(TestCase):
    def test_creating_a_unit_assigns_the_tenant_to_the_mall(self):
        # e.g. an admin creating a unit directly
        mall = make_mall()
        _, tenant = make_tenant()
        self.assertFalse(tenant.malls.exists())
        RetailUnit.objects.create(mall=mall, tenant=tenant, title="B2")
        self.assertEqual(list(tenant.malls.all()), [mall])
        self.assertEqual(list(mall.tenants.all()), [tenant])
