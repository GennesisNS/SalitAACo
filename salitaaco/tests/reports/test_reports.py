from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from salitaaco.forms.reports.export_report import ExportReportForm
from salitaaco.forms.reports.report_tab import ReportTabForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils import admin_stats


class ReportsBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.today = timezone.localdate()

    def used(self, kind, name, count, days_ago=0, user=None):
        return DailyUsage.objects.create(
            user=user or self.miguel, kind=kind, name=name, use_count=count, day=self.today - timedelta(days=days_ago),
        )


class AdminStatsTest(ReportsBase):
    def test_usage_by_day_covers_the_last_days_with_the_empty_ones(self):
        self.used(DailyUsage.WORD, "kain", 4)
        self.used(DailyUsage.WORD, "inom", 2)
        self.used(DailyUsage.WORD, "kain", 3, days_ago=2, user=self.ana)
        self.used(DailyUsage.BOARD, "Tao", 5, days_ago=2)
        self.used(DailyUsage.WORD, "kain", 99, days_ago=7)

        rows = admin_stats.usage_by_day()

        self.assertEqual([row["date"] for row in rows], [self.today - timedelta(days=offset) for offset in range(6, -1, -1)])
        self.assertEqual([row["taps"] for row in rows], [0, 0, 0, 0, 3, 0, 6])
        self.assertEqual([row["board_opens"] for row in rows], [0, 0, 0, 0, 5, 0, 0])
        self.assertEqual([row["height"] for row in rows], [0, 0, 0, 0, 50, 0, 100])

    def test_board_opens_add_up_every_account(self):
        self.used(DailyUsage.BOARD, "Tao", 5)
        self.used(DailyUsage.BOARD, "Tao", 2, user=self.ana)
        self.used(DailyUsage.BOARD, "Pandiwa", 1, days_ago=40)
        self.used(DailyUsage.WORD, "kain", 50)

        self.assertEqual(admin_stats.board_opens(), [
            {"name": "Tao", "icon": "👪", "count": 7, "width": 100},
            {"name": "Pandiwa", "icon": "🏃", "count": 1, "width": 14},
        ])

    def test_recent_activity_mixes_what_happened_newest_first(self):
        now = timezone.now()
        User.objects.all().update(date_joined=now - timedelta(days=5))
        User.objects.filter(pk=self.ana.pk).update(date_joined=now - timedelta(hours=3))
        message = SupportMessage.objects.create(guardian=self.nanay, message="Tulong po.")
        SupportMessage.objects.filter(pk=message.pk).update(created_at=now - timedelta(hours=1))
        rating = Rating.objects.create(user=self.miguel, rating=4)
        Rating.objects.filter(pk=rating.pk).update(updated_at=now - timedelta(hours=2))

        events = admin_stats.recent_activity(3)

        self.assertEqual([event["kind"] for event in events], ["Mensahe sa suporta", "Rating", "Bagong account"])
        self.assertEqual(events[0]["text"], "mula kay Nanay Rosa")
        self.assertEqual(events[2]["text"], "@ana")

    def test_retention_counts_who_came_back(self):
        now = timezone.now()
        User.objects.all().update(date_joined=now - timedelta(days=20), last_login=None)
        User.objects.filter(pk=self.miguel.pk).update(last_login=now)                       # came back today
        User.objects.filter(pk=self.ana.pk).update(last_login=now - timedelta(days=20))     # only the sign-up login
        for days_ago in [0, 1, 1]:
            DailyUsage.objects.get_or_create(user=self.miguel, kind=DailyUsage.WORD, name=f"salita{days_ago}",
                                             day=self.today - timedelta(days=days_ago), defaults={"use_count": 1})
        self.used(DailyUsage.WORD, "kain", 1, user=self.ana)

        values = {row["metric"]: row["value"] for row in admin_stats.retention()}

        self.assertEqual(values["Bumalik pagkatapos mag-sign up"], "1 sa 4 (25%)")
        self.assertEqual(values["Nag-log in sa huling 7 araw"], "1 sa 4 (25%)")
        self.assertEqual(values["Nag-log in sa huling 30 araw"], "2 sa 4 (50%)")
        self.assertEqual(values["Gumamit ng board nang higit sa isang araw"], "1 sa 2 (50%)")

    def test_retention_with_nobody_using_the_board_has_no_percentage(self):
        values = {row["metric"]: row["value"] for row in admin_stats.retention()}
        self.assertEqual(values["Gumamit ng board nang higit sa isang araw"], "0 sa 0 (—)")


class ReportsPageTest(ReportsBase):
    def test_only_admins_open_the_page_and_download_reports(self):
        for url in [reverse("reports"), reverse("export_report") + "?report=usage"]:
            self.assertTrue(self.client.get(url).url.startswith("/login/"))
            for username in ["miguel", "nanay"]:
                self.login_as(username)
                self.assertEqual(self.client.get(url).status_code, 302, f"{username} {url}")
            self.client.post(reverse("logout"))

    def test_each_tab_opens_and_an_unknown_one_is_the_first(self):
        self.login_as("developer")
        for tab, heading in [
            ("growth", "Mga bagong sign-up"), ("usage", "Mga pindot kada araw"), ("retention", "Pagbabalik ng mga gumagamit"),
            ("business", "Lalabas dito ang mga subscription"), ("export", "Mag-download ng ulat"),
        ]:
            response = self.client.get(reverse("reports"), {"tab": tab})
            self.assertEqual(response.context["tab"], tab)
            self.assertContains(response, heading)
            self.assertEqual([item["value"] for item in response.context["tabs"] if item["active"]], [tab])

        for data in [{}, {"tab": "wala-nito"}]:
            self.assertEqual(self.client.get(reverse("reports"), data).context["tab"], "growth")
        self.assertEqual(ReportTabForm({"tab": "usage"}).chosen(), "usage")


class ExportReportTest(ReportsBase):
    def export(self, **query):
        self.login_as("developer")
        return self.client.get(reverse("export_report"), query)

    def lines(self, response):
        return response.content.decode("utf-8-sig").splitlines()

    def test_form_needs_a_report_and_dates_in_order(self):
        self.assertEqual(ExportReportForm({}).errors["report"], ["Pumili ng ulat."])
        self.assertEqual(ExportReportForm({"report": "passwords"}).errors["report"], ["Pumili ng ulat mula sa listahan."])
        form = ExportReportForm({"report": "usage", "date_from": "2026-10-10", "date_to": "2026-10-01"})
        self.assertEqual(form.errors["date_to"], ["Dapat hindi mas maaga ang “Hanggang” kaysa sa “Mula”."])
        self.assertTrue(ExportReportForm({"report": "usage", "date_from": "2026-10-01", "date_to": "2026-10-01"}).is_valid())

    def test_usage_per_day_within_the_dates(self):
        self.used(DailyUsage.WORD, "kain", 4)
        self.used(DailyUsage.BOARD, "Tao", 2)
        self.used(DailyUsage.WORD, "inom", 3, days_ago=1, user=self.ana)
        self.used(DailyUsage.WORD, "laro", 9, days_ago=10)
        yesterday = self.today - timedelta(days=1)

        response = self.export(report="usage", date_from=yesterday.isoformat())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], f'attachment; filename="salitaaco-usage-{self.today.isoformat()}.csv"')
        self.assertEqual(self.lines(response), [
            "araw,mga_pindot,mga_bukas_ng_board",
            f"{yesterday.isoformat()},3,0",
            f"{self.today.isoformat()},4,2",
        ])
        self.assertEqual(len(self.lines(self.export(report="usage"))), 4)
        self.assertEqual(len(self.lines(self.export(report="usage", date_to=(self.today - timedelta(days=5)).isoformat()))), 2)

    def test_words_over_all_time_are_the_totals_and_with_dates_the_days(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=30)
        WordUsage.objects.create(user=self.ana, word="kain", use_count=5)
        WordUsage.objects.create(user=self.ana, word="inom", use_count=2)
        self.used(DailyUsage.WORD, "kain", 4)

        self.assertEqual(self.lines(self.export(report="words")), ["salita,mga_pindot", "kain,35", "inom,2"])
        self.assertEqual(self.lines(self.export(report="words", date_from=self.today.isoformat())), ["salita,mga_pindot", "kain,4"])

    def test_signups_per_day(self):
        now = timezone.now()
        User.objects.all().update(date_joined=now - timedelta(days=3))
        User.objects.filter(pk=self.ana.pk).update(date_joined=now)

        self.assertEqual(self.lines(self.export(report="signups")), [
            "araw,mga_sign_up",
            f"{(self.today - timedelta(days=3)).isoformat()},3",
            f"{self.today.isoformat()},1",
        ])

    def test_reports_hold_counts_only(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=3)
        self.used(DailyUsage.WORD, "kain", 3)
        for report in ["signups", "usage", "words"]:
            text = self.export(report=report).content.decode("utf-8-sig")
            for private in ["miguel", "Miguel", "nanay", "Nanay Rosa", "developer"]:
                self.assertNotIn(private, text, report)

    def test_a_request_that_is_not_valid_returns_to_the_reports_tab_with_the_reason(self):
        response = self.export(report="usage", date_from="2026-10-10", date_to="2026-10-01")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertContains(response, "Dapat hindi mas maaga ang “Hanggang” kaysa sa “Mula”.", status_code=400)
        self.assertContains(response, "Mag-download ng ulat", status_code=400)

        self.assertContains(self.export(), "Pumili ng ulat.", status_code=400)
