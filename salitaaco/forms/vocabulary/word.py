from django import forms

from salitaaco.utils.board import every_board_name
from salitaaco.utils.tile_audio import tile_word_slug, tile_words

from ..picture_choice import EMOJI_KEYS, PictureChoiceForm


class WordForm(PictureChoiceForm):
    """
    A word an admin adds to a board, or changes, with its symbol: an emoji or
    an uploaded picture. `editing` is the AddedWord being changed, so that it
    is not taken for a copy of itself and keeps its picture when no new one is chosen.
    """
    picture_label = "Simbolo"
    emoji_missing = "Ilagay ang simbolo."
    image_missing = "Pumili ng larawan ng salita."

    board = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={"required": "Pumili ng board.", "invalid_choice": "Walang ganitong board."},
        label="Board",
    )
    word = forms.CharField(
        required=True,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "hal. pandesal"}),
        error_messages={
            "required": "Ilagay ang salita.",
            "max_length": "Masyadong mahaba ang salita (hanggang 40 character).",
        },
        label="Salita",
        help_text="Ito mismo ang lalabas sa tile at bibigkasin.",
    )
    emoji = forms.CharField(
        required=False,
        max_length=16,
        widget=forms.TextInput(attrs={"class": "input emojiInput"}),
        error_messages={"max_length": "Isang emoji lang ang simbolo."},
        label="Emoji",
        help_text=f"Isang emoji lang, hal. 🥖 para sa pandesal. {EMOJI_KEYS}",
    )

    def __init__(self, *args, editing=None, **kwargs):
        super().__init__(*args, editing=editing, **kwargs)
        self.fields["board"].choices = [("", "Pumili ng board…")] + [(name, name) for name in every_board_name()]

    def clean_word(self):
        word = " ".join(self.cleaned_data["word"].split())
        slug = tile_word_slug(word)
        if not slug:
            raise forms.ValidationError("Kailangang may titik o numero ang salita.")

        # A word's recording, picture and count are found by the word and by the
        # name of its audio file, so no two tiles may share either.
        others = [other for other in tile_words() if not self.editing or other != self.editing.word]
        if word.lower() in (other.lower() for other in others) or slug in (tile_word_slug(other) for other in others):
            raise forms.ValidationError("May tile na para sa salitang ito.")
        return word
