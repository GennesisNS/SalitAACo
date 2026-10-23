from django import forms

from ..helpers import BaseForm
from ..validators import check_tile_word, validate_sound_size, validate_sound_type


class UploadTileSoundForm(BaseForm):
    """A recording for one of the tiles on the board: `words` are the words its boards have."""
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

    def __init__(self, *args, words=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.words = words

    def clean_word(self):
        return check_tile_word(self.cleaned_data["word"], self.words)
