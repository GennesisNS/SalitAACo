from django.contrib.auth.decorators import login_required
from django.db.models import Min, Sum
from django.shortcuts import render

from salitaaco.forms.children.usage_range import UsageRangeForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.board import all_boards
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.usage import usage_in_days, with_bar_widths, word_usage


@active_nav("child_usage")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_child_usage(request, child_uuid):
    """What a child used most on their board. Counts of taps and openings only, never what was said."""
    child = guardian_child_or_404(request, child_uuid)

    range_form = UsageRangeForm(request.GET or None)
    days = range_form.days()

    icons = {board["name"]: board["icon"] for board in all_boards()}
    boards = with_bar_widths(usage_in_days(child.user, DailyUsage.BOARD, days))
    for row in boards:
        row["icon"] = icons.get(row["name"], "")

    context = {
        "child": child,
        "ranges": [
            {"value": value, "label": label, "active": value == range_form.chosen()}
            for value, label in range_form.fields["range"].choices
        ],
        "words": with_bar_widths(word_usage(child.user, days)),
        "boards": boards,
        "total_taps": child.user.word_usages.aggregate(total=Sum("use_count"))["total"] or 0,
        # Days are counted from the first tap after this page existed; before that only totals were kept.
        "counted_since": child.user.daily_usages.aggregate(first=Min("day"))["first"],
    }
    return render(request, 'dashboard/children/usage.html', context)
