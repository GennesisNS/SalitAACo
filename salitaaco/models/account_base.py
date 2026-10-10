from django.db import models
import uuid


class AccountBase(models.Model):
    """
    What every kind of account has beyond Django's own User: the name shown on
    screen and the profile picture. ChildAccount, GuardianAccount and
    AdminAccount each add their own key, their link to the user, and whatever
    only that kind of account needs.
    """
    TILE_SIZE_CHOICES = [
        ("small", "Maliit"),
        ("medium", "Katamtaman"),
        ("large", "Malaki"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    display_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    avatar_mime = models.CharField(max_length=50, blank=True)
    # How big the tiles on this account's board are drawn.
    tile_size = models.CharField(max_length=10, choices=TILE_SIZE_CHOICES, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Only children have an age. The other accounts answer None, so pages that
    # list every kind of account can ask any of them.
    age = None

    class Meta:
        abstract = True

    @property
    def has_avatar(self):
        return bool(self.avatar)

    @property
    def role_badge_class(self):
        """CSS classes for the pill that names the kind of account."""
        return "badge"

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
