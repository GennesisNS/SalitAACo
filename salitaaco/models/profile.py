from django.db import models
import uuid


class Profile(models.Model):
    """
    Everything the app knows about an account beyond Django's own User:
    the name shown on screen, the optional age and the profile picture.
    """
    profile_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    avatar_mime = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_avatar(self):
        return bool(self.avatar)

    def set_avatar(self, file_name, content, mime):
        """Replace the profile picture, removing the previous file from storage."""
        self.remove_avatar(save=False)
        self.avatar.save(file_name, content, save=False)
        self.avatar_mime = mime
        self.save()

    def remove_avatar(self, save=True):
        if self.avatar:
            self.avatar.delete(save=False)
        self.avatar_mime = ''
        if save:
            self.save()

    def __str__(self):
        return self.display_name
