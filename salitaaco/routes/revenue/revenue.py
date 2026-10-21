"""
The admin's record of payments: each picture of a GCash payment a guardian
uploaded and what became of it, by status. It only shows them; the waiting
ones are approved or rejected on Mga Subscription (routes/subscriptions/).
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from salitaaco.forms.revenue.transaction_status import TransactionStatusForm
from salitaaco.models.payment import Payment
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test


@active_nav("revenue")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_revenue(request):
    status_form = TransactionStatusForm(request.GET or None)
    status = status_form.chosen()

    payments = Payment.objects.select_related("guardian__user", "plan")
    counts = dict(payments.values_list("status").annotate(count=Count("payment_id")).order_by())

    context = {
        "payments": paginate(payments.filter(status=status) if status else payments, request.GET.get("page", 1)),
        # Each status as a tab, with how many payments it holds.
        "tabs": [
            {
                "value": value,
                "label": label,
                "count": counts.get(value, 0) if value else sum(counts.values()),
                "active": value == status,
            }
            for value, label in status_form.fields["status"].choices
        ],
    }
    return render(request, 'dashboard/revenue/revenue.html', context)
