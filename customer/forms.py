import re

from django import forms
from django.core.exceptions import ValidationError

PAYMENT_METHODS = [
    ("Cash", "Cash"),
    ("Card", "Card"),
    ("UPI", "UPI"),
    ("Online", "Online Transfer"),
]


def normalize_phone(raw):
    """Return the phone number with spaces/dashes/brackets stripped.

    A leading "+" is kept. Raises ValidationError if it doesn't look like a
    phone number (7-15 digits, nothing but digits and common separators).
    """
    raw = (raw or "").strip()
    if re.search(r"[^\d\s\-\+\(\)\.]", raw):
        raise ValidationError("Enter a valid phone number.")
    digits = re.sub(r"\D", "", raw)
    if not 7 <= len(digits) <= 15:
        raise ValidationError("Enter a valid phone number (7 to 15 digits).")
    return ("+" if raw.startswith("+") else "") + digits


class PurchaseForm(forms.Form):
    """Guest checkout: the customer only has to give a name and phone number."""

    customer_name = forms.CharField(
        label="Your name",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    customer_phone = forms.CharField(
        label="Phone number",
        max_length=20,
        widget=forms.TextInput(
            attrs={"class": "form-control", "type": "tel", "autocomplete": "tel"}
        ),
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        initial="Cash",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if product is not None:
            self.fields["quantity"].widget.attrs["max"] = product.stock_quantity

    def clean_customer_name(self):
        name = self.cleaned_data["customer_name"].strip()
        if not name:
            raise ValidationError("Please enter your name.")
        return name

    def clean_customer_phone(self):
        return normalize_phone(self.cleaned_data["customer_phone"])

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if self.product is not None and quantity > self.product.stock_quantity:
            raise ValidationError(
                f"Only {self.product.stock_quantity} unit(s) available in stock."
            )
        return quantity
