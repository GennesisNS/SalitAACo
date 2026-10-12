from django import forms

from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.utils.tile_audio import VERB_ASPECTS

from ..helpers import BaseForm


def word_choices():
    """Every tile word, grouped by its board. A verb is offered in each of its three aspects, as the board shows it."""
    groups = []
    for category in CATEGORIES:
        words = []
        for item in category["items"]:
            verb = item.get("verb")
            words += [verb[aspect] for aspect in VERB_ASPECTS] if verb else [item["w"]]
        groups.append((category["name"], [(word, word) for word in words]))
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
