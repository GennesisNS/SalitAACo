from django import forms

from ..helpers import BaseForm

SIGNUPS = "signups"
USAGE = "usage"
WORDS = "words"


class ExportReportForm(BaseForm):
    """Which report to download as a CSV file, and for which days."""
    report = forms.ChoiceField(
        required=True,
        choices=[
            (SIGNUPS, "Mga sign-up kada araw"),
            (USAGE, "Paggamit kada araw (mga pindot at bukas ng board)"),
            (WORDS, "Mga salita at kung ilang beses pinindot"),
        ],
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={"required": "Pumili ng ulat.", "invalid_choice": "Pumili ng ulat mula sa listahan."},
        label="Ulat",
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
        error_messages={"invalid": "Hindi tama ang petsa."},
        label="Mula (opsiyonal)",
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
        error_messages={"invalid": "Hindi tama ang petsa."},
        label="Hanggang (opsiyonal)",
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from, date_to = cleaned_data.get("date_from"), cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "Dapat hindi mas maaga ang “Hanggang” kaysa sa “Mula”.")
        return cleaned_data
