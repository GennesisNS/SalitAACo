from django import forms

from ..helpers import BaseForm


class RejectPaymentForm(BaseForm):
    """Why an admin rejects a payment. The guardian sees it in their payment history."""
    # Which payment, from the dialog it was sent from.
    payment = forms.UUIDField(
        required=True,
        widget=forms.HiddenInput(),
        error_messages={"required": "Walang bayad na pinili.", "invalid": "Walang bayad na pinili."},
    )
    note = forms.CharField(
        required=True,
        max_length=300,
        widget=forms.Textarea(attrs={
            "class": "textarea",
            "rows": 3,
            "placeholder": "hal. Malabo ang larawan ng bayad. Pakisubukan muli.",
        }),
        error_messages={
            "required": "Ilagay kung bakit tinanggihan ang bayad.",
            "max_length": "Masyadong mahaba ang dahilan (hanggang 300 character).",
        },
        label="Dahilan, makikita ng tagapag-alaga",
    )
