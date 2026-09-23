from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from mall.models import Mall
from tenant.models import RetailUnit, Tenant


def make_manager(email="boss@example.com", mall_name="City Mall"):
    user = User.objects.create_user(
        email=email, password="pw12345!", fullname="Manager", role=Role.MALL_MANAGER
    )
    mall = Mall.objects.create(user=user, name=mall_name, floors=3, total_shops=40)
    return user, mall


class RoleTests(TestCase):
    def test_role_is_called_mall_manager(self):
        self.assertEqual(Role.MALL_MANAGER.label, "Mall Manager")
        self.assertEqual(Role.MALL_MANAGER.value, "mall_manager")
        self.assertNotIn("mall", Role.values)

    def test_login_redirects_mall_manager_to_their_dashboard(self):
        make_manager()
        response = self.client.post(
            reverse("accounts:login"), {"email": "boss@example.com", "password": "pw12345!"}
        )
        self.assertRedirects(response, reverse("mall:index"))

    def test_admin_creating_a_mall_manager_user_creates_their_mall(self):
        from django.contrib.admin.sites import site
        from accounts.admin import UserAdmin

        user = User.objects.create_user("new@example.com", "pw12345!", fullname="Grand Mall", role=Role.MALL_MANAGER)
        UserAdmin(User, site).save_model(None, user, None, change=False)
        self.assertEqual(Mall.objects.get(user=user).name, "Grand Mall")


class MallManagerDashboardTests(TestCase):
    def setUp(self):
        self.user, self.mall = make_manager()
        self.client.force_login(self.user)
        self.tenant = Tenant.objects.create(name="Shoe Shop", email="s@example.com")
        self.other_tenant = Tenant.objects.create(name="Book Shop")

    def test_dashboard_shows_mall_tenants_and_units(self):
        self.mall.tenants.add(self.tenant)
        RetailUnit.objects.create(mall=self.mall, tenant=self.tenant, title="Unit Q7")
        response = self.client.get(reverse("mall:index"))
        self.assertContains(response, "City Mall")
        self.assertContains(response, "Shoe Shop")
        self.assertContains(response, "Unit Q7")

    def test_dashboard_only_shows_own_mall(self):
        _, other_mall = make_manager("other@example.com", "Other Mall")
        other_mall.tenants.add(self.other_tenant)
        RetailUnit.objects.create(mall=other_mall, tenant=self.other_tenant, title="Secret Unit")
        response = self.client.get(reverse("mall:index"))
        self.assertNotContains(response, "Secret Unit")
        self.assertNotContains(response, "Other Mall")

    def test_manager_can_assign_a_tenant_to_their_mall(self):
        response = self.client.post(reverse("mall:assign_tenant"), {"tenant": self.tenant.pk})
        self.assertRedirects(response, reverse("mall:index"))
        self.assertIn(self.tenant, self.mall.tenants.all())
        self.assertIn(self.mall, self.tenant.malls.all())

    def test_assigned_tenant_can_then_add_units_in_that_mall(self):
        self.client.post(reverse("mall:assign_tenant"), {"tenant": self.tenant.pk})
        tenant_user = User.objects.create_user("t@example.com", "pw12345!", role=Role.TENANT)
        self.tenant.user = tenant_user
        self.tenant.save()
        self.client.force_login(tenant_user)
        response = self.client.post(
            reverse("tenant:add_retail_unit"), {"title": "New Unit", "mall": self.mall.pk}
        )
        self.assertRedirects(response, reverse("tenant:dashboard"))
        self.assertEqual(RetailUnit.objects.get().mall, self.mall)

    def test_assigning_twice_is_harmless(self):
        for _ in range(2):
            self.client.post(reverse("mall:assign_tenant"), {"tenant": self.tenant.pk})
        self.assertEqual(self.mall.tenants.count(), 1)

    def test_assign_rejects_bad_input(self):
        self.assertRedirects(
            self.client.post(reverse("mall:assign_tenant"), {"tenant": "abc"}), reverse("mall:index")
        )
        self.assertEqual(self.client.post(reverse("mall:assign_tenant"), {"tenant": 9999}).status_code, 404)
        self.assertEqual(self.mall.tenants.count(), 0)

    def test_assign_requires_post(self):
        self.assertEqual(self.client.get(reverse("mall:assign_tenant")).status_code, 405)

    def test_manager_can_remove_a_tenant_without_units(self):
        self.mall.tenants.add(self.tenant)
        self.client.post(reverse("mall:remove_tenant", args=[self.tenant.pk]))
        self.assertEqual(self.mall.tenants.count(), 0)

    def test_cannot_remove_tenant_who_still_has_units(self):
        RetailUnit.objects.create(mall=self.mall, tenant=self.tenant, title="A1")
        response = self.client.post(reverse("mall:remove_tenant", args=[self.tenant.pk]), follow=True)
        self.assertEqual(self.mall.tenants.count(), 1)
        self.assertContains(response, "still has retail units")

    def test_cannot_remove_tenant_from_someone_elses_mall(self):
        _, other_mall = make_manager("other@example.com", "Other Mall")
        other_mall.tenants.add(self.other_tenant)
        response = self.client.post(reverse("mall:remove_tenant", args=[self.other_tenant.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(other_mall.tenants.count(), 1)

    def test_only_mall_managers_get_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("mall:index")).status_code, 302)
        tenant_user = User.objects.create_user("t@example.com", "pw12345!", role=Role.TENANT)
        self.client.force_login(tenant_user)
        self.assertRedirects(self.client.get(reverse("mall:index")), reverse("accounts:login"))
        self.assertRedirects(
            self.client.post(reverse("mall:assign_tenant"), {"tenant": self.tenant.pk}),
            reverse("accounts:login"),
        )
        self.assertEqual(self.mall.tenants.count(), 0)

    def test_manager_without_a_mall_is_sent_back_to_login(self):
        lonely = User.objects.create_user("l@example.com", "pw12345!", role=Role.MALL_MANAGER)
        self.client.force_login(lonely)
        self.assertRedirects(self.client.get(reverse("mall:index")), reverse("accounts:login"))
