"""
A guardian's plan and payments.

FRONTEND ONLY FOR NOW: these pages show the design of choosing a plan, paying
by QR code and uploading the proof of payment. Nothing is saved; the plans come
from defaults/plans.py and there are no payments to list.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from salitaaco.defaults.plans import PLUS
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_guardian, multi_user_test
from salitaaco.utils.plans import current_plan, examples_can_be_shown, examples_requested, offered_plans, transactions
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE


@active_nav("plan")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_plan(request):
    """The plans, the one the guardian is on, and how to pay for another."""
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    plan = current_plan(guardian)

    context = {
        "current_plan": plan,
        "plans": [
            # A plan that costs something is paid for before it starts; the free one needs no payment.
            {**offered, "is_current": offered["key"] == plan["key"], "needs_payment": offered["price"] > 0}
            for offered in offered_plans()
        ],
        "paid_plan": next((offered for offered in offered_plans() if offered["key"] == PLUS), None),
        "max_proof_megabytes": MAX_UPLOAD_SIZE // (1024 * 1024),
    }
    return render(request, 'dashboard/plan/plan.html', context)


@active_nav("plan")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_transactions(request):
    """The guardian's payments and what became of each."""
    context = {
        "transactions": transactions(request),
        "examples_can_be_shown": examples_can_be_shown(),
        "showing_examples": examples_requested(request),
    }
    return render(request, 'dashboard/plan/transactions.html', context)
