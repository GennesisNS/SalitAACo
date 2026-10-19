from django import forms

from ..helpers import BaseForm


class PlusSettingsForm(BaseForm):
    """What a guardian on a paid plan gets that an admin can change."""
    guardian_word_limit = forms.IntegerField(
        required=True,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={"class": "input", "min": 0, "max": 500}),
        error_messages={
            "required": "Ilagay ang bilang.",
            "invalid": "Hindi tama ang bilang.",
            "min_value": "Hindi tama ang bilang.",
            "max_value": "Hanggang 500 lang.",
        },
        label="Ilang sariling tile ang puwedeng idagdag ng bawat tagapag-alaga",
        help_text="Para sa lahat ng board ng isang tagapag-alaga at ng mga anak niya. 0 para walang makapagdagdag.",
    )
