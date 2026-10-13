from django import forms

from ..helpers import BaseForm

ALL = ""
ACTIVE = "active"
INACTIVE = "inactive"


class UserStatusForm(BaseForm):
    """The status tab the list of users is on."""
    status = forms.ChoiceField(
        required=False,
        choices=[(ALL, "Lahat"), (ACTIVE, "Aktibo"), (INACTIVE, "Hindi aktibo")],
        label="Status",
    )

    def chosen(self):
        """The status asked for, or ALL when none or an unknown one was."""
        return (self.cleaned_data.get("status") if self.is_valid() else "") or ALL
