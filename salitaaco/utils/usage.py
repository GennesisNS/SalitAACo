from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from salitaaco.models.daily_usage import DailyUsage
from salitaaco.utils.analytics import bar_width
from salitaaco.utils.word_usage import frequent_words

USAGE_ROWS = 10


def with_bar_widths(rows):
    """Give each row the width of its bar, the longest being the row with the highest count."""
    highest = max((row["use_count"] for row in rows), default=0)
    for row in rows:
        row["width"] = bar_width(row["use_count"], highest)
    return rows


def usage_in_days(user, kind, days=None, limit=USAGE_ROWS):
    """
    What the user used most of one kind (DailyUsage.WORD or DailyUsage.BOARD),
    highest count first: over the last `days` days, today included, or over
    every day counted when `days` is None.
    """
    usages = DailyUsage.objects.filter(user=user, kind=kind)
    if days is not None:
        usages = usages.filter(day__gt=timezone.localdate() - timedelta(days=days))
    totals = usages.values("name").annotate(total=Sum("use_count")).order_by("-total", "name")[:limit]
    return [{"name": row["name"], "use_count": row["total"]} for row in totals]


def word_usage(user, days=None, limit=USAGE_ROWS):
    """
    The user's most-tapped words. Over every day it is each word's total since
    the account began, which includes taps from before days were counted.
    """
    if days is None:
        return [{"name": row["word"], "use_count": row["use_count"]} for row in frequent_words(user, limit)]
    return usage_in_days(user, DailyUsage.WORD, days, limit)
