from django import forms

from ..authentication import RegisterForm
from ..validators import name_validator


class AddAdminForm(RegisterForm):
    """
    A new admin account: a name, a username no account has, and a password, as
    signing up asks for. An admin is never made from an existing account.
    """
    display_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Juan Dela Cruz"}),
        error_messages={"required": "Ilagay ang pangalan ng admin."},
        label="Pangalan ng admin",
        validators=[name_validator],
    )
