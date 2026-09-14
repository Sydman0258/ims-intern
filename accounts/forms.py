from django import forms
from django.contrib.auth import authenticate


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autofocus": True, "class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(
                self.request, username=email, password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid email or password", code="invalid_login"
                )
        return cleaned_data

    def get_user(self):
        return self.user_cache