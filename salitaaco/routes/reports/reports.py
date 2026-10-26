from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from salitaaco.defaults.plans import APPROVED, PENDING, REJECTED
from salitaaco.forms.reports.report_tab import ReportTabForm
from salitaaco.models.customization import Customization
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.utils import admin_stats, analytics
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.plans import payment_counts, revenue_by_month, revenue_this_month, subscriber_counts

USAGE_DAYS_SHOWN = 14
REVENUE_MONTHS_SHOWN = 6


def business_numbers():
    """The Negosyo tab: guardians on each plan, the payments by status, and the pesos approved each month."""
    counts = subscriber_counts()
    payments = payment_counts()
    months = revenue_by_month(REVENUE_MONTHS_SHOWN)
    highest = max((row["total"] for row in months), default=0)
    for row in months:
        row["width"] = analytics.bar_width(row["total"], highest)
        row["pesos"] = f"₱{row['total']:,}"
    total = Payment.objects.filter(status=APPROVED).aggregate(total=Sum("amount"))["total"] or 0
    return {
        "plans": [{"name": plan.name, "guardians": counts.get(plan.key, 0)} for plan in Plan.objects.all()],
        "revenue_this_month": f"₱{revenue_this_month():,}",
        "revenue_total": f"₱{total:,}",
        "pending": payments.get(PENDING, 0),
        "approved": payments.get(APPROVED, 0),
        "rejected": payments.get(REJECTED, 0),
        "months": months,
    }


def reports_context(tab):
    """Everything the page shows, whichever tab is open."""
    tab_form = ReportTabForm()
    return {
        "tabs": [{"value": value, "label": label, "active": value == tab} for value, label in tab_form.fields["tab"].choices],
        "tab": tab,
        "overview": analytics.overview(),
        # Growth
        "signups": analytics.signups_by_day(),
        "accounts_by_role": admin_stats.accounts_by_role(),
        # Usage
        "top_words": analytics.top_words(),
        "board_opens": admin_stats.board_opens(),
        "usage_by_day": admin_stats.usage_by_day(USAGE_DAYS_SHOWN),
        "customized_tiles": Customization.objects.count(),
        "family_voices": FamilyVoice.objects.count(),
        # Retention
        "retention": admin_stats.retention(),
        # Business
        "business": business_numbers(),
    }


@active_nav("reports")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_reports(request):
    """
    Analytics at Ulat: the numbers in more depth, a tab at a time. Reports to
    keep and download are made on Mga Ulat (routes/generated_reports/).
    """
    tab = ReportTabForm(request.GET or None).chosen()
    return render(request, 'dashboard/reports/reports.html', reports_context(tab))
