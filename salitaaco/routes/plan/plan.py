"""
A guardian's plan and payments: the plans, paying for one by GCash QR code
with a picture of the payment, and what became of each payment.

The admin approves or rejects the payments on Mga Subscription
(routes/subscriptions/), sets up the plans on System Settings > Mga Plano and
the QR code on System Settings > General.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from salitaaco.forms.plan.payment_proof import PaymentProofForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, is_guardian, multi_user_test
from salitaaco.utils.plans import child_slots, current_plan, family_voice_slots, offered_plans, paid_until, pending_payment
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE, random_upload_name


@active_nav("plan")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_plan(request):
    """The plans, the one the guardian is on, and how to pay for another."""
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    plan = current_plan(guardian)
    setting = SiteSetting.load()
    waiting = pending_payment(guardian)
    paid_plans = [offered for offered in offered_plans() if not offered.is_free]

    proof_form = PaymentProofForm(plans=paid_plans)

    if request.method == "POST" and "proof_form" in request.POST:
        proof_form = PaymentProofForm(request.POST, request.FILES, plans=paid_plans)
        # Without a QR code there is nowhere to have paid, and one payment waits at a time.
        if not setting.has_gcash_qr:
            proof_form.add_error(None, "Wala pang QR code ng GCash. Hindi pa makakabayad.")
        elif waiting:
            proof_form.add_error(None, "May bayad ka pang naghihintay ng admin.")
        elif proof_form.is_valid():
            chosen = next(offered for offered in paid_plans if offered.key == proof_form.cleaned_data["plan"])
            proof = proof_form.cleaned_data["proof"]
            payment = Payment(guardian=guardian, plan=chosen, amount=chosen.price, proof_mime=proof.content_type)
            payment.proof.save(random_upload_name(proof.content_type), proof, save=False)
            payment.save()
            messages.success(request, "Naipadala na ang patunay ng bayad. Hintayin ang pag-apruba ng admin.")
            return redirect('plan_transactions')

    context = {
        "current_plan": plan,
        # How many children and family voices the guardian has, of how many the plan allows, shown on its card.
        "child_slots": child_slots(guardian, plan),
        "voice_slots": family_voice_slots(guardian, plan),
        "paid_until": paid_until(guardian),
        "pending_payment": waiting,
        # The plans on offer, and the guardian's own when it is no longer offered:
        # it stays theirs until their paid time ends, but cannot be paid for again.
        "plans": [
            {
                "plan": shown,
                "is_current": shown.pk == plan.pk,
                # A plan that costs something is paid for before it starts, and paid again to keep it.
                "needs_payment": not shown.is_free and shown.offered,
            }
            for shown in Plan.objects.filter(Q(offered=True) | Q(pk=plan.pk))
        ],
        # The pay window is for one plan at a time: the one whose button was pressed
        # (plan.js switches it), or after a refused upload the one it was for.
        "pay_plan": next(
            (offered for offered in paid_plans if proof_form.errors and offered.key == request.POST.get("plan")),
            paid_plans[0] if paid_plans else None,
        ),
        "setting": setting,
        "proof_form": proof_form,
        "show_pay_modal": bool(proof_form.errors),
        "max_proof_megabytes": MAX_UPLOAD_SIZE // (1024 * 1024),
    }
    return render(request, 'dashboard/plan/plan.html', context)


@active_nav("plan")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_transactions(request):
    """The guardian's payments and what became of each."""
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    payments = guardian.payments.select_related("plan")

    context = {
        "payments": paginate(payments, request.GET.get("page", 1)),
    }
    return render(request, 'dashboard/plan/transactions.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian, is_administrator)
def view_payment_proof(request, payment_uuid):
    """The picture of a payment, for the guardian who sent it and for admins."""
    payments = Payment.objects.all() if is_administrator(request.user) else Payment.objects.filter(guardian__user=request.user)
    payment = get_object_or_404(payments, uuid=payment_uuid)
    response = FileResponse(payment.proof.open('rb'), content_type=payment.proof_mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_guardian, is_administrator)
def view_gcash_qr(request):
    """The GCash QR code guardians pay with, set by an admin on System Settings > General."""
    setting = SiteSetting.load()
    if not setting.has_gcash_qr:
        raise Http404()
    response = FileResponse(setting.gcash_qr.open('rb'), content_type=setting.gcash_qr_mime or "application/octet-stream")
    # Short, so that a replaced QR code shows soon; the page's link carries a version too.
    response["Cache-Control"] = "private, max-age=300"
    return response
