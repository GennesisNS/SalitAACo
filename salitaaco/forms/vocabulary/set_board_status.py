from django import forms

from salitaaco.utils.board import board_names, every_board_name

from ..helpers import BaseForm


class SetBoardStatusForm(BaseForm):
    """Publishes a board or hides it from everyone. At least one board has to stay published."""
    board = forms.ChoiceField(
        required=True,
        error_messages={"required": "Walang ganitong board.", "invalid_choice": "Walang ganitong board."},
    )
    published = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["board"].choices = [(name, name) for name in every_board_name()]

    def clean(self):
        cleaned_data = super().clean()
        board = cleaned_data.get("board")
        if board and not cleaned_data.get("published") and board_names() == [board]:
            raise forms.ValidationError("Kailangang may kahit isang board na naka-publish.")
        return cleaned_data
