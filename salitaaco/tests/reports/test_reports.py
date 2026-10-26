from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from salitaaco.forms.reports.report_tab import ReportTabForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.payments_base import make_payment
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils import admin_stats, analytics
from salitaaco.utils.plans import approve_payment, reject_payment


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
    def test_only_admins_open_the_page(self):
        url = reverse("reports")
        self.assertTrue(self.client.get(url).url.startswith("/login/"))
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 302, username)

    def test_each_tab_opens_and_an_unknown_one_is_the_first(self):
        self.login_as("developer")
        for tab, heading in [
            ("growth", "Mga bagong sign-up"), ("usage", "Mga pindot kada araw"), ("retention", "Pagbabalik ng mga gumagamit"),
            ("business", "Mga bayad ayon sa status"),
        ]:
            response = self.client.get(reverse("reports"), {"tab": tab})
            self.assertEqual(response.context["tab"], tab)
            self.assertContains(response, heading)
            self.assertEqual([item["value"] for item in response.context["tabs"] if item["active"]], [tab])

        for data in [{}, {"tab": "wala-nito"}]:
            self.assertEqual(self.client.get(reverse("reports"), data).context["tab"], "growth")
        self.assertEqual(ReportTabForm({"tab": "usage"}).chosen(), "usage")

    def test_the_csv_tab_is_gone_and_mga_ulat_is_linked(self):
        # Reports to download are made on Mga Ulat now.
        self.login_as("developer")
        self.assertEqual(self.client.get(reverse("reports"), {"tab": "export"}).context["tab"], "growth")
        self.assertContains(self.client.get(reverse("reports")), f'href="{reverse("generated_reports")}"')

    def test_the_business_tab_has_the_plans_and_the_money(self):
        approve_payment(make_payment(self.nanay), self.developer)
        make_payment(self.nanay)
        rejected = make_payment(self.nanay)
        reject_payment(rejected, self.developer, "Malabo.")

        self.login_as("developer")
        response = self.client.get(reverse("reports"), {"tab": "business"})
        business = response.context["business"]
        self.assertEqual(business["plans"], [{"name": "Free", "guardians": 0}, {"name": "SalitAACo Plus", "guardians": 1}])
        self.assertEqual((business["revenue_this_month"], business["revenue_total"]), ("₱149", "₱149"))
        self.assertEqual((business["pending"], business["approved"], business["rejected"]), (1, 1, 1))
        self.assertEqual(len(business["months"]), 6)
        self.assertEqual((business["months"][-1]["month"], business["months"][-1]["pesos"]), (self.today.replace(day=1), "₱149"))
        self.assertContains(response, "Naka-SalitAACo Plus")


class TopWordsTest(ReportsBase):
    def test_the_most_used_words_leave_out_a_familys_own_tiles(self):
        # Nanay's family has a tile of a name; Ana, of another family, taps an app word of the same spelling.
        GuardianWord.objects.create(guardian=self.nanay, board="Tao", word="Lola Nena", emoji="👵")
        GuardianWord.objects.create(guardian=self.nanay, board="Pagkain", word="pandesal", emoji="🥖")
        WordUsage.objects.create(user=self.miguel, word="Lola Nena", use_count=9)
        WordUsage.objects.create(user=self.miguel, word="pandesal", use_count=4)
        WordUsage.objects.create(user=self.ana, word="pandesal", use_count=2)
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=1)

        self.assertEqual([(row["word"], row["total_uses"]) for row in analytics.top_words()], [("pandesal", 2), ("kain", 1)])
