from django import forms

from .helpers import BaseForm
from .validators import (
    MIN_GUARDIAN_AGE,
    email_exists,
    name_validator,
    username_exists,
    validate_password_strength,
    validate_username,
)


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
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Maria Santos"}),
        error_messages={"required": "Ilagay ang pangalan mo."},
        label="Pangalan mo (magulang / tagapag-alaga)",
        validators=[name_validator]
    )
    email = forms.EmailField(
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "input", "autocomplete": "email", "placeholder": "hal. maria@email.com"}),
        error_messages={
            "required": "Ilagay ang email mo.",
            "invalid": "Hindi tama ang email address.",
        },
        label="Email",
        validators=[email_exists],
    )
    age = forms.IntegerField(
        required=True,
        min_value=MIN_GUARDIAN_AGE,
        max_value=120,
        widget=forms.NumberInput(attrs={"class": "input", "min": MIN_GUARDIAN_AGE, "max": 120, "placeholder": "hal. 35"}),
        error_messages={
            "required": "Ilagay ang edad mo.",
            "invalid": "Hindi tama ang edad.",
            "min_value": f"{MIN_GUARDIAN_AGE} taong gulang pataas lang ang puwedeng gumawa ng account.",
            "max_value": "Hindi tama ang edad.",
        },
        label="Edad mo",
    )
    username = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "username", "placeholder": "username"}),
        error_messages={"required": "Ilagay ang username."},
        label="Username",
        validators=[validate_username, username_exists],
    )
    password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        label="Password",
        help_text="Hindi bababa sa 8 character, may malaki at maliit na titik, numero, at espesyal na character (hal. ! @ # $).",
        validators=[validate_password_strength],
    )
    confirm_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        error_messages={"required": "Hindi magkatugma ang bagong password at kumpirmasyon."},
        label="Kumpirmahin ang Password",
    )
    privacy_consent = forms.BooleanField(
        required=True,
        error_messages={"required": "Kailangang sumang-ayon sa Paalala sa Privacy para makagawa ng account."},
        # auth/register.html writes this label itself, with the notice's name as the button that opens it.
        label="Sumasang-ayon ako sa Paalala sa Privacy.",
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Hindi magkatugma ang password at kumpirmasyon.")
        return cleaned_data