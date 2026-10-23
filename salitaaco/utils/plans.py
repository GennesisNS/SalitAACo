import calendar

from django.db import transaction
from django.db.models import Count, Max, Sum
from django.utils import timezone

from salitaaco.defaults.plans import APPROVED, DEFAULT_PLAN, FREE_FAMILY_VOICE_LIMIT, PAID_MONTHS, PENDING, REJECTED
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan


def offered_plans():
    """The plans guardians can choose from, in their order."""
    return Plan.objects.filter(offered=True)


def default_plan():
    return Plan.objects.get(key=DEFAULT_PLAN)


def add_months(moment, months):
    """
    The same day and time `months` later. On a shorter month it is that
    month's last day: a month after 31 January is 28 (or 29) February.
    """
    moment = timezone.localtime(moment)
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def active_payment(guardian):
    """The approved payment that has the guardian on a paid plan right now, or None."""
    now = timezone.now()
    return (
        Payment.objects.filter(guardian=guardian, status=APPROVED, starts_at__lte=now, ends_at__gt=now)
        .select_related("plan")
        .order_by("starts_at")
        .first()
    )


def current_plan(guardian):
    """The plan a guardian is on: the one their payment covers right now, or the default plan."""
    payment = active_payment(guardian)
    return payment.plan if payment else default_plan()


def child_slots(guardian, plan=None):
    """
    How many child accounts the guardian has and their plan (`plan`, when
    already looked up) allows, whether they can make another, and when they
    cannot, what they are told: the plan on offer that allows more, if there
    is one, or to delete a child first. A guardian over the limit keeps every child.
    """
    plan = plan or current_plan(guardian)
    count = guardian.children.count()
    can_add = count < plan.child_limit
    # A paid plan to get, never the free one to go back to.
    roomier = (
        offered_plans().exclude(pk=plan.pk).filter(price__gt=0, child_limit__gt=plan.child_limit)
        .order_by("child_limit", "position").first()
    )
    if can_add:
        message = ""
    elif roomier is not None:
        message = (f"Hanggang {plan.child_limit} na account ng bata lang sa {plan.name}. "
                   f"Kunin ang {roomier.name} para makapagdagdag ng hanggang {roomier.child_limit}.")
    else:
        message = (f"Naabot mo na ang {plan.child_limit} na account ng bata sa {plan.name}. "
                   "Magbura muna ng isa para makapagdagdag ng bago.")
    return {
        "count": count,
        "limit": plan.child_limit,
        "can_add": can_add,
        "message": message,
        "upgrade": roomier if not can_add else None,
    }


def family_voice_limit(guardian):
    """How many family voices the guardian can have: a few on a free plan, None (no limit) on a paid one."""
    return FREE_FAMILY_VOICE_LIMIT if current_plan(guardian).is_free else None


def paid_until(guardian):
    """
    When the guardian's paid time ends, counting payments approved ahead of
    time; None when they have no paid time left.
    """
    return Payment.objects.filter(
        guardian=guardian, status=APPROVED, ends_at__gt=timezone.now(),
    ).aggregate(end=Max("ends_at"))["end"]


def pending_payment(guardian):
    """The guardian's payment still waiting for an admin, or None. A guardian has at most one."""
    return Payment.objects.filter(guardian=guardian, status=PENDING).select_related("plan").first()


def approve_payment(payment, admin_user):
    """
    Approve a pending payment. Its months start now, or, when the guardian
    still has paid time, where that time ends, so paying early loses nothing.
    Returns False, changing nothing, when the payment is no longer pending.
    """
    with transaction.atomic():
        # Lock the guardian, so that two approvals at once cannot both start from the same end.
        GuardianAccount.objects.select_for_update().get(pk=payment.guardian_id)
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if not payment.is_pending:
            return False

        now = timezone.now()
        starts_at = max(now, paid_until(payment.guardian) or now)
        payment.status = APPROVED
        payment.reviewed_at = now
        payment.reviewed_by = admin_user
        payment.starts_at = starts_at
        payment.ends_at = add_months(starts_at, PAID_MONTHS)
        payment.save()
    return True


def reject_payment(payment, admin_user, note):
    """
    Reject a pending payment, with the reason the guardian is shown. Returns
    False, changing nothing, when the payment is no longer pending.
    """
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if not payment.is_pending:
            return False

        payment.status = REJECTED
        payment.note = note
        payment.reviewed_at = timezone.now()
        payment.reviewed_by = admin_user
        payment.save()
    return True


def subscriber_counts():
    """How many guardians are on each plan right now, by plan key."""
    now = timezone.now()
    paying = (
        Payment.objects.filter(status=APPROVED, starts_at__lte=now, ends_at__gt=now)
        .values("plan__key")
        .annotate(guardians=Count("guardian", distinct=True))
    )
    counts = {row["plan__key"]: row["guardians"] for row in paying}
    counts[DEFAULT_PLAN] = GuardianAccount.objects.count() - sum(counts.values())
    return counts


def revenue_this_month():
    """The pesos of the payments approved since the start of this month."""
    month_start = timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return Payment.objects.filter(
        status=APPROVED, reviewed_at__gte=month_start,
    ).aggregate(total=Sum("amount"))["total"] or 0


def revenue_by_month(months=6):
    """
    The pesos approved in each of the last `months` months, this one last,
    with the months that had none: [{"month": first day, "total": pesos}].
    """
    this_month = timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first = add_months(this_month, -(months - 1))
    # Grouped here, not in SQL: date functions on MySQL need its time zone tables loaded.
    totals = {}
    for reviewed_at, amount in Payment.objects.filter(status=APPROVED, reviewed_at__gte=first).values_list("reviewed_at", "amount"):
        moment = timezone.localtime(reviewed_at)
        totals[(moment.year, moment.month)] = totals.get((moment.year, moment.month), 0) + amount
    return [
        {"month": month.date(), "total": totals.get((month.year, month.month), 0)}
        for month in (add_months(first, offset) for offset in range(months))
    ]


def payment_counts():
    """How many payments are waiting, approved and rejected, by status."""
    return dict(Payment.objects.values_list("status").annotate(count=Count("payment_id")))
