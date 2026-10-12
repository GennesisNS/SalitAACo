from django import forms

from ..helpers import BaseForm

SHARED_VOICE = ""


class ChooseFamilyVoiceForm(BaseForm):
    """
    Which of the guardian's family voices a child hears. The values are the
    voices' UUIDs. The guardian chooses from a list on the child's page; the
    child chooses from radio buttons on their Settings page (`radios=True`).
    """
    family_voice = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "select"}),
        label="Boses na maririnig",
    )

    def __init__(self, *args, guardian=None, radios=False, **kwargs):
        super().__init__(*args, **kwargs)
        if radios:
            self.fields["family_voice"].widget = forms.RadioSelect()
        # The voices in the order of the choices, after the app's shared voice.
        self.voices = list(guardian.family_voices.order_by("name")) if guardian else []
        self.fields["family_voice"].choices = [(SHARED_VOICE, "Karaniwang boses ng app")] + [
            (str(voice.uuid), voice.name) for voice in self.voices
        ]
