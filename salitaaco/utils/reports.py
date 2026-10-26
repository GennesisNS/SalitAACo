"""
What the reports on Mga Ulat say, made from the database for some days, and
written as a CSV or as a page to print (routes/generated_reports/).

A report is a dict: its title, the days it covers, its key numbers
("summary": [label, value] pairs), and its tables ("sections": each with a
title, the column headers, the rows and an optional note). The CSV and the
printed page are both drawn from it, so they always say the same.

Children are only ever counted: no table lists a child, their name, their
username, their rating or anything they wrote.
"""
import csv
from datetime import datetime, time, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum
from django.utils import dateformat, timezone

from salitaaco.defaults.plans import APPROVED, PENDING, REJECTED
from salitaaco.defaults.reports import (
    FEEDBACK,
    MESSAGE_COLUMNS,
    PAYMENT_COLUMNS,
    PAYMENTS,
    RATING_COLUMNS,
    REPORT_TYPES,
    USER_COLUMNS,
    USERS,
)
from salitaaco.models.payment import Payment
from salitaaco.models.plan import Plan
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.utils.account import find_user_account
from salitaaco.utils.plans import current_plan

NOTHING = "—"


def pesos(amount):
    return f"₱{amount:,}"


def day(moment):
    """A moment as the day and time in the project's time zone, or a dash when there is none."""
    return timezone.localtime(moment).strftime("%Y-%m-%d %H:%M") if moment else NOTHING


def long_date(value):
    return dateformat.format(value, "F j, Y")


def date_range(start_date, end_date):
    """The moments from the start of the first day to the end of the last, in the project's time zone."""
    zone = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(start_date, time.min), zone)
    end = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min), zone)
    return start, end


def headers(columns, choices):
    """The labels of the chosen columns, in the order the choices list them."""
    return [label for value, label in choices if value in columns]


def pick(values, columns, choices):
    """One row: the values of the chosen columns, in the order the choices list them."""
    return [values[value] for value, _ in choices if value in columns]


def report(report_type, start_date, end_date, summary, sections):
    return {
        "title": f"Ulat: {dict(REPORT_TYPES)[report_type]}",
        "subheading": f"{long_date(start_date)} – {long_date(end_date)}",
        "summary": summary,
        "sections": sections,
    }


def users_report(start_date, end_date, columns):
    """The accounts made in the days: how many of each kind, and a table of the guardians' and admins'."""
    start, end = date_range(start_date, end_date)
    joined = User.objects.filter(date_joined__gte=start, date_joined__lt=end)
    listed = (
        joined.filter(child_account__isnull=True)
        .select_related("admin_account", "guardian_account")
        .order_by("date_joined", "pk")
    )

    rows = []
    for user in listed:
        account = find_user_account(user)
        guardian = getattr(user, "guardian_account", None)
        rows.append(pick({
            "username": user.username,
            "role": account.ROLE_LABEL if account else NOTHING,
            "date_joined": day(user.date_joined),
            "last_login": day(user.last_login),
            "status": "Aktibo" if user.is_active else "Hindi aktibo",
            "plan": current_plan(guardian).name if guardian else NOTHING,
            "children": guardian.children.count() if guardian else NOTHING,
        }, columns, USER_COLUMNS))

    summary = [
        ["Mga bagong account", joined.count()],
        ["Bagong tagapag-alaga", joined.filter(guardian_account__isnull=False).count()],
        ["Bagong bata", joined.filter(child_account__isnull=False).count()],
        ["Bagong admin", joined.filter(admin_account__isnull=False).count()],
        ["Hindi aktibo sa mga bago", joined.filter(is_active=False).count()],
        ["Lahat ng account ngayon", User.objects.count()],
    ]
    sections = [{
        "title": "Mga account ng tagapag-alaga at admin",
        "headers": headers(columns, USER_COLUMNS),
        "rows": rows,
        "note": "Hindi nakalista ang mga account ng bata; kasama lang sila sa bilang.",
    }]
    return report(USERS, start_date, end_date, summary, sections)


def payments_report(start_date, end_date, columns):
    """The payments sent in the days: by status and by plan, the money approved, and each payment."""
    start, end = date_range(start_date, end_date)
    payments = (
        Payment.objects.filter(created_at__gte=start, created_at__lt=end)
        .select_related("guardian__user", "plan", "reviewed_by")
        .order_by("created_at", "payment_id")
    )
    approved = payments.filter(status=APPROVED)

    by_plan = []
    for plan in Plan.objects.all():
        of_plan = payments.filter(plan=plan)
        approved_of_plan = of_plan.filter(status=APPROVED)
        by_plan.append([
            plan.name, of_plan.count(), approved_of_plan.count(),
            pesos(approved_of_plan.aggregate(total=Sum("amount"))["total"] or 0),
        ])

    rows = [
        pick({
            "payment_id": str(payment.uuid).split("-")[0],
            "date": day(payment.created_at),
            "guardian": payment.guardian.user.username,
            "plan": payment.plan.name,
            "amount": pesos(payment.amount),
            "status": payment.get_status_display(),
            "reviewed_at": day(payment.reviewed_at),
            "reviewed_by": payment.reviewed_by.username if payment.reviewed_by else NOTHING,
            "period": (f"{timezone.localtime(payment.starts_at):%Y-%m-%d} hanggang {timezone.localtime(payment.ends_at):%Y-%m-%d}"
                       if payment.starts_at and payment.ends_at else NOTHING),
            "note": payment.note or NOTHING,
        }, columns, PAYMENT_COLUMNS)
        for payment in payments
    ]

    summary = [
        ["Bilang ng bayad", payments.count()],
        ["Naghihintay", payments.filter(status=PENDING).count()],
        ["Aprubado", approved.count()],
        ["Tinanggihan", payments.filter(status=REJECTED).count()],
        ["Kita mula sa mga aprubado", pesos(approved.aggregate(total=Sum("amount"))["total"] or 0)],
    ]
    sections = [
        {
            "title": "Ayon sa plano",
            "headers": ["Plano", "Bilang ng bayad", "Aprubado", "Kita"],
            "rows": by_plan,
            "note": "",
        },
        {
            "title": "Mga bayad",
            "headers": headers(columns, PAYMENT_COLUMNS),
            "rows": rows,
            "note": "",
        },
    ]
    return report(PAYMENTS, start_date, end_date, summary, sections)


def feedback_report(start_date, end_date, rating_columns, message_columns):
    """The ratings given (or changed) and the support messages sent in the days."""
    start, end = date_range(start_date, end_date)
    ratings = Rating.objects.filter(updated_at__gte=start, updated_at__lt=end)
    messages = (
        SupportMessage.objects.filter(created_at__gte=start, created_at__lt=end)
        .select_related("guardian__user")
        .order_by("created_at", "support_message_id")
    )
    average = ratings.aggregate(average=Avg("rating"))["average"]
    by_stars = dict(ratings.values_list("rating").annotate(count=Count("rating_id")))

    rating_rows = [
        pick({
            "date": day(rating.updated_at),
            "username": rating.user.username,
            "stars": rating.stars,
            "comment": rating.comment or NOTHING,
        }, rating_columns, RATING_COLUMNS)
        for rating in ratings.filter(user__child_account__isnull=True).select_related("user").order_by("updated_at", "rating_id")
    ]
    message_rows = [
        pick({
            "date": day(message.created_at),
            "username": message.guardian.user.username,
            "message": message.message,
            "status": "Naayos na" if message.is_resolved else "Bukas",
            "resolved_at": day(message.resolved_at),
        }, message_columns, MESSAGE_COLUMNS)
        for message in messages
    ]

    summary = [
        ["Bilang ng rating", ratings.count()],
        ["Average na rating", f"{average:.2f} sa 5" if average is not None else NOTHING],
        ["Mga mensahe sa suporta", messages.count()],
        ["Bukas pa", messages.filter(resolved_at__isnull=True).count()],
        ["Naayos na", messages.filter(resolved_at__isnull=False).count()],
    ]
    sections = [
        {
            "title": "Ayon sa bituin",
            "headers": ["Bituin", "Bilang"],
            "rows": [[f"{stars} ★", by_stars.get(stars, 0)] for stars in range(Rating.MAX_RATING, Rating.MIN_RATING - 1, -1)],
            "note": "",
        },
        {
            "title": "Mga rating",
            "headers": headers(rating_columns, RATING_COLUMNS),
            "rows": rating_rows,
            "note": "Kasama sa bilang ang mga rating ng bata, pero hindi sila nakalista.",
        },
        {
            "title": "Mga mensahe sa suporta",
            "headers": headers(message_columns, MESSAGE_COLUMNS),
            "rows": message_rows,
            "note": "",
        },
    ]
    return report(FEEDBACK, start_date, end_date, summary, sections)


def report_csv(content, details):
    """
    A report as a CSV file, as MYO writes them: who made it and for which
    days, then the key numbers, then each table under its title.
    `details` are [label, value] pairs about the report itself.
    """
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([content["title"]])
    writer.writerows(details)
    writer.writerow([])
    writer.writerow(["MGA PANGUNAHING BILANG"])
    writer.writerow(["Sukatan", "Halaga"])
    writer.writerows(content["summary"])
    for section in content["sections"]:
        writer.writerow([])
        writer.writerow([section["title"].upper()])
        writer.writerow(section["headers"])
        writer.writerows(section["rows"])
        if section["note"]:
            writer.writerow([section["note"]])
    # The mark at the start tells spreadsheet programs the file is UTF-8, so "ñ" and "₱" survive.
    return "﻿" + buffer.getvalue()
