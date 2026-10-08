from django import forms

from .helpers import BaseForm
from .validators import name_validator, username_exists, validate_password_strength


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

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Hindi magkatugma ang password at kumpirmasyon.")
        return cleaned_data