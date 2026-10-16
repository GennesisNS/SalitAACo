from django import forms

from salitaaco.utils.board import all_boards
from salitaaco.utils.tile_audio import VERB_ASPECTS

from ..helpers import BaseForm


def word_choices():
    """Every word of the published boards, grouped by board. A verb is offered in each of its three aspects, as the board shows it."""
    groups = []
    for board in all_boards():
        words = []
        for item in board["items"]:
            verb = item.get("verb")
            words += [verb[aspect] for aspect in VERB_ASPECTS] if verb else [item["w"]]
        groups.append((board["name"], [(word, word) for word in words]))
    return groups


class AddFavoriteWordForm(BaseForm):
    """A tile word to put on a child's Paborito screen."""
    word = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={"class": "select"}),
        error_messages={
            "required": "Pumili ng salita.",
            "invalid_choice": "Pumili ng salita mula sa listahan.",
        },
        label="Salitang idadagdag",
    )

    def __init__(self, *args, child=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = child
        self.fields["word"].choices = [("", "Pumili ng salita…")] + word_choices()

    def clean_word(self):
        word = self.cleaned_data["word"]
        if self.child.favorite_words.filter(word=word).exists():
            raise forms.ValidationError("Paborito na ang salitang ito.")
        return word
