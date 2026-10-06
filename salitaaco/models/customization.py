from django.db import models
import uuid


class Customization(models.Model):
    """
    A user's own picture and/or recorded sound for one word on the board.
    There is at most one row per (user, word); resetting a tile deletes the row.
    """
    customization_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='customizations')
    word = models.CharField(max_length=100)
    image = models.ImageField(upload_to='customization-images/', blank=True)
    image_mime = models.CharField(max_length=50, blank=True)
    sound = models.FileField(upload_to='customization-sounds/', blank=True)
    sound_mime = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'word'], name='unique_user_word'),
        ]

    @property
    def has_image(self):
        return bool(self.image)

    @property
    def has_sound(self):
        return bool(self.sound)

    @property
    def version(self):
        """Changes whenever the row does, so the browser re-fetches replaced media."""
        return int(self.updated_at.timestamp())

    def set_image(self, file_name, content, mime):
        """Replace the picture, removing the previous file from storage."""
        if self.image:
            self.image.delete(save=False)
        self.image.save(file_name, content, save=False)
        self.image_mime = mime
        self.save()

    def set_sound(self, file_name, content, mime):
        """Replace the recording, removing the previous file from storage."""
        if self.sound:
            self.sound.delete(save=False)
        self.sound.save(file_name, content, save=False)
        self.sound_mime = mime
        self.save()

    def delete_files(self):
        if self.image:
            self.image.delete(save=False)
        if self.sound:
            self.sound.delete(save=False)

    def reset(self):
        """Put the tile back to its default: remove the files and the row."""
        self.delete_files()
        self.delete()

    def __str__(self):
        return f"{self.word} ({self.user})"
