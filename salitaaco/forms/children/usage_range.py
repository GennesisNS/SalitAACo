from django import forms

from ..helpers import BaseForm

ALL_DAYS = "all"
DEFAULT_RANGE = "7"


class UsageRangeForm(BaseForm):
    """The stretch of days a child's usage page counts."""
    range = forms.ChoiceField(
        required=False,
        choices=[
            ("7", "Huling 7 araw"),
            ("30", "Huling 30 araw"),
            (ALL_DAYS, "Lahat"),
        ],
        label="Saklaw ng petsa",
    )

    def days(self):
        """The number of days chosen, or None for every day. An unreadable choice counts as the usual one."""
        chosen = (self.cleaned_data.get("range") if self.is_valid() else "") or DEFAULT_RANGE
        return None if chosen == ALL_DAYS else int(chosen)

    def chosen(self):
        days = self.days()
        return ALL_DAYS if days is None else str(days)
