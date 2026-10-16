from django import forms

from ..helpers import BaseForm


class PurgeUsageForm(BaseForm):
    """How old the per-day usage counts have to be to be deleted."""
    older_than = forms.ChoiceField(
        required=True,
        choices=[
            ("90", "Mas luma sa 90 araw"),
            ("180", "Mas luma sa 180 araw"),
            ("365", "Mas luma sa 1 taon"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={"required": "Pumili kung gaano kaluma.", "invalid_choice": "Pumili mula sa listahan."},
        label="Burahin ang mga bilang kada araw na",
    )

    def days(self):
        return int(self.cleaned_data["older_than"])
