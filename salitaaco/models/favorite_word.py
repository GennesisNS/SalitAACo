from django.db import models
import uuid


class FavoriteWord(models.Model):
    """
    A word a guardian put on a child's Paborito screen, ahead of the words the
    child uses most. Belongs to the "Mga Paborito" page (routes/favorites/),
    which may be removed: nothing else reads this model.
    """
    favorite_word_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    child = models.ForeignKey('ChildAccount', on_delete=models.CASCADE, related_name='favorite_words')
    # A tile word, spelled as on the board.
    word = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['child', 'word'], name='unique_child_favorite_word'),
        ]

    def __str__(self):
        return f"{self.word} ({self.child})"
