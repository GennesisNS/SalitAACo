from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone

from salitaaco.models.child_account import ChildAccount
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.utils.analytics import bar_width, start_of_today
from salitaaco.utils.board import every_board

USAGE_CHART_DAYS = 7
TOP_BOARDS = 6
RECENT_ROWS = 5


def last_days(count):
    """The last `count` days, oldest first, today last."""
    today = timezone.localdate()
    return [today - timedelta(days=offset) for offset in range(count - 1, -1, -1)]


def usage_by_day(days=USAGE_CHART_DAYS):
    """Taps and board openings per day across every account, oldest day first, with days that had none."""
    wanted = last_days(days)
    totals = DailyUsage.objects.filter(day__gte=wanted[0]).values("day", "kind").annotate(total=Sum("use_count"))
    counts = {(row["day"], row["kind"]): row["total"] for row in totals}

    rows = [
        {
            "date": day,
            "taps": counts.get((day, DailyUsage.WORD), 0),
            "board_opens": counts.get((day, DailyUsage.BOARD), 0),
        }
        for day in wanted
    ]
    highest = max((row["taps"] for row in rows), default=0)
    for row in rows:
        row["height"] = bar_width(row["taps"], highest)
    return rows


def board_opens(limit=TOP_BOARDS):
    """
    The app's boards opened most across every account, with each board's
    picture. A family's own boards are theirs, and are not counted here.
    """
    icons = {board["name"]: board["icon"] for board in every_board()}
    totals = (
        DailyUsage.objects.filter(kind=DailyUsage.BOARD, name__in=list(icons))
        .values("name").annotate(total=Sum("use_count")).order_by("-total", "name")[:limit]
    )
    rows = [{"name": row["name"], "icon": icons.get(row["name"], ""), "count": row["total"]} for row in totals]
    highest = max((row["count"] for row in rows), default=0)
    for row in rows:
        row["width"] = bar_width(row["count"], highest)
    return rows


def account_counts():
    """How many accounts there are of each kind, and how many cannot log in."""
    return {
        "guardians": GuardianAccount.objects.count(),
        "children": ChildAccount.objects.count(),
        "inactive": User.objects.filter(is_active=False).count(),
    }


def open_feedback_count():
    """Support messages nobody has marked as dealt with yet."""
    return SupportMessage.objects.filter(resolved_at__isnull=True).count()


def recent_activity(limit=RECENT_ROWS):
    """The latest sign-ups, support messages and ratings, as one list, newest first."""
    events = [
        {"when": user.date_joined, "kind": "Bagong account", "text": f"@{user.username}"}
        for user in User.objects.order_by("-date_joined")[:limit]
    ] + [
        {"when": message.created_at, "kind": "Mensahe sa suporta", "text": f"mula kay {message.guardian.display_name}"}
        for message in SupportMessage.objects.select_related("guardian").order_by("-created_at")[:limit]
    ] + [
        {"when": rating.updated_at, "kind": "Rating", "text": f"{rating.stars} mula kay @{rating.user.username}"}
        for rating in Rating.objects.select_related("user").order_by("-updated_at")[:limit]
    ]
    return sorted(events, key=lambda event: event["when"], reverse=True)[:limit]


def percent(part, whole):
    return f"{round(part / whole * 100)}%" if whole else "—"


def retention():
    """
    How many accounts come back. Counted from what the app already keeps:
    when each account last logged in, and the days on which a child tapped.
    """
    today = start_of_today()
    total = User.objects.count()
    # Signing up counts as a login, so "came back" means a login on a later day.
    joined_and_seen = User.objects.filter(last_login__isnull=False).values_list("date_joined", "last_login")
    came_back = sum(
        1 for joined, seen in joined_and_seen
        if timezone.localtime(seen).date() > timezone.localtime(joined).date()
    )
    seen_this_week = User.objects.filter(last_login__gte=today - timedelta(days=7)).count()
    seen_this_month = User.objects.filter(last_login__gte=today - timedelta(days=30)).count()

    # One (user, day) pair for each day a user tapped at least one word.
    days_tapped = DailyUsage.objects.filter(kind=DailyUsage.WORD).values_list("user_id", "day").distinct()
    days_used = Counter(user_id for user_id, day in days_tapped)
    board_users = len(days_used)
    used_more_than_a_day = sum(1 for days in days_used.values() if days > 1)

    return [
        {"metric": "Bumalik pagkatapos mag-sign up", "meaning": "Mga account na nag-log in ulit sa ibang araw",
         "value": f"{came_back} sa {total} ({percent(came_back, total)})"},
        {"metric": "Nag-log in sa huling 7 araw", "meaning": "Mga account na aktibo ngayong linggo",
         "value": f"{seen_this_week} sa {total} ({percent(seen_this_week, total)})"},
        {"metric": "Nag-log in sa huling 30 araw", "meaning": "Mga account na aktibo ngayong buwan",
         "value": f"{seen_this_month} sa {total} ({percent(seen_this_month, total)})"},
        {"metric": "Gumamit ng board nang higit sa isang araw", "meaning": "Mga gumagamit ng board na bumabalik dito",
         "value": f"{used_more_than_a_day} sa {board_users} ({percent(used_more_than_a_day, board_users)})"},
    ]


def accounts_by_role():
    """How many accounts each kind has, for the growth tab."""
    return [
        {"label": "Tagapag-alaga", "count": GuardianAccount.objects.count()},
        {"label": "Bata", "count": ChildAccount.objects.count()},
        {"label": "Admin", "count": User.objects.filter(admin_account__isnull=False).count()},
    ]


def ratings_by_stars():
    """{stars: count}, for the summary beside the average."""
    return dict(Rating.objects.values_list("rating").annotate(count=Count("rating_id")))
