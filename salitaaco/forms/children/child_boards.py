from django import forms

from ..helpers import BaseForm


class ChildBoardsForm(BaseForm):
    """Which boards a child sees: the ticked ones are on. At least one has to stay on."""
    boards = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        error_messages={"invalid_choice": "Walang ganitong board."},
        label="Mga board na ipinapakita",
    )

    def __init__(self, *args, names=(), **kwargs):
        """names: every board the child's family has, the app's and the guardian's own."""
        super().__init__(*args, **kwargs)
        self.fields["boards"].choices = [(name, name) for name in names]

    def clean_boards(self):
        boards = self.cleaned_data["boards"]
        if not boards:
            raise forms.ValidationError("Kailangang may kahit isang board na naka-on para sa bata.")
        return boards
