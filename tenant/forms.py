from django import forms

from product.models import Product

from .models import RetailUnit


class RetailUnitForm(forms.ModelForm):
    """Tenant only adds retail unit name and chooses the mall they're assigned to."""

    class Meta:
        model = RetailUnit
        fields = ["title", "mall"]
        labels = {
            "title": "Retail unit name / number",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Unit A-12 or Fashion Hub",
                }
            ),
            "mall": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, tenant, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        self.fields["mall"].queryset = tenant.malls.order_by("name")
        self.fields["mall"].empty_label = "Select a mall"
        self.fields["mall"].required = True
        self.fields["title"].required = True

    def clean(self):
        cleaned = super().clean()
        mall = cleaned.get("mall")
        title = cleaned.get("title")
        if mall and title:
            title = title.strip()
            cleaned["title"] = title
            clash = RetailUnit.objects.filter(mall=mall, title__iexact=title)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error("title", f"{mall} already has a unit with this name.")
        return cleaned

    def save(self, commit=True):
        unit = super().save(commit=False)
        unit.tenant = self.tenant
        unit.leased = True
        if commit:
            unit.save()
        return unit


class ProductForm(forms.ModelForm):
    """Products are registered to a retail store (unit), not the tenant."""

    class Meta:
        model = Product
        fields = ["retail_unit", "name", "description", "price", "stock_quantity", "status"]
        widgets = {
            "retail_unit": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "status": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Available"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        self.fields["status"].required = False
        self.fields["description"].required = False
        if tenant is not None:
            self.fields["retail_unit"].queryset = RetailUnit.objects.filter(
                tenant=tenant
            ).select_related("mall").order_by("title")
            self.fields["retail_unit"].empty_label = "Select retail store"
            self.fields["retail_unit"].label = "Retail store"
        self.fields["retail_unit"].required = True


class OfflineSaleForm(forms.Form):
    """Record an in-store sale: customer + product(s) from one retail unit."""

    retail_unit = forms.ModelChoiceField(
        queryset=RetailUnit.objects.none(),
        widget=forms.Select(attrs={"class": "form-select","id": "id_retail_unit",}),
        label="Retail store",
    )
    customer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Customer name"}),
    )
    customer_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={"class": "form-select",     "id": "id_product",}),
        label="Product sold",
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )
    payment_method = forms.ChoiceField(
        choices=[
            ("Cash", "Cash"),
            ("Card", "Card"),
            ("UPI", "UPI"),
            ("Other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        if tenant is not None:
            units = RetailUnit.objects.filter(tenant=tenant).select_related("mall")
            self.fields["retail_unit"].queryset = units.order_by("title")
            # Products for all of tenant's units; JS can filter by unit later
            self.fields["product"].queryset = Product.objects.filter(
                retail_unit__tenant=tenant, stock_quantity__gt=0
            ).select_related("retail_unit").order_by("name")

    def clean(self):
        cleaned = super().clean()
        unit = cleaned.get("retail_unit")
        product = cleaned.get("product")
        qty = cleaned.get("quantity")
        if unit and product and product.retail_unit_id != unit.id:
            self.add_error("product", "This product does not belong to the selected retail store.")
        if product and qty and product.stock_quantity < qty:
            self.add_error("quantity", f"Only {product.stock_quantity} in stock.")
        return cleaned
