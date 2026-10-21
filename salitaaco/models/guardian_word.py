from django.db import models
import uuid


class GuardianWord(models.Model):
    """
    A tile a guardian on a paid plan added to one of the boards. It is shown,
    after the board's own words, on the guardian's own board and on every one
    of their children's. While the guardian is not on a paid plan it is kept
    but not shown. How many a guardian can have is a site setting.
    """
    guardian_word_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='words')
    # The board's name, spelled as in the vocabulary.
    board = models.CharField(max_length=100)
    # What the tile says. It differs from every other tile the guardian's family sees.
    word = models.CharField(max_length=40)
    # The tile's picture: an emoji, as the default words have.
    emoji = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "guardian_word_id"]
        constraints = [
            models.UniqueConstraint(fields=['guardian', 'word'], name='unique_guardian_word'),
        ]

    def __str__(self):
        return f"{self.emoji} {self.word} ({self.board}, {self.guardian})"
