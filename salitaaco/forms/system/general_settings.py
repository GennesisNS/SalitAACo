from django import forms

from ..helpers import BaseForm
from ..validators import validate_phone_number


class GeneralSettingsForm(BaseForm):
    """How guardians reach the people who run the app, and the switch that closes the app for maintenance."""
    contact_email = forms.EmailField(
        required=False,
        max_length=254,
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "hal. tulong@halimbawa.ph"}),
        error_messages={"invalid": "Hindi tama ang email address."},
        label="Email ng suporta (opsiyonal)",
    )
    contact_phone = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. 0917 000 0000", "inputmode": "tel"}),
        label="Telepono ng suporta (opsiyonal)",
        validators=[validate_phone_number],
    )
    maintenance_mode = forms.BooleanField(
        required=False,
        label="Maintenance mode",
    )
    maintenance_message = forms.CharField(
        required=False,
        max_length=300,
        widget=forms.Textarea(attrs={
            "class": "textarea",
            "rows": 2,
            "placeholder": "hal. Inaayos namin ang app. Babalik ito mamayang 6:00 ng gabi.",
        }),
        error_messages={"max_length": "Masyadong mahaba ang mensahe (hanggang 300 character)."},
        label="Mensahe habang naka-maintenance (opsiyonal)",
    )
