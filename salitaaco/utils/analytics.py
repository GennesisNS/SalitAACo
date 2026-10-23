from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Exists, OuterRef, Q, Sum
from django.utils import timezone

from salitaaco.models.customization import Customization
from salitaaco.models.rating import Rating
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.word_usage import WordUsage

SIGNUP_CHART_DAYS = 14
TOP_WORDS_LIMIT = 15


def family_tile_taps(usages, word_field):
    """
    `usages` (WordUsage, or DailyUsage of words, whose word is in `word_field`)
    without the taps of a family's own tiles: a name, a place at home. Only the
    family's own taps of their tile are left out; the same word as an app tile,
    tapped by anyone else, still counts.
    """
    own_tile = GuardianWord.objects.filter(word=OuterRef(word_field)).filter(
        Q(guardian__user=OuterRef("user")) | Q(guardian__children__user=OuterRef("user"))
    )
    return usages.exclude(Exists(own_tile))


def start_of_today():
    """Midnight today in the project's time zone."""
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


def bar_width(count, highest):
    """Width of a chart bar, as a whole percentage of the longest bar."""
    return round(count / max(1, highest) * 100)


def overview():
    """Top-line numbers for the stat cards."""
    today = start_of_today()
    week_ago = today - timedelta(days=7)
    tomorrow = today + timedelta(days=1)

    average_rating = Rating.objects.aggregate(average=Avg("rating"))["average"]

    return {
        "total_users": User.objects.count(),
        "new_today": User.objects.filter(date_joined__gte=today, date_joined__lt=tomorrow).count(),
        "new_this_week": User.objects.filter(date_joined__gte=week_ago).count(),
        "active_today": User.objects.filter(last_login__gte=today, last_login__lt=tomorrow).count(),
        "active_this_week": User.objects.filter(last_login__gte=week_ago).count(),
        "total_images": Customization.objects.exclude(image="").count(),
        "total_sounds": Customization.objects.exclude(sound="").count(),
        "total_taps": WordUsage.objects.aggregate(total=Sum("use_count"))["total"] or 0,
        "average_rating": round(average_rating, 2) if average_rating is not None else None,
        "average_stars": round(average_rating) if average_rating is not None else 0,
        "rating_count": Rating.objects.count(),
    }


def signups_by_day():
    """Sign-ups per day for the last 14 days, oldest first, with days that had none."""
    today = start_of_today()
    first_day = today - timedelta(days=SIGNUP_CHART_DAYS - 1)

    # Grouped here, not in SQL: date functions on MySQL need its time zone tables loaded.
    joined = User.objects.filter(date_joined__gte=first_day).values_list("date_joined", flat=True)
    counts = Counter(timezone.localtime(moment).date() for moment in joined)

    days = [(first_day + timedelta(days=offset)).date() for offset in range(SIGNUP_CHART_DAYS)]
    highest = max(counts.values(), default=0)

    return [
        {"date": day, "count": counts[day], "width": bar_width(counts[day], highest)}
        for day in days
    ]


def rating_distribution():
    """How many users gave each number of stars, five stars first."""
    counts = dict(Rating.objects.values_list("rating").annotate(count=Count("rating_id")))
    highest = max(counts.values(), default=0)

    return [
        {"label": f"{stars} ★", "count": counts.get(stars, 0), "width": bar_width(counts.get(stars, 0), highest)}
        for stars in range(Rating.MAX_RATING, Rating.MIN_RATING - 1, -1)
    ]


def top_words(limit=TOP_WORDS_LIMIT):
    """
    The most-used words across all users. A family's own tiles are theirs (a
    name, a place at home), and are not counted here.
    """
    words = list(
        family_tile_taps(WordUsage.objects.all(), "word")
        .values("word")
        .annotate(total_uses=Sum("use_count"), user_count=Count("user", distinct=True))
        .order_by("-total_uses", "word")[:limit]
    )
    highest = max((word["total_uses"] for word in words), default=0)

    for word in words:
        word["width"] = bar_width(word["total_uses"], highest)
    return words
