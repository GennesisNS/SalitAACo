from django.db import IntegrityError, models, transaction
from django.db.models import F
from django.utils import timezone
import uuid


class WordUsage(models.Model):
    """
    How many times a user has tapped a word. Powers the "Madalas Gamitin" tab
    and the most-used words on the admin dashboard.
    """
    word_usage_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='word_usages')
    word = models.CharField(max_length=100)
    use_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'word'], name='unique_user_word_usage'),
        ]

    @classmethod
    def record_use(cls, user, word):
        """Bump the count for (user, word), starting the row at 1 on first use."""
        def bump():
            return cls.objects.filter(user=user, word=word).update(
                use_count=F('use_count') + 1,
                last_used=timezone.now(),
            )

        if bump():
            return
        try:
            with transaction.atomic():
                cls.objects.create(user=user, word=word, use_count=1)
        except IntegrityError:
            # Another request created the row between the update and the insert.
            bump()

    def __str__(self):
        return f"{self.word} x{self.use_count} ({self.user})"
