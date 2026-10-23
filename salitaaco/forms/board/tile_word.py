from django import forms

from ..helpers import BaseForm
from ..validators import check_tile_word


class TileWordForm(BaseForm):
    """
    The word of the tile that was tapped. `words` are the words the user's
    boards have (utils/board.board_words), so that only a tile's tap is counted.
    """
    word = forms.CharField(
        required=True,
        max_length=100,
        error_messages={"required": "Walang word."},
    )

    def __init__(self, *args, words=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.words = words

    def clean_word(self):
        return check_tile_word(self.cleaned_data["word"], self.words)
