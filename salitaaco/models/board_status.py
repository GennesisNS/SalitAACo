from django.db import models


class BoardStatus(models.Model):
    """
    Whether a board is published. The boards are the categories of
    defaults/vocabulary.py and are published unless an admin says otherwise, so
    only the boards an admin has changed have a row here.

    A board that is not published is shown to nobody: not to children, and not
    to guardians choosing their children's boards.
    """
    board_status_id = models.AutoField(primary_key=True)
    # The board's name, spelled as in the vocabulary.
    board = models.CharField(max_length=100, unique=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.board}: {'published' if self.is_published else 'hidden'}"
