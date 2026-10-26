from django import forms

from salitaaco.defaults.reports import CSV, FILE_TYPES

from ..helpers import BaseForm


def columns_field(choices, label):
    """The columns of one of a report's detail tables, every one chosen to begin with."""
    return forms.MultipleChoiceField(
        required=True,
        choices=choices,
        initial=[value for value, _ in choices],
        widget=forms.CheckboxSelectMultiple(),
        error_messages={"required": "Pumili kahit isang column."},
        label=label,
    )


class ReportForm(BaseForm):
    """
    What every report on Mga Ulat asks for: the file to make it as, and the
    days it covers, both counted. Each kind of report adds the columns of its
    detail tables.
    """
    file_type = forms.ChoiceField(
        required=True,
        choices=FILE_TYPES,
        initial=CSV,
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={"required": "Pumili ng uri ng file."},
        label="Uri ng file",
    )
    start_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
        error_messages={"required": "Ilagay ang petsa ng simula.", "invalid": "Hindi tama ang petsa."},
        label="Mula",
    )
    end_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}),
        error_messages={"required": "Ilagay ang petsa ng katapusan.", "invalid": "Hindi tama ang petsa."},
        label="Hanggang",
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date, end_date = cleaned_data.get("start_date"), cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            self.add_error("end_date", "Dapat hindi mas maaga ang “Hanggang” kaysa sa “Mula”.")
        return cleaned_data
