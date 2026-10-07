import os

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.models.customization import Customization
from salitaaco.models.profile import Profile
from salitaaco.models.rating import Rating
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, image_upload, sound_upload
from salitaaco.utils.uploads import random_upload_name


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class AccountAccessTest(UserBase):
    def test_anonymous_is_sent_to_login(self):
        for route in [reverse("profile"), reverse("view_avatar")]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, route)
            self.assertTrue(response.url.startswith("/login/"), route)

        response = self.client.post(reverse("remove_avatar"))
        self.assertTrue(response.url.startswith("/login/"))

    def test_every_role_sees_the_page(self):
        for username in ["miguel", "developer"]:
            self.login_as(username)
            response = self.client.get(reverse("profile"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Impormasyon ng Account")

    def test_account_made_outside_the_app_gets_a_profile(self):
        User.objects.create_user(username="walangprofile", password="abcd")
        self.client.login(username="walangprofile", password="abcd")

        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)
        self.assertEqual(Profile.objects.get(user__username="walangprofile").display_name, "walangprofile")


class ProfileTest(UserBase):
    def test_update_profile(self):
        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {"profile_form": "", "display_name": "Migs", "age": ""})

        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(messages_of(response), ["Naka-save na ang profile."])
        profile = Profile.objects.get(user=self.miguel)
        self.assertEqual(profile.display_name, "Migs")
        self.assertIsNone(profile.age)

    def test_invalid_profile_shows_the_error_next_to_the_field(self):
        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {"profile_form": "", "display_name": "Migs", "age": "200"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hindi tama ang edad.")
        self.assertEqual(Profile.objects.get(user=self.miguel).display_name, "Miguel")

    def test_avatar_upload_view_and_remove(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("view_avatar")).status_code, 404)

        response = self.client.post(reverse("profile"), {"avatar_form": "1", "avatar": image_upload()})
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(messages_of(response), ["Nai-save na ang larawan."])

        profile = Profile.objects.get(user=self.miguel)
        path = profile.avatar.path
        self.assertEqual(profile.avatar_mime, "image/png")

        response = self.client.get(reverse("view_avatar"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        response.close()

        self.assertEqual(self.client.get(reverse("remove_avatar")).status_code, 405)
        response = self.client.post(reverse("remove_avatar"))
        self.assertRedirects(response, reverse("profile"))
        self.assertFalse(Profile.objects.get(user=self.miguel).has_avatar)
        self.assertFalse(os.path.exists(path))

    def test_rejected_avatar_shows_the_error(self):
        self.login_as("miguel")
        bitmap = image_upload(name="a.bmp", image_format="BMP", content_type="image/bmp")
        response = self.client.post(reverse("profile"), {"avatar_form": "1", "avatar": bitmap})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hindi suportadong file type ng larawan.")


class PasswordTest(UserBase):
    def test_change_password_keeps_the_user_logged_in(self):
        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {
            "password_form": "", "current_password": "lihim1234", "new_password": "bago1", "confirm_password": "bago1",
        })

        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(messages_of(response), ["Nabago na ang password."])
        self.assertTrue(User.objects.get(pk=self.miguel.pk).check_password("bago1"))
        self.assertEqual(self.client.get(reverse("board")).status_code, 200)

    def test_wrong_current_password_changes_nothing(self):
        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {
            "password_form": "", "current_password": "mali", "new_password": "bago1", "confirm_password": "bago1",
        })

        self.assertContains(response, "Maling kasalukuyang password.")
        self.assertTrue(User.objects.get(pk=self.miguel.pk).check_password("lihim1234"))


class DeleteAccountTest(UserBase):
    def test_wrong_password_reopens_the_dialog_and_deletes_nothing(self):
        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {"delete_account_form": "", "password": "mali"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_delete_account_modal"])
        self.assertContains(response, "Maling password.")
        self.assertTrue(User.objects.filter(pk=self.miguel.pk).exists())

    def test_delete_removes_the_account_its_data_and_its_files(self):
        profile = Profile.objects.get(user=self.miguel)
        profile.set_avatar(random_upload_name("image/png"), image_upload(), "image/png")
        customization = Customization.objects.create(user=self.miguel, word="mama")
        customization.set_image(random_upload_name("image/png"), image_upload(), "image/png")
        customization.set_sound(random_upload_name("audio/webm"), sound_upload(), "audio/webm")
        WordUsage.record_use(self.miguel, "kain")
        Rating.objects.create(user=self.miguel, rating=5)
        paths = [profile.avatar.path, customization.image.path, customization.sound.path]

        ana_customization = Customization.objects.create(user=self.ana, word="mama")
        ana_customization.set_image(random_upload_name("image/png"), image_upload(), "image/png")

        self.login_as("miguel")
        response = self.client.post(reverse("profile"), {"delete_account_form": "", "password": "lihim1234"})

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(User.objects.filter(username="miguel").exists())
        self.assertFalse(Profile.objects.filter(user_id=self.miguel.pk).exists())
        self.assertFalse(Customization.objects.filter(user_id=self.miguel.pk).exists())
        self.assertFalse(WordUsage.objects.filter(user_id=self.miguel.pk).exists())
        self.assertFalse(Rating.objects.filter(user_id=self.miguel.pk).exists())
        for path in paths:
            self.assertFalse(os.path.exists(path), path)

        # Another account's data is untouched, and the session is over.
        self.assertTrue(os.path.exists(Customization.objects.get(user=self.ana).image.path))
        self.assertTrue(self.client.get(reverse("board")).url.startswith("/login/"))
