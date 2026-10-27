from django import forms

from ..helpers import BaseForm

MAX_FEATURES = 12


class PlanForm(BaseForm):
    """
    A plan as an admin edits it on System Settings > Mga Plano. The default
    plan has no price or offered fields: it is always free and always offered.
    How many child accounts and family voices it allows are set below the plans,
    with the other limits (forms/system/plan_family_limits.py).
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

    def __init__(self, *args, include_price=True, taken_names=(), **kwargs):
        """taken_names: the names of the other plans, which this one may not repeat."""
        super().__init__(*args, **kwargs)
        self.taken_names = {name.lower() for name in taken_names}
        if not include_price:
            del self.fields["price"]
            del self.fields["offered"]

    def clean_name(self):
        """A name no other plan has, so that guardians and admins can tell the plans apart."""
        name = " ".join(self.cleaned_data["name"].split())
        if name.lower() in self.taken_names:
            raise forms.ValidationError("May plano nang may ganitong pangalan.")
        return name

    def clean_features(self):
        """One feature per line, without the blank lines."""
        features = [line.strip() for line in self.cleaned_data["features"].splitlines() if line.strip()]
        if not features:
            raise forms.ValidationError("Ilagay kahit isang kasama sa plano.")
        if len(features) > MAX_FEATURES:
            raise forms.ValidationError(f"Hanggang {MAX_FEATURES} kasama lang ang puwede.")
        return "\n".join(features)
