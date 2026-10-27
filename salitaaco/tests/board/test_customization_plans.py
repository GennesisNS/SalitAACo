from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.payment import Payment
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian, sound_upload
from salitaaco.utils.customizations import PLUS_CUSTOMIZATION
from salitaaco.utils.plans import approve_payment
from salitaaco.utils.uploads import random_upload_name


class CustomizationPlanTest(UserBase):
    """
    A tile's own recording (edit mode) is for paid plans. Nanay is Miguel's
    guardian, on Free; Ana has no guardian, from before guardians.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)

    def setUp(self):
        self.child_board = reverse("child_board", args=[self.miguel_account.uuid])

    def record(self, user, word="mama"):
        customization = Customization.objects.create(user=user, word=word)
        customization.set_sound(random_upload_name("audio/webm"), sound_upload(), "audio/webm")
        return customization

    def board_data(self, url):
        return self.client.get(url).context["board_data"]

    def test_on_free_there_is_no_edit_mode_and_a_recording_is_refused(self):
        self.login_as("nanay")
        for url in [reverse("board"), self.child_board]:
            response = self.client.get(url)
            self.assertFalse(response.context["board_data"]["can_customize"], url)
            self.assertNotContains(response, 'id="editModeBtn"')
            self.assertContains(response, f'<a class="iconbtn" href="{reverse("plan")}">✏️ Para sa Plus ang pag-edit ng mga cell</a>')

            response = self.client.post(url, {"tile_sound_form": "1", "word": "mama", "sound": sound_upload()})
            self.assertRedirects(response, url)
            self.assertEqual(messages_of(response)[-1], PLUS_CUSTOMIZATION)
        self.assertFalse(Customization.objects.exists())
        # The child's page tells the guardian too.
        self.assertContains(self.client.get(reverse("manage_child", args=[self.miguel_account.uuid])), PLUS_CUSTOMIZATION)

    def test_a_child_on_free_is_not_offered_plus(self):
        self.login_as("miguel")
        response = self.client.get(reverse("board"))
        self.assertNotContains(response, 'id="editModeBtn"')
        self.assertNotContains(response, "Para sa Plus")
        self.assertContains(self.client.get(reverse("settings")), "Hindi pa puwedeng baguhin ang mga tile.")

    def test_on_plus_the_guardian_records_on_the_childs_board(self):
        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("nanay")
        for url in [reverse("board"), self.child_board]:
            response = self.client.get(url)
            self.assertTrue(response.context["board_data"]["can_customize"], url)
            self.assertContains(response, 'id="editModeBtn"')
        self.assertRedirects(self.client.post(self.child_board, {"tile_sound_form": "1", "word": "mama", "sound": sound_upload()}), self.child_board)
        # It is the child's: it plays on their board, before the family voice.
        self.assertTrue(Customization.objects.get(user=self.miguel, word="mama").has_sound)
        self.assertContains(self.client.get(reverse("settings")), f'href="{reverse("board")}?edit=1"')
        self.assertContains(self.client.get(reverse("manage_child", args=[self.miguel_account.uuid])), "Mayroon na siyang 1 recording.")

    def test_when_plus_ends_they_are_kept_unplayed_and_come_back_on_renewal(self):
        approve_payment(make_payment(self.nanay), self.developer)
        customization = self.record(self.miguel)

        Payment.objects.filter(guardian=self.nanay).update(ends_at=timezone.now() - timedelta(days=1))
        self.login_as("miguel")
        self.assertEqual(self.board_data(reverse("board"))["customizations"], [])
        self.assertTrue(Customization.objects.filter(pk=customization.pk).exists())
        self.login_as("nanay")
        self.assertEqual(self.board_data(self.child_board)["customizations"], [])
        self.assertContains(self.client.get(reverse("settings")), PLUS_CUSTOMIZATION)

        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("miguel")
        self.assertEqual([item["word"] for item in self.board_data(reverse("board"))["customizations"]], ["mama"])

    def test_admins_and_children_from_before_guardians_keep_edit_mode(self):
        self.record(self.ana)
        for username in ["developer", "ana"]:
            self.login_as(username)
            data = self.board_data(reverse("board"))
            self.assertTrue(data["can_customize"], username)
        self.assertEqual([item["word"] for item in data["customizations"]], ["mama"])
