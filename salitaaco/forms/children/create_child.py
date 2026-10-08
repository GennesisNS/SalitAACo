from django import forms

from ..helpers import BaseForm
from ..validators import name_validator, username_exists, validate_password_strength


class CreateChildForm(BaseForm):
    display_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Miguel"}),
        error_messages={"required": "Ilagay ang pangalan ng bata."},
        label="Pangalan ng bata",
        validators=[name_validator],
    )
    username = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "off", "placeholder": "username"}),
        error_messages={"required": "Ilagay ang username ng bata."},
        label="Username ng bata",
        help_text="Ito ang gagamitin ng bata sa pag-log in.",
        validators=[username_exists],
    )
    age = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={"class": "input", "min": 0, "max": 150, "placeholder": "hal. 7"}),
        error_messages={
            "invalid": "Hindi tama ang edad.",
            "min_value": "Hindi tama ang edad.",
            "max_value": "Hindi tama ang edad.",
        },
        label="Edad (opsiyonal)",
    )
    password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        label="Password ng bata",
        help_text="Hindi bababa sa 8 character, may malaki at maliit na titik, numero, at espesyal na character (hal. ! @ # $).",
        validators=[validate_password_strength],
    )
    confirm_password = forms.CharField(
        required=True,
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        error_messages={"required": "Hindi magkatugma ang password at kumpirmasyon."},
        label="Kumpirmahin ang Password",
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Hindi magkatugma ang password at kumpirmasyon.")
        return cleaned_data
