from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from salitaaco.forms.children.usage_range import UsageRangeForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.usage import usage_in_days, word_usage


class UsageBase(UserBase):
    """Nanay is Miguel's guardian. Tatay is a guardian of nobody."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.url = reverse("child_usage", args=[cls.miguel_account.uuid])

    def used(self, kind, name, count, days_ago=0, user=None):
        return DailyUsage.objects.create(
            user=user or self.miguel, kind=kind, name=name, use_count=count,
            day=timezone.localdate() - timedelta(days=days_ago),
        )


class DailyUsageTest(UsageBase):
    def test_a_tap_is_counted_for_the_word_and_for_the_day(self):
        self.login_as("miguel")
        for word in ["kain", "kain", "inom"]:
            self.client.post(reverse("increment_word_usage"), {"word": word})

        self.assertEqual(WordUsage.objects.get(user=self.miguel, word="kain").use_count, 2)
        today = DailyUsage.objects.filter(user=self.miguel, day=timezone.localdate(), kind=DailyUsage.WORD)
        self.assertEqual({usage.name: usage.use_count for usage in today}, {"kain": 2, "inom": 1})

    def test_each_day_has_its_own_row(self):
        self.used(DailyUsage.WORD, "kain", 4, days_ago=1)
        DailyUsage.record(self.miguel, DailyUsage.WORD, "kain")
        DailyUsage.record(self.miguel, DailyUsage.WORD, "kain")

        counts = DailyUsage.objects.filter(user=self.miguel, name="kain").order_by("day").values_list("use_count", flat=True)
        self.assertEqual(list(counts), [4, 2])

    def test_opening_a_board_is_counted(self):
        self.login_as("miguel")
        url = reverse("record_board_open")
        for board in ["Tao", "Tao", "Pandiwa"]:
            self.assertEqual(self.client.post(url, {"board": board}).json(), {"ok": True})

        opened = DailyUsage.objects.filter(user=self.miguel, kind=DailyUsage.BOARD)
        self.assertEqual({usage.name: usage.use_count for usage in opened}, {"Tao": 2, "Pandiwa": 1})

    def test_only_real_boards_are_counted_and_only_by_post(self):
        url = reverse("record_board_open")
        self.assertTrue(self.client.post(url, {"board": "Tao"}).url.startswith("/login/"))

        self.login_as("miguel")
        for board in ["Wala Nito", ""]:
            response = self.client.post(url, {"board": board})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {"ok": False, "error": "Walang ganitong board."})
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertFalse(DailyUsage.objects.exists())

    def test_a_guardian_on_a_childs_board_is_not_counted(self):
        self.login_as("nanay")
        board_data = self.client.get(reverse("child_board", args=[self.miguel_account.uuid])).context["board_data"]
        self.assertIsNone(board_data["board_open_url"])

        self.login_as("miguel")
        board_data = self.client.get(reverse("board")).context["board_data"]
        self.assertEqual(board_data["board_open_url"], reverse("record_board_open"))

    def test_deleting_the_account_deletes_its_counts(self):
        self.used(DailyUsage.WORD, "kain", 4)
        self.miguel.delete()
        self.assertFalse(DailyUsage.objects.exists())


class UsageNumbersTest(UsageBase):
    def setUp(self):
        self.used(DailyUsage.WORD, "kain", 3)
        self.used(DailyUsage.WORD, "kain", 2, days_ago=6)
        self.used(DailyUsage.WORD, "inom", 4, days_ago=7)
        self.used(DailyUsage.WORD, "laro", 9, days_ago=40)
        self.used(DailyUsage.BOARD, "Tao", 1, days_ago=29)
        self.used(DailyUsage.WORD, "tulog", 50, user=self.ana)

    def test_the_last_days_include_today_and_end_where_they_say(self):
        self.assertEqual(usage_in_days(self.miguel, DailyUsage.WORD, 7), [{"name": "kain", "use_count": 5}])
        self.assertEqual(usage_in_days(self.miguel, DailyUsage.WORD, 30), [
            {"name": "kain", "use_count": 5},
            {"name": "inom", "use_count": 4},
        ])
        self.assertEqual(usage_in_days(self.miguel, DailyUsage.WORD)[0], {"name": "laro", "use_count": 9})
        self.assertEqual(usage_in_days(self.miguel, DailyUsage.BOARD, 7), [])
        self.assertEqual(usage_in_days(self.miguel, DailyUsage.BOARD, 30), [{"name": "Tao", "use_count": 1}])

    def test_words_over_every_day_are_the_totals_which_go_further_back(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=25)
        WordUsage.objects.create(user=self.miguel, word="mama", use_count=30)
        self.assertEqual(word_usage(self.miguel), [
            {"name": "mama", "use_count": 30},
            {"name": "kain", "use_count": 25},
        ])
        self.assertEqual(word_usage(self.miguel, 7), [{"name": "kain", "use_count": 5}])


class UsageRangeFormTest(UsageBase):
    def test_the_usual_range_is_seven_days(self):
        for data in [None, {}, {"range": ""}, {"range": "abc"}, {"range": "365"}]:
            form = UsageRangeForm(data)
            self.assertEqual((form.days(), form.chosen()), (7, "7"), data)

    def test_the_other_ranges(self):
        self.assertEqual(UsageRangeForm({"range": "30"}).days(), 30)
        self.assertIsNone(UsageRangeForm({"range": "all"}).days())
        self.assertEqual(UsageRangeForm({"range": "all"}).chosen(), "all")


class UsagePageTest(UsageBase):
    def test_only_the_childs_guardian_opens_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("tatay")
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_page_shows_boards_and_words_for_the_range(self):
        self.used(DailyUsage.WORD, "kain", 4)
        self.used(DailyUsage.WORD, "inom", 1)
        self.used(DailyUsage.WORD, "laro", 9, days_ago=20)
        self.used(DailyUsage.BOARD, "Pandiwa", 2)
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=12)
        self.login_as("nanay")

        response = self.client.get(self.url)

        self.assertEqual(response.context["words"], [
            {"name": "kain", "use_count": 4, "width": 100},
            {"name": "inom", "use_count": 1, "width": 25},
        ])
        self.assertEqual(response.context["boards"], [{"name": "Pandiwa", "use_count": 2, "width": 100, "icon": "🏃"}])
        self.assertEqual(response.context["total_taps"], 12)
        self.assertEqual(response.context["counted_since"], timezone.localdate() - timedelta(days=20))
        self.assertEqual([r["value"] for r in response.context["ranges"] if r["active"]], ["7"])
        self.assertContains(response, "medikal na pagsusuri")

        response = self.client.get(self.url, {"range": "30"})
        self.assertEqual([row["name"] for row in response.context["words"]], ["laro", "kain", "inom"])
        self.assertEqual([r["value"] for r in response.context["ranges"] if r["active"]], ["30"])

        response = self.client.get(self.url, {"range": "all"})
        self.assertEqual(response.context["words"], [{"name": "kain", "use_count": 12, "width": 100}])

    def test_a_child_with_nothing_counted_gets_the_empty_states(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "Wala pang nabubuksang board sa panahong ito.")
        self.assertContains(response, "Wala pang napipindot na salita sa panahong ito.")
        self.assertIsNone(response.context["counted_since"])
