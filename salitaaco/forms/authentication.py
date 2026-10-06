from django import forms

from .helpers import BaseForm
from .validators import username_exists

MIN_PASSWORD_LENGTH = 4


class LoginForm(BaseForm):
    username = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "username", "placeholder": "username"}),
        error_messages={"required": "Ilagay ang username."},
        label="Username",
    )
    password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password", "placeholder": "••••••••"}),
        error_messages={"required": "Ilagay ang password."},
        label="Password",
    )


class RegisterForm(BaseForm):
    display_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Miguel"}),
        error_messages={"required": "Ilagay ang pangalan ng bata / user."},
        label="Pangalan ng bata / user",
    )
    username = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "username", "placeholder": "username"}),
        error_messages={"required": "Ilagay ang username."},
        label="Username",
        validators=[username_exists],
    )
    password = forms.CharField(
        required=True,
        strip=False,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password", "placeholder": "min. 4 characters"}),
        error_messages={
            "required": "Ang password ay dapat may hindi bababa sa 4 na character.",
            "min_length": "Ang password ay dapat may hindi bababa sa 4 na character.",
        },
        label="Password",
    )
