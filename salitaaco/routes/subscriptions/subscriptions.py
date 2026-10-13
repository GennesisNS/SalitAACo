"""
The admin's view of subscriptions: how many guardians are on each plan, and the plans themselves.

FRONTEND ONLY FOR NOW: nothing is saved about subscriptions yet, so every
guardian counts as on the free plan, and the form that edits a plan is shown disabled.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from salitaaco.defaults.plans import DEFAULT_PLAN, PLANS
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test


@active_nav("subscriptions")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_subscriptions(request):
    guardians = GuardianAccount.objects.count()

    plans = [
        # Without subscriptions, the free plan has every guardian and the others have none.
        {
            **plan,
            "subscribers": guardians if plan["key"] == DEFAULT_PLAN else 0,
            # One feature per line, as the plan's form will take them.
            "features_text": "\n".join(plan["features"]),
        }
        for plan in PLANS
    ]

    stat_cards = [
        {"label": "Mga tagapag-alaga", "value": guardians},
    ] + [
        {"label": f"Naka-{plan['name']}", "value": plan["subscribers"]} for plan in plans
    ] + [
        # No payment can be approved yet, so nothing has been earned.
        {"label": "Kita ngayong buwan", "value": "₱0", "sub": "mula sa mga aprubadong bayad"},
    ]

    context = {
        "stat_cards": stat_cards,
        "plans": plans,
    }
    return render(request, 'dashboard/subscriptions/subscriptions.html', context)
