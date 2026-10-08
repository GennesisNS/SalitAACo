import os

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.models.child_account import ChildAccount
from salitaaco.models.customization import Customization
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import GUARDIAN_PASSWORD, UserBase, image_upload, make_guardian, sound_upload
from salitaaco.utils.uploads import random_upload_name


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class GuardianBase(UserBase):
    """Nanay is Miguel's guardian. Tatay is another guardian, of nobody here. Ana has no guardian."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.ana_account = ChildAccount.objects.get(user=cls.ana)

    def child_routes(self, child):
        return [
            reverse("manage_child", args=[child.uuid]),
            reverse("view_child_avatar", args=[child.uuid]),
            reverse("child_board", args=[child.uuid]),
        ]


class ChildrenAccessTest(GuardianBase):
    def test_anonymous_is_sent_to_login(self):
        for route in [reverse("children")] + self.child_routes(self.miguel_account):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, route)
            self.assertTrue(response.url.startswith("/login/"), route)

    def test_children_and_admins_cannot_open_the_guardian_pages(self):
        guardian_pages = [reverse("children"), reverse("manage_child", args=[self.miguel_account.uuid])]
        for username in ["miguel", "ana", "developer"]:
            self.login_as(username)
            for route in guardian_pages:
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302, (username, route))
                self.assertTrue(response.url.startswith("/login/"), (username, route))
            # Nobody but the child's guardian gets the child's board either.
            self.assertEqual(self.client.get(reverse("child_board", args=[self.miguel_account.uuid])).status_code, 404)

    def test_guardian_sees_only_their_own_children(self):
        self.login_as("nanay")
        response = self.client.get(reverse("children"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([child.display_name for child in response.context["children"]], ["Miguel"])

        self.login_as("tatay")
        response = self.client.get(reverse("children"))
        self.assertEqual(list(response.context["children"]), [])
        self.assertContains(response, "Wala ka pang naidadagdag na bata.")

    def test_guardian_cannot_reach_a_child_that_is_not_theirs(self):
        self.login_as("tatay")
        for child in [self.miguel_account, self.ana_account]:
            for route in self.child_routes(child):
                self.assertEqual(self.client.get(route).status_code, 404, route)
            response = self.client.post(reverse("manage_child", args=[child.uuid]), {"delete_child_form": "", "password": GUARDIAN_PASSWORD})
            self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(username="miguel").exists())

    def test_sidebar_shows_mga_bata_to_guardians_only(self):
        self.login_as("nanay")
        self.assertContains(self.client.get(reverse("board")), reverse("children"))
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertNotContains(self.client.get(reverse("board")), reverse("children"))


class CreateChildTest(GuardianBase):
    def create(self, **changes):
        data = {
            "create_child_form": "", "display_name": "Bunso", "username": "bunso", "age": "5",
            "password": "Bunso#123", "confirm_password": "Bunso#123", **changes,
        }
        return self.client.post(reverse("children"), data)

    def test_guardian_creates_a_child_who_can_log_in(self):
        self.login_as("nanay")
        response = self.create()

        self.assertRedirects(response, reverse("children"))
        self.assertEqual(messages_of(response), ["Nagawa na ang account ni Bunso."])

        child = ChildAccount.objects.get(user__username="bunso")
        self.assertEqual((child.display_name, child.age, child.guardian), ("Bunso", 5, self.nanay))
        self.assertEqual(list(child.user.groups.values_list("name", flat=True)), ["Child"])

        # The guardian is still the one logged in; the child logs in with their own password.
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.nanay.user.pk)
        self.client.logout()
        self.assertTrue(self.client.login(username="bunso", password="Bunso#123"))
        self.assertEqual(self.client.get(reverse("board")).status_code, 200)

    def test_invalid_child_reopens_the_modal_and_creates_nothing(self):
        self.login_as("nanay")
        response = self.create(username="miguel")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_create_child_modal"])
        self.assertContains(response, "Ginagamit na ang username na ito.")
        self.assertFalse(User.objects.filter(username="bunso").exists())
        self.assertEqual(self.nanay.children.count(), 1)


class ManageChildTest(GuardianBase):
    def setUp(self):
        self.login_as("nanay")
        self.url = reverse("manage_child", args=[self.miguel_account.uuid])

    def test_page_shows_the_childs_usage(self):
        for word, count in [("kain", 5), ("inom", 2)]:
            WordUsage.objects.create(user=self.miguel, word=word, use_count=count)
        WordUsage.objects.create(user=self.ana, word="laro", use_count=9)
        customization = Customization.objects.create(user=self.miguel, word="mama")
        customization.set_image(random_upload_name("image/png"), image_upload(), "image/png")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["usage"], [
            {"word": "kain", "use_count": 5, "width": 100},
            {"word": "inom", "use_count": 2, "width": 40},
        ])
        self.assertEqual(response.context["total_taps"], 7)
        self.assertEqual((response.context["image_count"], response.context["sound_count"]), (1, 0))

    def test_update_the_childs_profile(self):
        response = self.client.post(self.url, {"child_form": "", "display_name": "Migs", "age": "8"})

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang profile ng bata."])
        child = ChildAccount.objects.get(user=self.miguel)
        self.assertEqual((child.display_name, child.age), ("Migs", 8))

    def test_invalid_profile_shows_the_error(self):
        response = self.client.post(self.url, {"child_form": "", "display_name": "", "age": "8"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ilagay ang pangalan.")
        self.assertEqual(ChildAccount.objects.get(user=self.miguel).display_name, "Miguel")

    def test_avatar_upload_view_and_remove(self):
        avatar_url = reverse("view_child_avatar", args=[self.miguel_account.uuid])
        self.assertEqual(self.client.get(avatar_url).status_code, 404)

        response = self.client.post(self.url, {"avatar_form": "1", "avatar": image_upload()})
        self.assertRedirects(response, self.url)
        path = ChildAccount.objects.get(user=self.miguel).avatar.path

        response = self.client.get(avatar_url)
        self.assertEqual((response.status_code, response["Content-Type"]), (200, "image/png"))
        response.close()

        remove_url = reverse("remove_child_avatar", args=[self.miguel_account.uuid])
        self.assertEqual(self.client.get(remove_url).status_code, 405)
        self.assertRedirects(self.client.post(remove_url), self.url)
        self.assertFalse(ChildAccount.objects.get(user=self.miguel).has_avatar)
        self.assertFalse(os.path.exists(path))

    def test_reset_password_does_not_need_the_old_one_and_logs_the_child_out(self):
        child_browser = self.client_class()
        self.assertTrue(child_browser.login(username="miguel", password="lihim1234"))

        response = self.client.post(self.url, {"password_form": "", "new_password": "Bago#1234", "confirm_password": "Bago#1234"})

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nabago na ang password ni Miguel."])
        self.assertTrue(User.objects.get(username="miguel").check_password("Bago#1234"))
        # The child's open session is over; the guardian's is not.
        self.assertTrue(child_browser.get(reverse("board")).url.startswith("/login/"))
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_mismatched_passwords_change_nothing(self):
        response = self.client.post(self.url, {"password_form": "", "new_password": "Bago#1234", "confirm_password": "Iba#12345"})
        self.assertContains(response, "Hindi magkatugma ang bagong password at kumpirmasyon.")
        self.assertTrue(User.objects.get(username="miguel").check_password("lihim1234"))

    def test_delete_needs_the_guardians_password(self):
        response = self.client.post(self.url, {"delete_child_form": "", "password": "lihim1234"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_delete_child_modal"])
        self.assertContains(response, "Maling password.")
        self.assertTrue(User.objects.filter(username="miguel").exists())

    def test_delete_removes_the_child_their_data_and_their_files(self):
        self.miguel_account.set_avatar(random_upload_name("image/png"), image_upload(), "image/png")
        customization = Customization.objects.create(user=self.miguel, word="mama")
        customization.set_sound(random_upload_name("audio/webm"), sound_upload(), "audio/webm")
        WordUsage.record_use(self.miguel, "kain")
        Rating.objects.create(user=self.miguel, rating=5)
        paths = [self.miguel_account.avatar.path, customization.sound.path]

        response = self.client.post(self.url, {"delete_child_form": "", "password": GUARDIAN_PASSWORD})

        self.assertRedirects(response, reverse("children"))
        self.assertEqual(messages_of(response), ["Permanente nang nabura ang account ni Miguel."])
        self.assertFalse(User.objects.filter(username="miguel").exists())
        for model in [ChildAccount, Customization, WordUsage, Rating]:
            self.assertFalse(model.objects.filter(user_id=self.miguel.pk).exists(), model.__name__)
        for path in paths:
            self.assertFalse(os.path.exists(path), path)
        # The guardian and the other child are untouched.
        self.assertTrue(User.objects.filter(username__in=["nanay", "ana"]).count() == 2)


class ChildBoardTest(GuardianBase):
    """A guardian sets up their child's tiles on the child's board."""

    def setUp(self):
        self.login_as("nanay")
        self.url = reverse("child_board", args=[self.miguel_account.uuid])

    def test_board_is_the_childs_and_counts_nothing(self):
        Customization.objects.create(user=self.miguel, word="mama")
        Customization.objects.create(user=self.nanay.user, word="papa")
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=3)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inaayos mo ang mga tile ni <b>Miguel</b>")
        self.assertNotContains(response, "I-rate ang app")
        board_data = response.context["board_data"]
        self.assertTrue(board_data["managed"])
        self.assertEqual([item["word"] for item in board_data["customizations"]], ["mama"])
        self.assertEqual(board_data["frequent_words"], [{"word": "kain", "use_count": 3}])
        self.assertIsNone(board_data["increment_usage_url"])
        self.assertIsNone(board_data["frequent_words_url"])

    def test_own_board_is_unchanged(self):
        Customization.objects.create(user=self.miguel, word="mama")
        response = self.client.get(reverse("board"))

        board_data = response.context["board_data"]
        self.assertFalse(board_data["managed"])
        self.assertEqual(board_data["customizations"], [])
        self.assertEqual(board_data["increment_usage_url"], reverse("increment_word_usage"))
        self.assertContains(response, "I-rate ang app")

    def test_guardian_uploads_and_resets_the_childs_tiles(self):
        response = self.client.post(self.url, {"tile_image_form": "1", "word": "mama", "image": image_upload()})
        self.assertRedirects(response, self.url)
        response = self.client.post(self.url, {"tile_sound_form": "1", "word": "mama", "sound": sound_upload()})
        self.assertRedirects(response, self.url)

        # The tile belongs to the child, not to the guardian who made it.
        customization = Customization.objects.get(word="mama")
        self.assertEqual(customization.user, self.miguel)
        self.assertTrue(customization.has_image and customization.has_sound)
        self.assertFalse(Customization.objects.filter(user=self.nanay.user).exists())

        # The guardian can see and hear it, and so can the child.
        image_url = reverse("view_customization_image", args=[customization.uuid])
        sound_url = reverse("view_customization_sound", args=[customization.uuid])
        for client in [self.client, self.client_class()]:
            if client is not self.client:
                self.assertTrue(client.login(username="miguel", password="lihim1234"))
            for url, content_type in [(image_url, "image/png"), (sound_url, "audio/webm")]:
                response = client.get(url)
                self.assertEqual((response.status_code, response["Content-Type"]), (200, content_type))
                response.close()

        response = self.client.post(reverse("reset_customization", args=[customization.uuid]))
        self.assertRedirects(response, self.url)
        self.assertFalse(Customization.objects.exists())

    def test_another_guardian_cannot_touch_the_childs_tiles(self):
        customization = Customization.objects.create(user=self.miguel, word="mama")
        customization.set_image(random_upload_name("image/png"), image_upload(), "image/png")

        self.login_as("tatay")
        self.assertEqual(self.client.get(reverse("view_customization_image", args=[customization.uuid])).status_code, 404)
        self.assertEqual(self.client.post(reverse("reset_customization", args=[customization.uuid])).status_code, 404)
        self.assertEqual(self.client.post(self.url, {"tile_image_form": "1", "word": "papa", "image": image_upload()}).status_code, 404)
        self.assertEqual(Customization.objects.count(), 1)

    def test_child_cannot_see_the_guardians_own_tiles(self):
        customization = Customization.objects.create(user=self.nanay.user, word="papa")
        customization.set_image(random_upload_name("image/png"), image_upload(), "image/png")

        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("view_customization_image", args=[customization.uuid])).status_code, 404)
