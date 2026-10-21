from django import forms

from ..helpers import BaseForm

MAX_FEATURES = 12


class PlanForm(BaseForm):
    """
    A plan as an admin edits it on Mga Subscription. The default plan has no
    price or offered fields: it is always free and always offered.
    """
    name = forms.CharField(
        required=True,
        max_length=60,
        widget=forms.TextInput(attrs={"class": "input"}),
        error_messages={"required": "Ilagay ang pangalan ng plano."},
        label="Pangalan",
    )
    price = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=100000,
        widget=forms.NumberInput(attrs={"class": "input", "min": 1}),
        error_messages={
            "required": "Ilagay ang presyo.",
            "invalid": "Hindi tama ang presyo.",
            "min_value": "Hindi bababa sa ₱1 ang presyo ng bayad na plano.",
            "max_value": "Hindi tama ang presyo.",
        },
        label="Presyo (₱) kada buwan",
    )
    features = forms.CharField(
        required=True,
        max_length=1000,
        widget=forms.Textarea(attrs={"class": "textarea", "rows": 4}),
        error_messages={
            "required": "Ilagay kahit isang kasama sa plano.",
            "max_length": "Masyadong mahaba ang listahan (hanggang 1000 character).",
        },
        label="Mga kasama (isa kada linya)",
    )
    offered = forms.BooleanField(
        required=False,
        label="Iniaalok sa mga tagapag-alaga",
    )

    def __init__(self, *args, include_price=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not include_price:
            del self.fields["price"]
            del self.fields["offered"]

    def clean_features(self):
        """One feature per line, without the blank lines."""
        features = [line.strip() for line in self.cleaned_data["features"].splitlines() if line.strip()]
        if not features:
            raise forms.ValidationError("Ilagay kahit isang kasama sa plano.")
        if len(features) > MAX_FEATURES:
            raise forms.ValidationError(f"Hanggang {MAX_FEATURES} kasama lang ang puwede.")
        return "\n".join(features)
