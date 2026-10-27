from django import forms

from salitaaco.defaults.plans import MAX_CHILD_LIMIT, MAX_FAMILY_VOICE_LIMIT

from ..helpers import BaseForm


class PlanFamilyLimitsForm(BaseForm):
    """
    How many child accounts and family voices a guardian on one plan can make,
    as an admin sets them in "Mga Limit ng Plano" on System Settings > Mga
    Plano: a card of these for each plan, beside the tile and board limits.
    A lower number only stops adding; nothing is deleted.
    """
    child_limit = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=MAX_CHILD_LIMIT,
        widget=forms.NumberInput(attrs={"class": "input", "min": 1, "max": MAX_CHILD_LIMIT}),
        error_messages={
            "required": "Ilagay ang bilang.",
            "invalid": "Hindi tama ang bilang.",
            "min_value": "Kahit isang account ng bata.",
            "max_value": f"Hanggang {MAX_CHILD_LIMIT} lang.",
        },
        label="Account ng bata",
    )
    # Left empty, the plan has no limit.
    family_voice_limit = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=MAX_FAMILY_VOICE_LIMIT,
        widget=forms.NumberInput(attrs={"class": "input", "min": 0, "max": MAX_FAMILY_VOICE_LIMIT, "placeholder": "Walang limit"}),
        error_messages={
            "invalid": "Hindi tama ang bilang.",
            "min_value": "Hindi tama ang bilang.",
            "max_value": f"Hanggang {MAX_FAMILY_VOICE_LIMIT} lang.",
        },
        label="Boses ng pamilya",
        help_text="Blangko para walang limit; 0 para walang makagawa.",
    )
