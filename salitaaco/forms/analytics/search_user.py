from django import forms

from ..helpers import BaseForm


class SearchUserForm(BaseForm):
    ORDER_BY_CHOICES = [
        ("", "Pinakabagong sign-up"),
        ("date_joined_asc", "Pinakalumang sign-up"),
        ("username_asc", "Username (A-Z)"),
        ("username_desc", "Username (Z-A)"),
        ("last_login_desc", "Pinakahuling login"),
    ]

    query = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Hanapin ang username o pangalan"}),
        label="Hanapin",
    )
    order_by = forms.ChoiceField(
        required=False,
        choices=ORDER_BY_CHOICES,
        widget=forms.Select(attrs={"class": "select"}),
        label="Ayusin",
    )
