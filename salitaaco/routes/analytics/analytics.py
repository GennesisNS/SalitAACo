from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from salitaaco.utils import admin_stats, analytics
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test


@active_nav("analytics")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_analytics(request):
    """
    The admin dashboard, where an admin lands after logging in: the numbers at
    a glance. The lists that used to be on this page have pages of their own:
    Mga User, Feedback at mga Isyu, and Analytics at Ulat.
    """
    overview = analytics.overview()
    accounts = admin_stats.account_counts()
    average_rating = overview["average_rating"]

    stat_cards = [
        {"label": "Kabuuang users", "value": overview["total_users"], "sub": f"+{overview['new_today']} ngayong araw"},
        {"label": "Aktibo ngayong linggo", "value": overview["active_this_week"], "sub": f"{overview['active_today']} ngayong araw"},
        {"label": "Mga tagapag-alaga", "value": accounts["guardians"], "sub": ""},
        {"label": "Mga bata", "value": accounts["children"], "sub": ""},
        {"label": "Kabuuang taps", "value": overview["total_taps"], "sub": ""},
        {"label": "Average rating", "value": average_rating if average_rating is not None else "—",
         "sub": f"{overview['rating_count']} na rating"},
        {"label": "Bukas na mensahe sa suporta", "value": admin_stats.open_feedback_count(), "sub": ""},
        {"label": "Hindi aktibong account", "value": accounts["inactive"], "sub": ""},
    ]

    context = {
        "overview": overview,
        "stat_cards": stat_cards,
        "usage_by_day": admin_stats.usage_by_day(),
        "board_opens": admin_stats.board_opens(),
        "recent_activity": admin_stats.recent_activity(),
    }
    return render(request, 'dashboard/analytics/analytics.html', context)
