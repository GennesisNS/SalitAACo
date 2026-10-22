from django.db import models
import uuid


class GuardianBoard(models.Model):
    """
    A board a guardian made for their family, after the app's boards. Its
    tiles are the guardian's own tiles (GuardianWord) put on it, and it shows,
    once it has one, on the guardian's own board and on each of their
    children's, where the guardian can turn it off as any other board. How many
    a guardian can have depends on their plan.

    Its picture is an emoji, or a picture the guardian uploaded (icon_image),
    which, like every upload, is served only by a login-protected view.
    """
    guardian_board_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='boards')
    # Its tiles find it by this name (GuardianWord.board), as the app's boards are found by theirs.
    name = models.CharField(max_length=40)
    # The board's picture: an emoji, as the app's boards have, unless it has an uploaded one.
    emoji = models.CharField(max_length=16, blank=True)
    icon_image = models.ImageField(upload_to='guardian-board-icons/', blank=True)
    icon_mime = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "guardian_board_id"]
        constraints = [
            models.UniqueConstraint(fields=['guardian', 'name'], name='unique_guardian_board'),
        ]

    @property
    def has_icon_image(self):
        return bool(self.icon_image)

    def set_icon_image(self, file_name, content, mime):
        """Use an uploaded picture as the board's picture, removing the one before."""
        self.remove_icon_image(save=False)
        self.icon_image.save(file_name, content, save=False)
        self.icon_mime = mime
        self.emoji = ""
        self.save()

    def remove_icon_image(self, save=True):
        if self.icon_image:
            self.icon_image.delete(save=False)
        self.icon_mime = ""
        if save:
            self.save()

    def __str__(self):
        return f"{self.emoji or '🖼️'} {self.name} ({self.guardian})"
