from django import forms

from salitaaco.defaults.plans import PAYMENT_STATUSES

from ..helpers import BaseForm

ALL_STATUSES = ""


class TransactionStatusForm(BaseForm):
    """The status tab the list of payments is on."""
    status = forms.ChoiceField(
        required=False,
        choices=[(ALL_STATUSES, "Lahat")] + PAYMENT_STATUSES,
        label="Status",
    )

    def chosen(self):
        """The status asked for, or ALL_STATUSES when none or an unknown one was."""
        return (self.cleaned_data.get("status") if self.is_valid() else "") or ALL_STATUSES
