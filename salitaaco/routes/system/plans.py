"""
System Settings > Mga Plano: the plans guardians can be on, which an admin
adds, edits, offers or not, and deletes here. The rules:

- The default plan (Free) is always free and always offered, and is never deleted.
- A plan that is not offered cannot be chosen any more, but stays with whoever
  is on it until their paid time ends.
- A new price is for the payments that follow; payments already sent keep theirs.
- A plan that has payments is not deleted, as they are its record; it is
  taken off offer instead.

Below the plans, "Mga Limit ng Plano": how many tiles and custom boards of
their own a guardian can make on Free and on a paid plan (SiteSetting).
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from salitaaco.forms.subscriptions.plan import PlanForm
from salitaaco.forms.system.plan_limits import PlanLimitsForm
from salitaaco.models.plan import Plan
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)

FIELDS = ["name", "price", "features", "offered"]
NEW_PLAN = "new"
LIMIT_FIELDS = ["free_word_limit", "free_board_limit", "plus_word_limit", "plus_board_limit"]


def plan_form(plan, plans, data=None):
    """The form of one plan, its fields named after the plan so that every plan's form can be on the page."""
    return PlanForm(
        data,
        prefix=plan.key,
        include_price=not plan.is_default,
        taken_names=[other.name for other in plans if other.pk != plan.pk],
        initial={field: getattr(plan, field) for field in FIELDS},
    )


def new_plan_key(name):
    """A key for a new plan, from its name, that no plan has (and never the new plan form's prefix)."""
    base = slugify(name)[:14] or "plano"
    key, number = base, 2
    while key == NEW_PLAN or Plan.objects.filter(key=key).exists():
        key = f"{base}-{number}"
        number += 1
    return key


@active_nav("system_plans")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_plans(request):
    plans = list(Plan.objects.annotate(payment_count=Count("payments")))
    forms = {plan.key: plan_form(plan, plans) for plan in plans}
    every_name = [plan.name for plan in plans]
    new_plan_form = PlanForm(prefix=NEW_PLAN, initial={"offered": True})
    setting = SiteSetting.load()
    limits_form = PlanLimitsForm(initial={field: getattr(setting, field) for field in LIMIT_FIELDS})

    if request.method == "POST":
        if "limits_form" in request.POST:
            limits_form = PlanLimitsForm(request.POST)
            if limits_form.is_valid():
                for field in LIMIT_FIELDS:
                    setattr(setting, field, limits_form.cleaned_data[field])
                setting.save()
                logger.info("Admin %s changed the plan limits", request.user.username)
                messages.success(request, "Naka-save na ang mga limit ng Free at Plus.")
                return redirect(f"{reverse('system_plans')}#limits")

        elif "new_plan_form" in request.POST:
            new_plan_form = PlanForm(request.POST, prefix=NEW_PLAN, taken_names=every_name)
            if new_plan_form.is_valid():
                last = Plan.objects.aggregate(last=Max("position"))["last"] or 0
                plan = Plan.objects.create(
                    key=new_plan_key(new_plan_form.cleaned_data["name"]),
                    position=last + 1,
                    **{field: new_plan_form.cleaned_data[field] for field in FIELDS},
                )
                logger.info("Admin %s added the plan %s", request.user.username, plan.key)
                messages.success(request, f"Naidagdag na ang {plan.name}.")
                return redirect('system_plans')

        else:
            plan = next((plan for plan in plans if plan.key == request.POST.get("plan_form")), None)
            if plan is not None:
                forms[plan.key] = plan_form(plan, plans, request.POST)
                if forms[plan.key].is_valid():
                    for field in FIELDS:
                        if field in forms[plan.key].cleaned_data:
                            setattr(plan, field, forms[plan.key].cleaned_data[field])
                    plan.save()
                    messages.success(request, f"Naka-save na ang {plan.name}.")
                    return redirect('system_plans')

    context = {
        "plans": [
            {
                "plan": plan,
                "form": forms[plan.key],
                "can_delete": not plan.is_default and not plan.payment_count,
            }
            for plan in plans
        ],
        "new_plan_form": new_plan_form,
        "show_new_plan_modal": bool(new_plan_form.errors),
        "limits_form": limits_form,
        # The limits are Free's and every paid plan's: named here as the plans are.
        "free_plan": next((plan for plan in plans if plan.is_default), None),
        "paid_plans": [plan for plan in plans if not plan.is_default],
    }
    return render(request, 'dashboard/system/plans.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def remove_plan(request, plan_id):
    plan = get_object_or_404(Plan, plan_id=plan_id)
    if plan.is_default:
        messages.error(request, "Hindi mabubura ang libreng plano: dito napupunta ang mga walang bayad na plano.")
    elif plan.payments.exists():
        messages.error(request, f"May mga bayad na para sa {plan.name}, kaya hindi ito mabubura. I-off na lang ang “Iniaalok”.")
    else:
        name = plan.name
        plan.delete()
        logger.info("Admin %s deleted the plan %s", request.user.username, name)
        messages.success(request, f"Nabura na ang {name}.")
    return redirect('system_plans')
