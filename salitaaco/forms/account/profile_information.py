from django import forms

from ..helpers import BaseForm


class ProfileInformationForm(BaseForm):
    display_name = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. Miguel"}),
        error_messages={"required": "Ilagay ang pangalan."},
        label="Pangalan (Display Name)",
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
