import csv
from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.urls import reverse
from django.utils import timezone

from salitaaco.defaults.reports import MESSAGE_COLUMNS, PAYMENT_COLUMNS, RATING_COLUMNS, USER_COLUMNS
from salitaaco.forms.generated_reports.users_report import UsersReportForm
from salitaaco.models.generated_report import GeneratedReport
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import approve_payment, reject_payment


class GeneratedReportsBase(UserBase):
    """
    Nanay is Miguel's guardian, on Plus. Every account was made today, and
    Ana was made 40 days ago, so that a report of the last week leaves her out.
    """
    url = reverse("generated_reports")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        approve_payment(make_payment(cls.nanay), cls.developer)
        User.objects.filter(pk=cls.ana.pk).update(date_joined=timezone.now() - timedelta(days=40))
        cls.today = timezone.localdate()

    def make(self, report_type, file_type="csv", days=7, **fields):
        """Send the form of one kind of report, every column chosen unless `fields` say otherwise."""
        columns = {
            "users": {"columns": [value for value, _ in USER_COLUMNS]},
            "payments": {"columns": [value for value, _ in PAYMENT_COLUMNS]},
            "feedback": {
                "rating_columns": [value for value, _ in RATING_COLUMNS],
                "message_columns": [value for value, _ in MESSAGE_COLUMNS],
            },
        }[report_type]
        data = {
            "file_type": file_type,
            "start_date": (self.today - timedelta(days=days)).isoformat(),
            "end_date": self.today.isoformat(),
            **columns,
            **fields,
        }
        return self.client.post(self.url, {f"{report_type}_report_form": "", **{f"{report_type}-{key}": value for key, value in data.items()}})

    def text_of(self, report):
        with report.file.open("rb") as file:
            return file.read().decode("utf-8-sig")

    def csv_rows(self, report):
        return list(csv.reader(StringIO(self.text_of(report))))


class MgaUlatPageTest(GeneratedReportsBase):
    def test_only_admins_open_it_and_it_is_beside_analytics_in_the_sidebar(self):
        self.assertTrue(self.client.get(self.url).url.startswith("/login/"))
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.make("users")
        self.assertFalse(GeneratedReport.objects.exists())

        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        items = [item["id"] for category in response.context["navigation_items"] for item in category["items"]]
        self.assertEqual(items[items.index("reports") + 1], "generated_reports")
        self.assertContains(response, 'data-open-modal="new-report">＋ Gumawa ng ulat</button>')
        self.assertContains(response, "Wala pang nagagawang ulat.")
        # The window has the three kinds of report, each with its form.
        for report_type in ["users", "payments", "feedback"]:
            self.assertContains(response, f'data-report-form="{report_type}"')
            self.assertContains(response, f'name="{report_type}_report_form"')

    def test_a_report_is_listed_newest_first_and_can_be_deleted(self):
        self.login_as("developer")
        self.assertRedirects(self.make("users"), self.url)
        self.make("payments", file_type="printable")
        first, second = GeneratedReport.objects.order_by("created_at", "generated_report_id")
        self.assertEqual(messages_of(self.client.get(self.url))[-1],
                         f"Nagawa na ang ulat na {second.report_id}. Buksan o i-download ito sa listahan.")

        response = self.client.get(self.url)
        self.assertEqual(list(response.context["reports"]), [second, first])
        self.assertContains(response, f'href="{reverse("view_generated_report", args=[first.uuid])}">I-download</a>')
        self.assertContains(response, f'href="{reverse("view_generated_report", args=[second.uuid])}" target="_blank" rel="noopener">Buksan</a>')
        self.assertContains(response, "@developer")
        self.assertContains(response, f'<span class="reportId">{first.report_id}</span>')

        name = first.file.name
        self.assertEqual(self.client.get(reverse("remove_generated_report", args=[first.uuid])).status_code, 405)
        response = self.client.post(reverse("remove_generated_report", args=[first.uuid]))
        self.assertRedirects(response, self.url)
        self.assertEqual(list(GeneratedReport.objects.all()), [second])
        self.assertFalse(default_storage.exists(name))

    def test_a_form_that_is_not_valid_reopens_the_window_on_its_kind(self):
        self.login_as("developer")
        response = self.make("payments", start_date=self.today.isoformat(), end_date=(self.today - timedelta(days=1)).isoformat())
        self.assertContains(response, "Dapat hindi mas maaga ang “Hanggang” kaysa sa “Mula”.")
        self.assertContains(response, 'data-modal="new-report" data-open="true"')
        self.assertContains(response, 'value="payments" checked')

        response = self.make("feedback", rating_columns=[])
        self.assertContains(response, "Pumili kahit isang column.")
        self.assertFalse(GeneratedReport.objects.exists())

    def test_the_form_needs_its_file_and_its_days(self):
        form = UsersReportForm({"columns": ["username"]})
        self.assertEqual(
            (form.errors["start_date"], form.errors["end_date"]),
            (["Ilagay ang petsa ng simula."], ["Ilagay ang petsa ng katapusan."]),
        )
        self.assertEqual(UsersReportForm({"file_type": "pdf", "start_date": "2026-10-01", "end_date": "2026-10-02",
                                          "columns": ["username"]}).errors["file_type"], ["Pumili mula sa listahan."])

    def test_the_report_id_says_its_kind_its_day_and_its_number(self):
        self.login_as("developer")
        for report_type in ["users", "payments", "feedback"]:
            self.make(report_type)
        day = timezone.localdate().strftime("%Y%m%d")
        reports = GeneratedReport.objects.order_by("generated_report_id")
        self.assertEqual(
            [report.report_id for report in reports],
            [f"RPT-{code}-{day}-{report.generated_report_id:04d}" for code, report in zip(["USR", "PAY", "FBK"], reports)],
        )
        # The file is named after it too (a test's numbers start again, so the storage may add to a name it has seen).
        self.assertTrue(reports[0].file.name.startswith(f"reports/{reports[0].report_id}"))
        self.assertTrue(reports[0].file.name.endswith(".csv"))

    def test_only_admins_open_a_report(self):
        self.login_as("developer")
        self.make("users")
        url = reverse("view_generated_report", args=[GeneratedReport.objects.get().uuid])
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 302, username)


class UsersReportTest(GeneratedReportsBase):
    def test_the_csv_counts_every_new_account_and_lists_no_child(self):
        self.login_as("developer")
        self.make("users")
        report = GeneratedReport.objects.get()
        rows = self.csv_rows(report)

        self.assertEqual(rows[0], ["Ulat: Mga User"])
        self.assertEqual(rows[1], ["Report ID", report.report_id])
        self.assertEqual(rows[2], ["Ginawa ni", "developer"])
        summary = {row[0]: row[1] for row in rows if len(row) == 2}
        # Miguel, Nanay and Developer were made this week; Ana 40 days ago.
        self.assertEqual(summary["Mga bagong account"], "3")
        self.assertEqual((summary["Bagong tagapag-alaga"], summary["Bagong bata"], summary["Bagong admin"]), ("1", "1", "1"))
        self.assertEqual(summary["Lahat ng account ngayon"], "4")

        table = rows[rows.index(["MGA ACCOUNT NG TAGAPAG-ALAGA AT ADMIN"]) + 1:]
        self.assertEqual(table[0], [label for _, label in USER_COLUMNS])
        listed = {row[0]: row for row in table[1:] if len(row) == len(USER_COLUMNS)}
        self.assertEqual(set(listed), {"nanay", "developer"})
        self.assertEqual(listed["nanay"][1:2] + listed["nanay"][4:], ["Tagapag-alaga", "Aktibo", "SalitAACo Plus", "1"])
        self.assertEqual(listed["developer"][5:], ["—", "—"])
        # No row is a child's: every username listed is a guardian's or an admin's.
        self.assertNotIn("miguel", self.text_of(report).lower())
        self.assertFalse({"miguel", "ana"} & {row[0] for row in table})

    def test_only_the_chosen_columns(self):
        self.login_as("developer")
        self.make("users", columns=["username", "status"])
        rows = self.csv_rows(GeneratedReport.objects.get())
        self.assertIn(["Username", "Status"], rows)
        self.assertIn(["nanay", "Aktibo"], rows)


class PaymentsReportTest(GeneratedReportsBase):
    def test_the_csv_has_the_money_and_each_payment(self):
        make_payment(self.nanay)
        reject_payment(make_payment(self.nanay), self.developer, "Malabo ang larawan.")

        self.login_as("developer")
        self.make("payments")
        rows = self.csv_rows(GeneratedReport.objects.get())
        summary = {row[0]: row[1] for row in rows if len(row) == 2}
        self.assertEqual((summary["Bilang ng bayad"], summary["Naghihintay"], summary["Aprubado"], summary["Tinanggihan"]),
                         ("3", "1", "1", "1"))
        self.assertEqual(summary["Kita mula sa mga aprubado"], "₱149")
        self.assertIn(["SalitAACo Plus", "3", "1", "₱149"], rows)

        table = rows[rows.index(["MGA BAYAD"]) + 1:]
        self.assertEqual(table[0], [label for _, label in PAYMENT_COLUMNS])
        self.assertEqual([row[5] for row in table[1:4]], ["Aprubado", "Naghihintay", "Tinanggihan"])
        self.assertEqual({row[2] for row in table[1:4]}, {"nanay"})
        self.assertEqual(table[3][7:], ["developer", "—", "Malabo ang larawan."])

    def test_payments_outside_the_days_are_left_out(self):
        self.login_as("developer")
        self.make("payments", start_date=(self.today - timedelta(days=30)).isoformat(),
                  end_date=(self.today - timedelta(days=10)).isoformat())
        summary = {row[0]: row[1] for row in self.csv_rows(GeneratedReport.objects.get()) if len(row) == 2}
        self.assertEqual(summary["Bilang ng bayad"], "0")


class FeedbackReportTest(GeneratedReportsBase):
    def test_a_childs_rating_is_counted_but_never_listed(self):
        Rating.objects.create(user=self.miguel, rating=5, comment="Gusto ko ang mga tile")
        Rating.objects.create(user=self.nanay.user, rating=3, comment="Sana may Ingles")
        SupportMessage.objects.create(guardian=self.nanay, message="Hindi tumunog ang tile.")

        self.login_as("developer")
        self.make("feedback")
        report = GeneratedReport.objects.get()
        rows = self.csv_rows(report)
        summary = {row[0]: row[1] for row in rows if len(row) == 2}
        self.assertEqual((summary["Bilang ng rating"], summary["Average na rating"]), ("2", "4.00 sa 5"))
        self.assertEqual((summary["Mga mensahe sa suporta"], summary["Bukas pa"], summary["Naayos na"]), ("1", "1", "0"))
        self.assertIn(["5 ★", "1"], rows)

        ratings = rows[rows.index(["MGA RATING"]) + 1:rows.index(["MGA MENSAHE SA SUPORTA"])]
        self.assertEqual([row[1:] for row in ratings[1:] if len(row) == 4], [["nanay", "★★★☆☆", "Sana may Ingles"]])
        messages = rows[rows.index(["MGA MENSAHE SA SUPORTA"]) + 1:]
        self.assertEqual(messages[1][1:4], ["nanay", "Hindi tumunog ang tile.", "Bukas"])
        text = self.text_of(report)
        for child in ["miguel", "Gusto ko ang mga tile"]:
            self.assertNotIn(child, text)


class PrintableReportTest(GeneratedReportsBase):
    def test_the_page_to_print_is_kept_and_opened_as_it_was_made(self):
        self.login_as("developer")
        self.make("users", file_type="printable")
        report = GeneratedReport.objects.get()
        self.assertTrue(report.file.name.startswith(f"reports/{report.report_id}"))
        self.assertTrue(report.file.name.endswith(".html"))

        response = self.client.get(reverse("view_generated_report", args=[report.uuid]))
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        page = b"".join(response.streaming_content).decode()
        for text in [
            "<h1>Ulat: Mga User</h1>", f"<code>{report.report_id}</code>", "<code>@developer</code>",
            "<h2>Mga pangunahing bilang</h2>", "<h2>Mga account ng tagapag-alaga at admin</h2>",
            "<td>nanay</td>", "I-print / I-save bilang PDF", 'counter(page) " ng " counter(pages)',
        ]:
            self.assertIn(text, page)
        self.assertNotIn("miguel", page)

        # A later change does not change a report already made.
        User.objects.filter(username="nanay").update(username="nanay2")
        self.assertIn("<td>nanay</td>", b"".join(self.client.get(reverse("view_generated_report", args=[report.uuid])).streaming_content).decode())

    def test_a_csv_is_downloaded(self):
        self.login_as("developer")
        self.make("feedback")
        report = GeneratedReport.objects.get()
        response = self.client.get(reverse("view_generated_report", args=[report.uuid]))
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], f'attachment; filename="{report.report_id}.csv"')
