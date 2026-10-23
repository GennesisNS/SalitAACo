from django import forms
from django.utils.html import format_html

# Django's own error messages are in English. A field that does not say its
# own message for one of these gets this one instead.
DEFAULT_ERROR_MESSAGES = {
    "required": "Kailangang sagutan ito.",
    "max_length": "Masyadong mahaba (hanggang %(limit_value)d character).",
    "min_length": "Masyadong maikli (hindi bababa sa %(limit_value)d character).",
    "max_value": "Hanggang %(limit_value)s lang.",
    "min_value": "Hindi bababa sa %(limit_value)s.",
    "invalid_choice": "Pumili mula sa listahan.",
}


def django_error_messages(field):
    """The messages Django gives a field of its kind, before a form says its own."""
    messages = {}
    for kind in reversed(type(field).__mro__):
        messages.update(getattr(kind, "default_error_messages", {}))
    return messages


class BaseForm(forms.Form):
    """
    Base for every form in the project: required fields get a red asterisk on
    their label, and errors a field has no message of its own for are said in
    Filipino (DEFAULT_ERROR_MESSAGES).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.required and field.label:
                field.label = format_html('{} <span class="required-mark">*</span>', field.label)
            djangos = django_error_messages(field)
            for code, message in DEFAULT_ERROR_MESSAGES.items():
                # Still Django's own (or none at all): the form did not choose one.
                if field.error_messages.get(code) is djangos.get(code):
                    field.error_messages[code] = message
