from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import add_board_numbers, children_with_numbers
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.plans import child_slots, current_plan


@active_nav("overview")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_overview(request):
    """Where a guardian lands after logging in: their children at a glance."""
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    children = add_board_numbers(list(children_with_numbers(guardian.children.all())))
    plan = current_plan(guardian)
    slots = child_slots(guardian, plan)

    stat_cards = [
        {"label": "Mga bata", "value": len(children), "sub": f"sa {slots['limit']} na puwede sa plano mo"},
        {"label": "Mga board na naka-on", "value": sum(child.shown_boards for child in children),
         "sub": "sa lahat ng bata"},
        {"label": "Kabuuang pindot", "value": sum(child.total_taps for child in children)},
        {"label": "Boses ng pamilya", "value": guardian.family_voices.count()},
    ]

    context = {
        "children": children,
        "stat_cards": stat_cards,
        "current_plan": plan,
        "child_slots": slots,
    }
    return render(request, 'dashboard/overview/overview.html', context)
