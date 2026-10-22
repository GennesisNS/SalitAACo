"""
The admin's view of subscriptions: how many guardians are on each plan, what
was earned this month, and the payments waiting to be approved or rejected.

Approving a payment puts the guardian on the plan (see utils/plans.py);
rejecting one tells the guardian why. Kita (routes/revenue/) is the record of
every payment and what became of it; the plans themselves are set up on
System Settings > Mga Plano (routes/system/plans.py).
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from salitaaco.defaults.plans import PENDING
from salitaaco.forms.subscriptions.reject_payment import RejectPaymentForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.plans import approve_payment as approve, reject_payment as reject, revenue_this_month, subscriber_counts

logger = logging.getLogger(__name__)


def back_to_page(request):
    """This page again, on the page of waiting payments the admin was on."""
    response = redirect('subscriptions')
    if request.POST.get("next", "").startswith("?"):
        response["Location"] += request.POST["next"]
    return response


@active_nav("subscriptions")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_subscriptions(request):
    plans = list(Plan.objects.all())

    reject_form = RejectPaymentForm()
    rejecting = None
    rejection_failed = False

    if request.method == "POST" and "reject_form" in request.POST:
        # Rejecting is a form of this page, so that a reason that is not valid reopens its dialog with what was typed.
        reject_form = RejectPaymentForm(request.POST)
        if reject_form.is_valid():
            payment = get_object_or_404(Payment.objects.select_related("guardian"), uuid=reject_form.cleaned_data["payment"])
            if reject(payment, request.user, reject_form.cleaned_data["note"]):
                logger.info("Admin %s rejected payment %s of %s", request.user.username, payment.uuid, payment.guardian)
                messages.success(request, f"Tinanggihan ang bayad ni {payment.guardian.display_name}.")
            else:
                messages.error(request, "Hindi na naghihintay ang bayad na ito.")
            return redirect(f"{reverse('subscriptions')}?{request.GET.urlencode()}" if request.GET else 'subscriptions')
        rejection_failed = True
        rejecting = reject_form.cleaned_data.get("payment")

    # The oldest first: they have waited longest.
    pending = Payment.objects.filter(status=PENDING).select_related("guardian__user", "plan").order_by("created_at", "payment_id")
    pending_page = paginate(pending, request.GET.get("pending_page", 1))

    # The dialog to reopen is on this page of the list; if the payment is not, say why here.
    if rejection_failed and not any(payment.uuid == rejecting for payment in pending_page):
        messages.error(request, " ".join(reject_form.errors.get("note", ["Hindi na-reject ang bayad."])))
        rejecting = None

    counts = subscriber_counts()

    stat_cards = [
        {"label": "Mga tagapag-alaga", "value": GuardianAccount.objects.count()},
    ] + [
        {"label": f"Naka-{plan.name}", "value": counts.get(plan.key, 0)} for plan in plans
    ] + [
        {"label": "Kita ngayong buwan", "value": f"₱{revenue_this_month():,}", "sub": "mula sa mga aprubadong bayad"},
    ]

    context = {
        "stat_cards": stat_cards,
        "pending_payments": pending_page,
        "pending_count": pending.count(),
        "reject_form": reject_form,
        "rejecting": rejecting,
    }
    return render(request, 'dashboard/subscriptions/subscriptions.html', context)


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
    return back_to_page(request)
