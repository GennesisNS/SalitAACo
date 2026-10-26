"""
Mga Ulat: the reports admins make, after MYO's Generate Reports. The page
lists every report made, newest first; "＋ Gumawa ng ulat" opens a window to
choose the kind of report (users, payments, feedback), the file (a CSV, or a
page to print or save as PDF), the days and the columns.

A report is made from the database once, when it is made, and kept as a file
(utils/reports.py says what each one holds), so opening it later shows it as
it was. Reports list guardians' and admins' usernames, never a child.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from salitaaco.defaults.reports import CSV, FEEDBACK, PAYMENTS, REPORT_TYPES, USERS
from salitaaco.forms.generated_reports.feedback_report import FeedbackReportForm
from salitaaco.forms.generated_reports.payments_report import PaymentsReportForm
from salitaaco.forms.generated_reports.users_report import UsersReportForm
from salitaaco.models.generated_report import GeneratedReport
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.pagination import paginate
from salitaaco.utils.perms_check import is_administrator, multi_user_test
from salitaaco.utils.reports import day, feedback_report, payments_report, report_csv, users_report

logger = logging.getLogger(__name__)

# Each kind of report: its form, whose fields are named after the kind so that
# all three can be on the page, and the name of the button that sends it.
REPORT_FORMS = {
    USERS: UsersReportForm,
    PAYMENTS: PaymentsReportForm,
    FEEDBACK: FeedbackReportForm,
}


def form_button(report_type):
    return f"{report_type}_report_form"


def report_content(report_type, data):
    """What a report of this kind says, for the form's days and columns."""
    if report_type == USERS:
        return users_report(data["start_date"], data["end_date"], data["columns"])
    if report_type == PAYMENTS:
        return payments_report(data["start_date"], data["end_date"], data["columns"])
    return feedback_report(data["start_date"], data["end_date"], data["rating_columns"], data["message_columns"])


def make_report(report_type, form, user):
    """
    Make a report from a valid form and keep it, as a CSV or as a page to
    print. The row is saved first, for the number in its report ID.
    """
    data = form.cleaned_data
    content = report_content(report_type, data)
    with transaction.atomic():
        generated = GeneratedReport.objects.create(
            report_type=report_type,
            file_type=data["file_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            generated_by=user,
        )
        made_at = day(generated.created_at)
        if data["file_type"] == CSV:
            details = [
                ["Report ID", generated.report_id],
                ["Ginawa ni", user.username],
                ["Saklaw ng petsa", content["subheading"]],
                ["Petsa ginawa", made_at],
            ]
            text, extension = report_csv(content, details), "csv"
        else:
            text = render_to_string("reports/printable.html", {
                "content": content,
                "report_id": generated.report_id,
                "generated_by": user.username,
                "made_at": made_at,
            })
            extension = "html"
        generated.file.save(f"{generated.report_id}.{extension}", ContentFile(text.encode("utf-8")))
    return generated


@active_nav("generated_reports")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_generated_reports(request):
    forms = {report_type: form_class(prefix=report_type) for report_type, form_class in REPORT_FORMS.items()}
    open_type = None

    if request.method == "POST":
        report_type = next((kind for kind in REPORT_FORMS if form_button(kind) in request.POST), None)
        if report_type is not None:
            form = forms[report_type] = REPORT_FORMS[report_type](request.POST, prefix=report_type)
            if form.is_valid():
                generated = make_report(report_type, form, request.user)
                logger.info("Admin %s made the report %s", request.user.username, generated.report_id)
                messages.success(request, f"Nagawa na ang ulat na {generated.report_id}. Buksan o i-download ito sa listahan.")
                return redirect('generated_reports')
            # The window opens again on this kind, to say what is wrong.
            open_type = report_type

    labels = dict(REPORT_TYPES)
    context = {
        "reports": paginate(GeneratedReport.objects.select_related("generated_by"), request.GET.get("page", 1)),
        "report_forms": [
            {"type": report_type, "label": labels[report_type], "form": form, "button": form_button(report_type)}
            for report_type, form in forms.items()
        ],
        "open_type": open_type,
        "chosen_type": open_type or USERS,
    }
    return render(request, 'dashboard/generated_reports/generated_reports.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_generated_report(request, report_uuid):
    """A report as it was made: a CSV to download, or the page to print or save as PDF."""
    generated = get_object_or_404(GeneratedReport, uuid=report_uuid)
    if generated.file_type == CSV:
        response = FileResponse(
            generated.file.open('rb'), content_type="text/csv; charset=utf-8", as_attachment=True,
            filename=f"{generated.report_id}.csv",
        )
    else:
        response = FileResponse(generated.file.open('rb'), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "private, no-store"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def remove_generated_report(request, report_uuid):
    """Delete a report and its file, for good: a report keeps usernames, which an admin may want gone."""
    generated = get_object_or_404(GeneratedReport, uuid=report_uuid)
    report_id = generated.report_id
    generated.delete_file()
    generated.delete()
    logger.info("Admin %s deleted the report %s", request.user.username, report_id)
    messages.success(request, f"Nabura na ang ulat na {report_id}.")
    return redirect('generated_reports')
