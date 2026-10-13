from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, make_guardian


class AdminDashboardTest(UserBase):
    """The admin dashboard: numbers at a glance. Its old lists are on Mga User and Feedback at mga Isyu."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])

    def test_an_admin_lands_here_and_it_is_lit_in_the_sidebar(self):
        response = self.client.post(reverse("login"), {"username": "developer", "password": "dev-password"})
        self.assertRedirects(response, reverse("analytics"))
        response = self.client.get(reverse("analytics"))
        self.assertContains(response, f'<a class="sidebarItem active" href="{reverse("analytics")}" aria-current="page">')
        self.assertContains(response, "Dashboard")

    def test_the_numbers(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=7)
        Rating.objects.create(user=self.miguel, rating=4)
        SupportMessage.objects.create(guardian=self.nanay, message="Bukas pa ito.")
        SupportMessage.objects.create(guardian=self.nanay, message="Naayos na ito.", resolved_at=timezone.now())
        User.objects.filter(pk=self.ana.pk).update(is_active=False)
        DailyUsage.objects.create(user=self.miguel, day=timezone.localdate(), kind=DailyUsage.WORD, name="kain", use_count=7)
        DailyUsage.objects.create(user=self.miguel, day=timezone.localdate(), kind=DailyUsage.BOARD, name="Pandiwa", use_count=2)
        self.login_as("developer")

        response = self.client.get(reverse("analytics"))

        cards = {card["label"]: card["value"] for card in response.context["stat_cards"]}
        self.assertEqual(cards["Kabuuang users"], 4)
        self.assertEqual(cards["Mga tagapag-alaga"], 1)
        self.assertEqual(cards["Mga bata"], 2)
        self.assertEqual(cards["Kabuuang taps"], 7)
        self.assertEqual(cards["Average rating"], 4.0)
        self.assertEqual(cards["Bukas na mensahe sa suporta"], 1)
        self.assertEqual(cards["Hindi aktibong account"], 1)

        self.assertEqual(len(response.context["usage_by_day"]), 7)
        self.assertEqual(response.context["usage_by_day"][-1]["taps"], 7)
        self.assertEqual([board["name"] for board in response.context["board_opens"]], ["Pandiwa"])
        self.assertTrue(response.context["recent_activity"])

    def test_the_lists_moved_to_pages_of_their_own(self):
        self.login_as("developer")
        response = self.client.get(reverse("analytics"))
        for moved in ["users", "ratings", "search_user_form"]:
            self.assertNotIn(moved, response.context)
        self.assertContains(response, f'href="{reverse("users")}"')
        self.assertContains(response, f'href="{reverse("feedback")}"')
        self.assertContains(response, f'href="{reverse("reports")}"')

    def test_a_site_with_no_activity_shows_the_empty_states(self):
        self.login_as("developer")
        response = self.client.get(reverse("analytics"))
        self.assertContains(response, "Wala pang nabubuksang board.")
        self.assertEqual([day["taps"] for day in response.context["usage_by_day"]], [0] * 7)
