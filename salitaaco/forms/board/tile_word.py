from django import forms

from ..helpers import BaseForm


class TileWordForm(BaseForm):
    """The word of the tile that was tapped."""
    word = forms.CharField(
        required=True,
        max_length=100,
        error_messages={"required": "Walang word."},
    )
