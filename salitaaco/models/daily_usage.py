from django.db import IntegrityError, models, transaction
from django.db.models import F
from django.utils import timezone


class DailyUsage(models.Model):
    """
    How many times, on one day, a user tapped a word or opened a board. This is
    what "the last 7 days" on a child's usage page is counted from; WordUsage
    keeps each word's total since the account began.

    Only counts are kept, never the sentences that were built.
    """
    WORD = "word"
    BOARD = "board"
    KIND_CHOICES = [
        (WORD, "Salita"),
        (BOARD, "Board"),
    ]

    daily_usage_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='daily_usages')
    # The day in TIME_ZONE, not in UTC: a tap at 7 in the morning in Manila belongs to that morning.
    day = models.DateField()
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    # The word, or the board's name.
    name = models.CharField(max_length=100)
    use_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'day', 'kind', 'name'], name='unique_user_day_kind_name_usage'),
        ]

    @classmethod
    def record(cls, user, kind, name):
        """Bump today's count for (user, kind, name), starting the row at 1 on the first use of the day."""
        today = timezone.localdate()

        def bump():
            return cls.objects.filter(user=user, day=today, kind=kind, name=name).update(use_count=F('use_count') + 1)

        if bump():
            return
        try:
            with transaction.atomic():
                cls.objects.create(user=user, day=today, kind=kind, name=name, use_count=1)
        except IntegrityError:
            # Another request created the row between the update and the insert.
            bump()

    def __str__(self):
        return f"{self.day} {self.kind} {self.name} x{self.use_count} ({self.user})"
