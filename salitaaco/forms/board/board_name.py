from django import forms

from ..helpers import BaseForm


class BoardNameForm(BaseForm):
    """The board that was opened: one of the boards the user's board shows."""
    board = forms.ChoiceField(required=True)

    def __init__(self, *args, names=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["board"].choices = [(name, name) for name in names]
