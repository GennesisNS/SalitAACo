from django import forms

from salitaaco.utils.board import board_names
from salitaaco.utils.guardian_words import on_free_plan
from salitaaco.utils.tile_audio import tile_word_slug

from ..picture_choice import EMOJI, IMAGE
from ..vocabulary.word import WordForm

PLUS_PICTURES = "Para sa SalitAACo Plus ang pag-upload ng larawan. Emoji muna ang simbolo ng tile."
PLUS_PICTURES_KEPT = "Para sa SalitAACo Plus ang pag-upload ng bagong larawan. Puwedeng panatilihin ang kasalukuyang larawan nito."


class GuardianWordForm(WordForm):
    """
    A tile a guardian adds to one of the boards, or changes: an admin's word
    form, with the boards that are shown and the guardian's own, and a check
    against the guardian's other tiles too. `editing` is the GuardianWord
    being changed, so that it is not taken for a copy of itself.

    Uploading a picture for it is for guardians on Plus, like the rest of
    Sariling Tile; on Free (when an admin allows Free tiles at all, or when a
    Plus guardian's plan ended) its symbol is an emoji, or the picture it
    already has.
    """
    image_missing = "Pumili ng larawan ng tile."

    def __init__(self, *args, guardian, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardian = guardian
        names = board_names() + list(guardian.boards.values_list("name", flat=True))
        self.fields["board"].choices = [("", "Pumili ng board…")] + [(name, name) for name in names]
        self.fields["word"].help_text = "Ito mismo ang lalabas sa tile at bibigkasin, sa lahat ng board ng mga anak mo."

        # Said in place of the picture upload when it is not theirs to make.
        self.pictures_note = ""
        if on_free_plan(guardian):
            keeps_picture = self.editing is not None and self.editing.has_icon_image
            self.pictures_note = PLUS_PICTURES_KEPT if keeps_picture else PLUS_PICTURES
            self.fields["icon_kind"].choices = [(EMOJI, "Emoji")] + ([(IMAGE, "Larawan")] if keeps_picture else [])
            self.fields["icon_kind"].error_messages["invalid_choice"] = PLUS_PICTURES

    def clean_icon_image(self):
        # On Free a picture sent anyway is not taken; the tile keeps the one it has, if any.
        return None if self.pictures_note else self.cleaned_data["icon_image"]

    def clean_word(self):
        word = super().clean_word()
        slug = tile_word_slug(word)
        others = self.guardian.words.exclude(pk=self.editing.pk) if self.editing else self.guardian.words.all()
        if any(tile_word_slug(own) == slug for own in others.values_list("word", flat=True)):
            raise forms.ValidationError("May tile ka na para sa salitang ito.")
        return word
