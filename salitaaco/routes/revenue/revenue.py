"""
The admin's list of payments: each proof of payment a guardian uploaded, to approve or reject.

FRONTEND ONLY FOR NOW: nothing is saved yet, so the list is empty and the
buttons that approve and reject are shown disabled.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from salitaaco.forms.revenue.transaction_status import TransactionStatusForm
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.plans import examples_can_be_shown, examples_requested, transactions


@active_nav("revenue")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_revenue(request):
    status_form = TransactionStatusForm(request.GET or None)
    status = status_form.chosen()
    every_transaction = transactions(request)

    context = {
        "transactions": [row for row in every_transaction if not status or row["status"] == status],
        # Each status as a tab, with how many payments it holds.
        "tabs": [
            {
                "value": value,
                "label": label,
                "count": sum(1 for row in every_transaction if not value or row["status"] == value),
                "active": value == status,
            }
            for value, label in status_form.fields["status"].choices
        ],
        "examples_can_be_shown": examples_can_be_shown(),
        "showing_examples": examples_requested(request),
    }
    return render(request, 'dashboard/revenue/revenue.html', context)
