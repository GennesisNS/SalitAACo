from django import forms

from salitaaco.utils.board import board_names

from ..helpers import BaseForm


class BoardNameForm(BaseForm):
    """The board that was opened."""
    board = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["board"].choices = [(name, name) for name in board_names()]
