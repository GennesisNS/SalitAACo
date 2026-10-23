import csv
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from salitaaco.defaults.plans import APPROVED, PENDING, REJECTED
from salitaaco.forms.reports.export_report import SIGNUPS, USAGE, WORDS, ExportReportForm
from salitaaco.forms.reports.report_tab import EXPORT, ReportTabForm
from salitaaco.models.customization import Customization
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.word_usage import WordUsage
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


def reports_context(tab, export_form):
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
        # Reports
        "export_form": export_form,
    }


@active_nav("reports")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_reports(request):
    """Analytics at Ulat: the numbers in more depth, a tab at a time, and the reports to download."""
    tab = ReportTabForm(request.GET or None).chosen()
    return render(request, 'dashboard/reports/reports.html', reports_context(tab, ExportReportForm()))


def in_range(day, date_from, date_to):
    return (date_from is None or day >= date_from) and (date_to is None or day <= date_to)


def signups_rows(date_from, date_to):
    # Grouped here, not in SQL: date functions on MySQL need its time zone tables loaded.
    joined = Counter(timezone.localtime(moment).date() for moment in User.objects.values_list("date_joined", flat=True))
    days = sorted(day for day in joined if in_range(day, date_from, date_to))
    return ["araw", "mga_sign_up"], [[day.isoformat(), joined[day]] for day in days]


def usage_rows(date_from, date_to):
    usages = DailyUsage.objects.all()
    if date_from:
        usages = usages.filter(day__gte=date_from)
    if date_to:
        usages = usages.filter(day__lte=date_to)
    totals = {}
    for row in usages.values("day", "kind").annotate(total=Sum("use_count")):
        totals.setdefault(row["day"], {})[row["kind"]] = row["total"]
    return ["araw", "mga_pindot", "mga_bukas_ng_board"], [
        [day.isoformat(), kinds.get(DailyUsage.WORD, 0), kinds.get(DailyUsage.BOARD, 0)]
        for day, kinds in sorted(totals.items())
    ]


def words_rows(date_from, date_to):
    """
    Every word and how often it was tapped. Over all time it is each word's
    total; with dates it is counted from the days, which began later. A
    family's own tiles (names, places at home) are left out, as on the page.
    """
    if date_from is None and date_to is None:
        usages = analytics.family_tile_taps(WordUsage.objects.all(), "word")
        totals = usages.values("word").annotate(total=Sum("use_count")).order_by("-total", "word")
        return ["salita", "mga_pindot"], [[row["word"], row["total"]] for row in totals]

    usages = analytics.family_tile_taps(DailyUsage.objects.filter(kind=DailyUsage.WORD), "name")
    if date_from:
        usages = usages.filter(day__gte=date_from)
    if date_to:
        usages = usages.filter(day__lte=date_to)
    totals = usages.values("name").annotate(total=Sum("use_count")).order_by("-total", "name")
    return ["salita", "mga_pindot"], [[row["name"], row["total"]] for row in totals]


REPORTS = {SIGNUPS: signups_rows, USAGE: usage_rows, WORDS: words_rows}


@active_nav("reports")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def export_report(request):
    """
    A report as a CSV file. Reports hold counts only: no names, no usernames
    and nothing anyone said with the board.
    """
    export_form = ExportReportForm(request.GET)
    if not export_form.is_valid():
        # Back on the reports tab, with what is wrong beside the fields.
        return render(request, 'dashboard/reports/reports.html', reports_context(EXPORT, export_form), status=400)

    report = export_form.cleaned_data['report']
    header, rows = REPORTS[report](export_form.cleaned_data['date_from'], export_form.cleaned_data['date_to'])

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="salitaaco-{report}-{timezone.localdate().isoformat()}.csv"'
    # The mark at the start tells spreadsheet programs the file is UTF-8, so "ñ" and emoji survive.
    response.write("﻿")
    writer = csv.writer(response)
    writer.writerow(header)
    writer.writerows(rows)
    return response
