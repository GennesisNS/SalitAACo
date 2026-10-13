from django import forms

from ..helpers import BaseForm


class InstitutionForm(BaseForm):
    """A school or centre and what was agreed with it. Used to add one and to change one."""
    name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. SPED Center ng Barangay"}),
        error_messages={"required": "Ilagay ang pangalan ng institusyon."},
        label="Pangalan ng institusyon",
    )
    contact_person = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={"class": "input"}),
        label="Taong kausap (opsiyonal)",
    )
    contact_details = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "telepono o email"}),
        label="Paano makakausap (opsiyonal)",
    )
    seats = forms.IntegerField(
        required=True,
        min_value=0,
        max_value=100000,
        widget=forms.NumberInput(attrs={"class": "input", "min": 0}),
        error_messages={
            "required": "Ilagay kung ilang bata ang sakop.",
            "invalid": "Hindi tama ang bilang.",
            "min_value": "Hindi tama ang bilang.",
            "max_value": "Hindi tama ang bilang.",
        },
        label="Bilang ng batang sakop",
    )
    plan_notes = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. napagkasunduang presyo kada taon"}),
        label="Napagkasunduang plano (opsiyonal)",
    )
    renewal_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
        error_messages={"invalid": "Hindi tama ang petsa."},
        label="Petsa ng renewal (opsiyonal)",
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Aktibo ang institusyon",
    )
