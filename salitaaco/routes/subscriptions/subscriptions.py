"""
The admin's view of subscriptions: how many guardians are on each plan, what
was earned this month, and the plans themselves, which the admin edits here.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from salitaaco.forms.subscriptions.plan import PlanForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.plan import Plan
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.plans import revenue_this_month, subscriber_counts

FIELDS = ["name", "price", "features", "offered"]


def plan_form(plan, data=None):
    """The form of one plan, its fields named after the plan so that every plan's form can be on the page."""
    return PlanForm(
        data,
        prefix=plan.key,
        include_price=not plan.is_default,
        initial={field: getattr(plan, field) for field in FIELDS},
    )


@active_nav("subscriptions")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_subscriptions(request):
    plans = list(Plan.objects.all())
    forms = {plan.key: plan_form(plan) for plan in plans}

    if request.method == "POST":
        plan = next((plan for plan in plans if plan.key == request.POST.get("plan_form")), None)
        if plan is not None:
            forms[plan.key] = plan_form(plan, request.POST)
            if forms[plan.key].is_valid():
                for field in FIELDS:
                    if field in forms[plan.key].cleaned_data:
                        setattr(plan, field, forms[plan.key].cleaned_data[field])
                plan.save()
                messages.success(request, f"Naka-save na ang {plan.name}.")
                return redirect('subscriptions')

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
        "plans": [
            {"plan": plan, "subscribers": counts.get(plan.key, 0), "form": forms[plan.key]}
            for plan in plans
        ],
    }
    return render(request, 'dashboard/subscriptions/subscriptions.html', context)
