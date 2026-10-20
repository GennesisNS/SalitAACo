from django.db import models
import uuid


class GuardianBoard(models.Model):
    """
    A board a guardian made for their family, after the app's boards. Its
    tiles are the guardian's own tiles (GuardianWord) put on it, and it shows,
    once it has one, on the guardian's own board and on each of their
    children's, where the guardian can turn it off as any other board. How many
    a guardian can have depends on their plan.
    """
    guardian_board_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='boards')
    # Its tiles find it by this name (GuardianWord.board), as the app's boards are found by theirs.
    name = models.CharField(max_length=40)
    # The board's picture: an emoji, as the app's boards have.
    emoji = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "guardian_board_id"]
        constraints = [
            models.UniqueConstraint(fields=['guardian', 'name'], name='unique_guardian_board'),
        ]

    def __str__(self):
        return f"{self.emoji} {self.name} ({self.guardian})"
