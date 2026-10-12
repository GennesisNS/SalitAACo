from django.db import models


class HiddenBoard(models.Model):
    """
    A board a guardian turned off for one of their children. The boards
    themselves are the categories of defaults/vocabulary.py; only the ones
    turned off are stored, so a board added to the vocabulary later is on for
    every child until their guardian decides otherwise.
    """
    hidden_board_id = models.AutoField(primary_key=True)
    child = models.ForeignKey('ChildAccount', on_delete=models.CASCADE, related_name='hidden_boards')
    # The board's name, spelled as in the vocabulary.
    board = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['child', 'board'], name='unique_child_hidden_board'),
        ]

    def __str__(self):
        return f"{self.board} ({self.child})"
