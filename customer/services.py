from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from product.models import Product

from .models import Customer, CustomerPayment, CustomerPurchase, CustomerPurchaseItem


class InsufficientStock(Exception):
    def __init__(self, available):
        self.available = available
        super().__init__(f"Only {available} unit(s) available in stock.")


def get_or_create_customer(name, phone):
    """Find the customer with this name + phone, or create one."""
    customer = Customer.objects.filter(phone=phone, name__iexact=name).first()
    if customer is None:
        customer = Customer.objects.create(name=name, phone=phone)
    return customer


def create_offline_purchase(
    *,
    tenant,
    retail_unit,
    name,
    phone,
    items,
    payment_method="Cash",
):
    """
    Record an in-store (offline) sale for a retail unit.

    items: list of dicts with keys product_id, quantity
    Raises InsufficientStock if any product doesn't have enough stock.
    """
    with transaction.atomic():
        customer = get_or_create_customer(name, phone)
        now = timezone.now()
        purchase = CustomerPurchase.objects.create(
            customer=customer,
            tenant=tenant,
            retail_unit=retail_unit,
            purchase_date=now,
            total_amount=Decimal("0"),
            full_paid=True,
            is_offline=True,
        )

        total = Decimal("0")
        for item in items:
            product = (
                Product.objects.select_for_update()
                .select_related("retail_unit")
                .get(pk=item["product_id"], retail_unit=retail_unit)
            )
            qty = int(item["quantity"])
            if product.stock_quantity < qty:
                raise InsufficientStock(product.stock_quantity)

            unit_price = product.price
            line_total = unit_price * Decimal(qty)
            CustomerPurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                total_price=line_total,
            )
            product.stock_quantity -= qty
            product.save(update_fields=["stock_quantity", "updated_at"])
            total += line_total

        purchase.total_amount = total
        purchase.save(update_fields=["total_amount", "updated_at"])

        CustomerPayment.objects.create(
            purchase=purchase,
            amount=total,
            payment_method=payment_method,
            payment_status="Completed",
            payment_date=now,
            transaction_reference=f"MallMS-{purchase.pk}-{now.strftime('%Y%m%d%H%M%S')}",
        )

    return purchase
