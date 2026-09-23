from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role
from customer.forms import normalize_phone
from customer.models import Customer, CustomerPayment, CustomerPurchase
from customer.services import InsufficientStock, create_purchase
from product.models import Product
from tenant.models import Tenant


class GuestCheckoutTests(TestCase):
    """Customers don't need an account - just a name and a phone number."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Shoe Shop")
        self.product = Product.objects.create(
            retail_unit=None,  # was shop=tenant; now requires RetailUnit name="Sneaker", price=Decimal("100.00"), stock_quantity=5
        )
        self.url = reverse("customer:purchase", args=[self.product.pk])

    def buy(self, **overrides):
        data = {
            "customer_name": "Sita Sharma",
            "customer_phone": "98012 34567",
            "quantity": 2,
            "payment_method": "Cash",
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_shop_and_purchase_page_need_no_login(self):
        self.assertEqual(self.client.get(reverse("customer:index")).status_code, 200)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your name")
        self.assertContains(response, "Phone number")

    def test_purchase_needs_only_name_and_phone(self):
        response = self.buy()
        purchase = CustomerPurchase.objects.get()
        self.assertRedirects(
            response, reverse("customer:purchase_detail", args=[purchase.pk])
        )
        self.assertEqual(purchase.customer.name, "Sita Sharma")
        self.assertEqual(purchase.customer.phone, "9801234567")  # spaces stripped
        self.assertEqual(purchase.total_amount, Decimal("200.00"))
        self.assertTrue(purchase.full_paid)
        self.assertEqual(CustomerPayment.objects.get().payment_status, "Completed")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_no_user_account_is_created(self):
        from accounts.models import User

        self.buy()
        self.assertEqual(User.objects.count(), 0)

    def test_name_is_required(self):
        response = self.buy(customer_name="   ")
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "customer_name", "This field is required.")
        self.assertEqual(CustomerPurchase.objects.count(), 0)

    def test_phone_is_required(self):
        response = self.buy(customer_phone="")
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "customer_phone", "This field is required.")
        self.assertEqual(CustomerPurchase.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_invalid_phone_rejected(self):
        for bad in ["abc", "12", "98-abc-1234", "1" * 20]:
            response = self.buy(customer_phone=bad)
            self.assertEqual(response.status_code, 200, bad)
            self.assertIn("customer_phone", response.context["form"].errors, bad)
        self.assertEqual(CustomerPurchase.objects.count(), 0)

    def test_form_keeps_typed_values_on_error(self):
        response = self.buy(customer_phone="nope")
        self.assertContains(response, 'value="Sita Sharma"')

    def test_same_name_and_phone_reuses_customer(self):
        self.buy()
        self.buy(customer_name="sita sharma", customer_phone="9801-234-567")
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(CustomerPurchase.objects.count(), 2)

    def test_different_name_same_phone_is_a_different_customer(self):
        self.buy()
        self.buy(customer_name="Ram Sharma")
        self.assertEqual(Customer.objects.count(), 2)

    def test_cannot_buy_more_than_stock(self):
        response = self.buy(quantity=6)
        self.assertEqual(response.status_code, 200)
        self.assertIn("quantity", response.context["form"].errors)
        self.assertEqual(CustomerPurchase.objects.count(), 0)

    def test_service_rejects_insufficient_stock(self):
        with self.assertRaises(InsufficientStock):
            create_purchase(
                name="A", phone="9800000000", product_id=self.product.pk,
                quantity=99, payment_method="Cash",
            )
        self.assertEqual(Customer.objects.count(), 0)  # rolled back / never created

    def test_out_of_stock_product_shows_message(self):
        self.product.stock_quantity = 0
        self.product.save()
        self.assertContains(self.client.get(self.url), "out of stock")
        # and it's not listed in the shop
        self.assertNotContains(self.client.get(reverse("customer:index")), "Sneaker")

    def test_receipt_only_visible_in_purchasing_session(self):
        self.buy()
        purchase = CustomerPurchase.objects.get()
        receipt = reverse("customer:purchase_detail", args=[purchase.pk])

        mine = self.client.get(receipt)
        self.assertContains(mine, "Sita Sharma")
        self.assertContains(mine, "9801234567")

        stranger = Client()  # a different browser: no session
        response = stranger.get(receipt)
        self.assertRedirects(response, reverse("customer:index"))

    def test_shop_tenant_filter_ignores_garbage(self):
        response = self.client.get(reverse("customer:index"), {"tenant": "abc"})
        self.assertEqual(response.status_code, 200)

    def test_no_customer_role_exists(self):
        self.assertNotIn("customer", Role.values)


class PhoneNormalizationTests(TestCase):
    def test_strips_separators_and_keeps_plus(self):
        self.assertEqual(normalize_phone(" +977 (98) 1234-5678 "), "+9779812345678")
        self.assertEqual(normalize_phone("98.01.23.45.67"), "9801234567")

    def test_rejects_letters_and_bad_lengths(self):
        for bad in ["", "abc1234567", "123456", "1" * 16]:
            with self.assertRaises(ValidationError, msg=bad):
                normalize_phone(bad)
