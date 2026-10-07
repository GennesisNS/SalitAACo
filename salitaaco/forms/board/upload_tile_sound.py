from django import forms

from ..helpers import BaseForm
from ..validators import validate_sound_size, validate_sound_type


class UploadTileSoundForm(BaseForm):
    word = forms.CharField(
        required=True,
        max_length=100,
        widget=forms.HiddenInput(attrs={"id": "tileSoundWord"}),
        error_messages={"required": "Walang natanggap na tunog."},
    )
    sound = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={"id": "tileSoundFile", "accept": "audio/*", "class": "hidden"}),
        error_messages={
            "required": "Walang natanggap na tunog.",
            "empty": "Walang natanggap na tunog.",
        },
        validators=[validate_sound_type, validate_sound_size],
    )
