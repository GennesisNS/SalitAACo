from django import forms

from salitaaco.utils.board import board_names
from salitaaco.utils.tile_audio import tile_word_slug

from ..vocabulary.word import WordForm


class GuardianWordForm(WordForm):
    """
    A tile a guardian adds to one of the boards: an admin's word form, with the
    boards that are shown and the guardian's own, and a check against the
    guardian's own tiles too.
    """

    def __init__(self, *args, guardian, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardian = guardian
        names = board_names() + list(guardian.boards.values_list("name", flat=True))
        self.fields["board"].choices = [("", "Pumili ng board…")] + [(name, name) for name in names]
        self.fields["word"].help_text = "Ito mismo ang lalabas sa tile at bibigkasin, sa lahat ng board ng mga anak mo."

    def clean_word(self):
        word = super().clean_word()
        slug = tile_word_slug(word)
        if any(tile_word_slug(own) == slug for own in self.guardian.words.values_list("word", flat=True)):
            raise forms.ValidationError("May tile ka na para sa salitang ito.")
        return word
