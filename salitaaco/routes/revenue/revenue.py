"""
The admin's list of payments: each picture of a GCash payment a guardian
uploaded, to approve or reject. Approving one puts the guardian on the plan
(see utils/plans.py); rejecting one tells the guardian why.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from salitaaco.forms.revenue.reject_payment import RejectPaymentForm
from salitaaco.forms.revenue.transaction_status import TransactionStatusForm
from salitaaco.models.payment import Payment
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.plans import approve_payment as approve, reject_payment as reject

logger = logging.getLogger(__name__)


def back_to_list(request):
    """The list again, on the tab and page the admin was on."""
    response = redirect('revenue')
    if request.POST.get("next", "").startswith("?"):
        response["Location"] += request.POST["next"]
    return response


@active_nav("revenue")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_revenue(request):
    """
    The payments, by status. Rejecting one is a form of this page, so that a
    reason that is not valid reopens its dialog with what was typed.
    """
    status_form = TransactionStatusForm(request.GET or None)
    status = status_form.chosen()

    reject_form = RejectPaymentForm()
    rejecting = None
    rejection_failed = False

    if request.method == "POST" and "reject_form" in request.POST:
        reject_form = RejectPaymentForm(request.POST)
        if reject_form.is_valid():
            payment = get_object_or_404(Payment.objects.select_related("guardian"), uuid=reject_form.cleaned_data["payment"])
            if reject(payment, request.user, reject_form.cleaned_data["note"]):
                logger.info("Admin %s rejected payment %s of %s", request.user.username, payment.uuid, payment.guardian)
                messages.success(request, f"Tinanggihan ang bayad ni {payment.guardian.display_name}.")
            else:
                messages.error(request, "Hindi na naghihintay ang bayad na ito.")
            # Back to the same tab and page.
            return redirect(f"{reverse('revenue')}?{request.GET.urlencode()}" if request.GET else 'revenue')
        rejection_failed = True
        rejecting = reject_form.cleaned_data.get("payment")

    payments = Payment.objects.select_related("guardian__user", "plan")
    counts = dict(payments.values_list("status").annotate(count=Count("payment_id")).order_by())
    payments_page = paginate(payments.filter(status=status) if status else payments, request.GET.get("page", 1))

    # The dialog to reopen is on this page of the list; if the payment is not, say why here.
    if rejection_failed and not any(payment.uuid == rejecting for payment in payments_page):
        messages.error(request, " ".join(reject_form.errors.get("note", ["Hindi na-reject ang bayad."])))
        rejecting = None

    context = {
        "payments": payments_page,
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
        "reject_form": reject_form,
        "rejecting": rejecting,
    }
    return render(request, 'dashboard/revenue/revenue.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def approve_payment(request, payment_uuid):
    payment = get_object_or_404(Payment.objects.select_related("guardian", "plan"), uuid=payment_uuid)
    if approve(payment, request.user):
        logger.info("Admin %s approved payment %s of %s", request.user.username, payment.uuid, payment.guardian)
        messages.success(request, f"Naaprubahan na. Naka-{payment.plan.name} na si {payment.guardian.display_name}.")
    else:
        messages.error(request, "Hindi na naghihintay ang bayad na ito.")
    return back_to_list(request)
