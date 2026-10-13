from datetime import timedelta

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from salitaaco.models.child_account import ChildAccount
from salitaaco.models.rating import Rating
from salitaaco.models.support_message import SupportMessage
from salitaaco.tests.users_base import UserBase, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class FeedbackTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("feedback")

    def test_only_admins_open_the_page_and_mark_messages(self):
        message = SupportMessage.objects.create(guardian=self.nanay, message="Tulong po.")
        resolve_url = reverse("resolve_support_message", args=[message.uuid])
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.client.post(resolve_url).status_code, 302)
        self.assertFalse(SupportMessage.objects.get().is_resolved)

    def test_page_shows_the_ratings_and_the_support_messages(self):
        Rating.objects.create(user=self.miguel, rating=5, comment="Ang galing")
        Rating.objects.create(user=self.ana, rating=3)
        child = ChildAccount.objects.get(user=self.miguel)
        SupportMessage.objects.create(guardian=self.nanay, child=child, message="Hindi lumalabas ang larawan.")
        self.login_as("developer")

        response = self.client.get(self.url)

        self.assertEqual(response.context["overview"]["average_rating"], 4.0)
        self.assertEqual(len(response.context["ratings"]), 2)
        self.assertContains(response, "Ang galing")
        self.assertContains(response, "Hindi lumalabas ang larawan.")
        self.assertContains(response, "tungkol kay Miguel")
        self.assertEqual(response.context["open_count"], 1)
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')

    def test_page_with_no_feedback_shows_the_empty_states(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, "Wala pang mensahe sa suporta.")
        self.assertContains(response, "Walang rating pa.")

    def test_open_messages_come_before_the_ones_dealt_with(self):
        now = timezone.now()
        old_open = SupportMessage.objects.create(guardian=self.nanay, message="Luma, bukas")
        SupportMessage.objects.filter(pk=old_open.pk).update(created_at=now - timedelta(days=3))
        SupportMessage.objects.create(guardian=self.nanay, message="Bago, naayos", resolved_at=now)
        SupportMessage.objects.create(guardian=self.nanay, message="Bago, bukas")
        self.login_as("developer")

        shown = [message.message for message in self.client.get(self.url).context["support_messages"]]

        self.assertEqual(shown, ["Bago, bukas", "Luma, bukas", "Bago, naayos"])

    def test_marking_a_message_and_opening_it_again(self):
        message = SupportMessage.objects.create(guardian=self.nanay, message="Tulong po.")
        resolve_url = reverse("resolve_support_message", args=[message.uuid])
        self.login_as("developer")
        self.assertEqual(self.client.get(resolve_url).status_code, 405)

        response = self.client.post(resolve_url)
        self.assertRedirects(response, f"{self.url}#messages", fetch_redirect_response=False)
        self.assertEqual(messages_of(response), ["Namarkahan nang naayos ang mensahe."])
        self.assertTrue(SupportMessage.objects.get().is_resolved)
        self.assertContains(self.client.get(self.url), '<span class="statusBadge approved">Naayos na</span>')

        response = self.client.post(resolve_url)
        self.assertEqual(messages_of(response)[-1], "Bukas na muli ang mensahe.")
        self.assertFalse(SupportMessage.objects.get().is_resolved)

    def test_the_guardian_sees_whether_their_message_was_dealt_with(self):
        message = SupportMessage.objects.create(guardian=self.nanay, message="Tulong po.")
        self.login_as("nanay")
        self.assertContains(self.client.get(reverse("support")), "Bukas pa")

        SupportMessage.objects.filter(pk=message.pk).update(resolved_at=timezone.now())
        response = self.client.get(reverse("support"))
        self.assertContains(response, "Naayos na")
        self.assertNotContains(response, "Bukas pa")
