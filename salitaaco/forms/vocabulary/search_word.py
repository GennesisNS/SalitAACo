from django import forms

from salitaaco.utils.board import every_board_name

from ..helpers import BaseForm

EVERY_BOARD = ""


class SearchWordForm(BaseForm):
    """Narrows the list of words to those that contain some text, and to one board."""
    query = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Hanapin ang salita"}),
        label="Hanapin",
    )
    board = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "select"}),
        label="Board",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["board"].choices = [(EVERY_BOARD, "Lahat ng board")] + [(name, name) for name in every_board_name()]

    def filters(self):
        """The text and the board asked for; nothing when the form cannot be read."""
        if not self.is_valid():
            return "", EVERY_BOARD
        return self.cleaned_data["query"].strip().lower(), self.cleaned_data["board"]
