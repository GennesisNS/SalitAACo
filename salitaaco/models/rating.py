from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import uuid


class Rating(models.Model):
    """A user's rating of the app, from 1 to 5 stars, with an optional comment. One per user."""
    MIN_RATING = 1
    MAX_RATING = 5

    rating_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='rating')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)],
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='chk_rating_range',
            ),
        ]

    @property
    def stars(self):
        return "★" * self.rating + "☆" * (self.MAX_RATING - self.rating)

    def __str__(self):
        return f"{self.rating}/5 ({self.user})"
