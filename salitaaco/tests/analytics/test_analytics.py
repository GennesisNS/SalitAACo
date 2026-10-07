from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from salitaaco.forms.analytics.search_user import SearchUserForm
from salitaaco.models.customization import Customization
from salitaaco.models.profile import Profile
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, image_upload, sound_upload
from salitaaco.utils import analytics
from salitaaco.utils.pagination import paginate
from salitaaco.utils.uploads import random_upload_name


class AnalyticsAccessTest(UserBase):
    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("analytics"))
        self.assertRedirects(response, f"/login/?next={reverse('analytics')}")

    def test_ordinary_user_is_turned_away_with_a_message(self):
        self.login_as("miguel")
        response = self.client.get(reverse("analytics"), follow=True)

        self.assertRedirects(response, reverse("board"))
        self.assertEqual(
            [str(message) for message in get_messages(response.wsgi_request)],
            ["Naka-log in ka pero hindi admin ang account na ito."],
        )

    def test_administrator_sees_the_dashboard(self):
        self.login_as("developer")
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kabuuang users")


class SearchUserFormTest(UserBase):
    def test_empty_and_filled_are_valid(self):
        self.assertTrue(SearchUserForm({}).is_valid())
        self.assertTrue(SearchUserForm({"query": "mig", "order_by": "username_asc"}).is_valid())

    def test_unknown_order_is_rejected(self):
        form = SearchUserForm({"order_by": "password_asc"})
        self.assertFalse(form.is_valid())
        self.assertIn("order_by", form.errors)


class AnalyticsNumbersTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()

        # miguel signed up 3 days ago and logged in today; ana signed up 10 days ago
        # and last logged in 8 days ago; developer signed up today and never logged in.
        User.objects.filter(pk=cls.miguel.pk).update(date_joined=now - timedelta(days=3), last_login=now)
        User.objects.filter(pk=cls.ana.pk).update(date_joined=now - timedelta(days=10), last_login=now - timedelta(days=8))

        mama = Customization.objects.create(user=cls.miguel, word="mama")
        mama.set_image(random_upload_name("image/png"), image_upload(), "image/png")
        mama.set_sound(random_upload_name("audio/webm"), sound_upload(size=96), "audio/webm")
        papa = Customization.objects.create(user=cls.miguel, word="papa")
        papa.set_image(random_upload_name("image/png"), image_upload(), "image/png")
        cls.upload_bytes = mama.image.size + mama.sound.size + papa.image.size

        WordUsage.objects.create(user=cls.miguel, word="kain", use_count=5)
        WordUsage.objects.create(user=cls.miguel, word="inom", use_count=2)
        WordUsage.objects.create(user=cls.ana, word="kain", use_count=4)

        Rating.objects.create(user=cls.miguel, rating=5, comment="Ang galing")
        Rating.objects.create(user=cls.ana, rating=4)

    def test_overview(self):
        numbers = analytics.overview()

        self.assertEqual(numbers["total_users"], 3)
        self.assertEqual(numbers["new_today"], 1)
        self.assertEqual(numbers["new_this_week"], 2)
        self.assertEqual(numbers["active_today"], 1)
        self.assertEqual(numbers["active_this_week"], 1)
        self.assertEqual(numbers["total_images"], 2)
        self.assertEqual(numbers["total_sounds"], 1)
        self.assertEqual(numbers["total_taps"], 11)
        self.assertEqual(numbers["average_rating"], 4.5)
        self.assertEqual(numbers["rating_count"], 2)
        self.assertEqual(numbers["storage_bytes"], self.upload_bytes)

    def test_overview_with_no_ratings(self):
        Rating.objects.all().delete()
        numbers = analytics.overview()
        self.assertIsNone(numbers["average_rating"])
        self.assertEqual(analytics.stat_cards(numbers)[3]["value"], "—")

    def test_signups_by_day_covers_fourteen_days_ending_today(self):
        series = analytics.signups_by_day()
        today = timezone.localdate()

        self.assertEqual(len(series), 14)
        self.assertEqual(series[-1]["date"], today)
        self.assertEqual(series[0]["date"], today - timedelta(days=13))
        self.assertEqual({day["date"]: day["count"] for day in series if day["count"]}, {
            today: 1,
            today - timedelta(days=3): 1,
            today - timedelta(days=10): 1,
        })
        self.assertEqual(series[-1]["width"], 100)

    def test_rating_distribution_lists_five_stars_first(self):
        distribution = analytics.rating_distribution()
        self.assertEqual([row["label"] for row in distribution], ["5 ★", "4 ★", "3 ★", "2 ★", "1 ★"])
        self.assertEqual([row["count"] for row in distribution], [1, 1, 0, 0, 0])

    def test_top_words_adds_up_all_users(self):
        words = analytics.top_words()
        self.assertEqual(
            [(word["word"], word["total_uses"], word["user_count"], word["width"]) for word in words],
            [("kain", 9, 2, 100), ("inom", 2, 1, 22)],
        )

    def test_users_table_has_the_per_user_counts(self):
        self.login_as("developer")
        users = {user.username: user for user in self.client.get(reverse("analytics")).context["users"]}

        miguel = users["miguel"]
        self.assertEqual((miguel.image_count, miguel.sound_count, miguel.total_taps, miguel.rating_stars), (2, 1, 7, 5))
        self.assertFalse(miguel.is_admin)

        developer = users["developer"]
        self.assertEqual((developer.image_count, developer.sound_count, developer.total_taps), (0, 0, 0))
        self.assertIsNone(developer.rating_stars)
        self.assertTrue(developer.is_admin)

    def test_users_are_newest_first_and_can_be_searched_and_sorted(self):
        self.login_as("developer")

        def usernames(**query):
            return [user.username for user in self.client.get(reverse("analytics"), query).context["users"]]

        self.assertEqual(usernames(), ["developer", "miguel", "ana"])
        self.assertEqual(usernames(order_by="username_asc"), ["ana", "developer", "miguel"])
        self.assertEqual(usernames(query="MIG"), ["miguel"])
        self.assertEqual(usernames(query="Ana"), ["ana"])  # matched on the display name too
        self.assertEqual(usernames(order_by="password_asc"), ["developer", "miguel", "ana"])

    def test_feedback_is_most_recently_updated_first(self):
        Rating.objects.filter(user=self.ana).update(updated_at=timezone.now() + timedelta(minutes=5))
        self.login_as("developer")
        response = self.client.get(reverse("analytics"))

        self.assertEqual([rating.user.username for rating in response.context["ratings"]], ["ana", "miguel"])
        self.assertContains(response, "Ang galing")

    def test_users_table_is_paginated_ten_per_page(self):
        for number in range(12):
            user = User.objects.create_user(username=f"bata{number:02}", password="abcd")
            Profile.objects.create(user=user, display_name=f"Bata {number}")
        self.login_as("developer")

        first_page = self.client.get(reverse("analytics"))
        self.assertEqual(len(first_page.context["users"]), 10)
        self.assertContains(first_page, "?users_page=2#users")

        second_page = self.client.get(reverse("analytics"), {"users_page": 2, "query": "bata"})
        self.assertEqual(len(second_page.context["users"]), 2)
        self.assertContains(second_page, "?users_page=1&amp;query=bata#users")


class PaginationTest(UserBase):
    def test_page_window_is_three_pages_around_the_current_one(self):
        rows = list(range(95))  # ten pages
        self.assertEqual(list(paginate(rows, 1).page_window), [1, 2, 3])
        self.assertEqual(list(paginate(rows, 5).page_window), [4, 5, 6])
        self.assertEqual(list(paginate(rows, 10).page_window), [8, 9, 10])
        self.assertEqual(list(paginate(rows, "abc").page_window), [1, 2, 3])
        self.assertEqual(list(paginate(list(range(15)), 2).page_window), [1, 2])
        self.assertEqual(list(paginate([], 1).page_window), [1])
