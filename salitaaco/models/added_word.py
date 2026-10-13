from django.db import models
import uuid


class AddedWord(models.Model):
    """
    A word an admin added to a board, on top of the default vocabulary in
    defaults/vocabulary.py (which is never edited). It is shown after the
    board's own words, to every account that sees the board.
    """
    added_word_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # The board's name, spelled as in the vocabulary.
    board = models.CharField(max_length=100)
    # What the tile says. No two tiles say the same thing, so that a word's
    # picture, recording and count always belong to one tile.
    word = models.CharField(max_length=40, unique=True)
    # The tile's picture: an emoji, as the default words have.
    emoji = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.emoji} {self.word} ({self.board})"
