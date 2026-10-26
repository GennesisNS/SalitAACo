from django import forms

from ..helpers import BaseForm

GROWTH = "growth"
USAGE = "usage"
RETENTION = "retention"
BUSINESS = "business"


class ReportTabForm(BaseForm):
    """The tab the Analytics at Ulat page is on. Reports to download are on Mga Ulat."""
    tab = forms.ChoiceField(
        required=False,
        choices=[
            (GROWTH, "Paglago ng user"),
            (USAGE, "Paggamit"),
            (RETENTION, "Pagbabalik"),
            (BUSINESS, "Negosyo"),
        ],
        label="Tab",
    )

    def chosen(self):
        """The tab asked for, or the first one when none or an unknown one was."""
        return (self.cleaned_data.get("tab") if self.is_valid() else "") or GROWTH
