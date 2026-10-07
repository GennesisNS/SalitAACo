from django import forms
from django.utils.html import format_html


class BaseForm(forms.Form):
    """Base for every form in the project: required fields get a red asterisk on their label."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.required and field.label:
                field.label = format_html('{} <span class="required-mark">*</span>', field.label)
