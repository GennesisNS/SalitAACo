import os

from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.models.customization import Customization
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.users_base import UserBase, image_upload, sound_upload


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class BoardAccessTest(UserBase):
    def test_anonymous_is_sent_to_login(self):
        customization = Customization.objects.create(user=self.miguel, word="mama")
        routes = [
            reverse("board"),
            reverse("list_frequent_words"),
            reverse("view_customization_image", args=[customization.uuid]),
            reverse("view_customization_sound", args=[customization.uuid]),
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, route)
            self.assertTrue(response.url.startswith("/login/"), route)

        for route in [reverse("increment_word_usage"), reverse("reset_customization", args=[customization.uuid])]:
            response = self.client.post(route)
            self.assertEqual(response.status_code, 302, route)
            self.assertTrue(response.url.startswith("/login/"), route)

    def test_every_role_sees_the_board(self):
        for username in ["miguel", "developer"]:
            self.login_as(username)
            response = self.client.get(reverse("board"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Pindutin ang mga salita...")

    def test_board_carries_the_vocabulary_and_the_users_data(self):
        self.login_as("miguel")
        Customization.objects.create(user=self.miguel, word="mama")
        Customization.objects.create(user=self.ana, word="papa")
        WordUsage.record_use(self.miguel, "kain")

        board_data = self.client.get(reverse("board")).context["board_data"]

        self.assertEqual([category["name"] for category in board_data["categories"]],
                         ["Tao", "Bagay", "Pagkain", "Lugar", "Pandiwa", "Pakiramdam"])
        self.assertEqual([item["word"] for item in board_data["customizations"]], ["mama"])
        self.assertEqual(board_data["frequent_words"], [{"word": "kain", "use_count": 1}])

    def test_sidebar_shows_the_admin_dashboard_to_administrators_only(self):
        self.login_as("miguel")
        self.assertNotContains(self.client.get(reverse("board")), reverse("analytics"))
        self.login_as("developer")
        self.assertContains(self.client.get(reverse("board")), reverse("analytics"))


class TileCustomizationTest(UserBase):
    def upload_image(self, word="mama", **upload):
        return self.client.post(reverse("board"), {"tile_image_form": "1", "word": word, "image": image_upload(**upload)})

    def upload_sound(self, word="mama", **upload):
        return self.client.post(reverse("board"), {"tile_sound_form": "1", "word": word, "sound": sound_upload(**upload)})

    def test_upload_image_then_sound_keeps_one_row_per_word(self):
        self.login_as("miguel")

        response = self.upload_image()
        self.assertRedirects(response, reverse("board"))
        self.assertEqual(messages_of(response), ["Nai-save na ang larawan ng tile."])

        response = self.upload_sound()
        self.assertRedirects(response, reverse("board"))
        self.assertEqual(messages_of(response), ["Nai-save na ang tunog ng tile."])

        customization = Customization.objects.get(user=self.miguel, word="mama")
        self.assertTrue(customization.has_image)
        self.assertTrue(customization.has_sound)
        self.assertEqual(customization.image_mime, "image/png")
        self.assertEqual(customization.sound_mime, "audio/webm")
        self.assertTrue(customization.image.name.endswith(".png"))
        self.assertNotIn("larawan", customization.image.name)

    def test_replacing_an_image_removes_the_old_file(self):
        self.login_as("miguel")
        self.upload_image()
        old_path = Customization.objects.get(word="mama").image.path

        self.upload_image(name="bago.jpg", image_format="JPEG", content_type="image/jpeg")

        customization = Customization.objects.get(word="mama")
        self.assertEqual(customization.image_mime, "image/jpeg")
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(customization.image.path))

    def test_rejected_upload_shows_the_reason_and_saves_nothing(self):
        self.login_as("miguel")
        response = self.upload_image(name="larawan.bmp", image_format="BMP", content_type="image/bmp")
        self.assertRedirects(response, reverse("board"))
        self.assertEqual(messages_of(response), ["Hindi suportadong file type ng larawan."])
        self.assertFalse(Customization.objects.exists())

    def test_owner_is_served_the_files(self):
        self.login_as("miguel")
        self.upload_image()
        self.upload_sound()
        customization = Customization.objects.get(word="mama")

        response = self.client.get(reverse("view_customization_image", args=[customization.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "private, max-age=86400")
        self.assertTrue(b"".join(response.streaming_content).startswith(b"\x89PNG"))

        response = self.client.get(reverse("view_customization_sound", args=[customization.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "audio/webm")
        response.close()

    def test_other_users_cannot_see_or_reset_a_customization(self):
        self.login_as("miguel")
        self.upload_image()
        customization = Customization.objects.get(word="mama")

        self.login_as("ana")
        self.assertEqual(self.client.get(reverse("view_customization_image", args=[customization.uuid])).status_code, 404)
        self.assertEqual(self.client.post(reverse("reset_customization", args=[customization.uuid])).status_code, 404)
        self.assertTrue(Customization.objects.filter(pk=customization.pk).exists())

    def test_missing_media_is_not_found(self):
        self.login_as("miguel")
        self.upload_image()
        customization = Customization.objects.get(word="mama")
        self.assertEqual(self.client.get(reverse("view_customization_sound", args=[customization.uuid])).status_code, 404)

    def test_reset_deletes_the_row_and_its_files(self):
        self.login_as("miguel")
        self.upload_image()
        self.upload_sound()
        customization = Customization.objects.get(word="mama")
        paths = [customization.image.path, customization.sound.path]

        self.assertEqual(self.client.get(reverse("reset_customization", args=[customization.uuid])).status_code, 405)
        response = self.client.post(reverse("reset_customization", args=[customization.uuid]))

        self.assertRedirects(response, reverse("board"))
        self.assertFalse(Customization.objects.exists())
        for path in paths:
            self.assertFalse(os.path.exists(path))


class WordUsageTest(UserBase):
    def tap(self, word):
        return self.client.post(reverse("increment_word_usage"), {"word": word})

    def test_taps_are_counted_per_user(self):
        self.login_as("miguel")
        for word in ["kain", "kain", "inom"]:
            self.assertEqual(self.tap(word).json(), {"ok": True})
        self.login_as("ana")
        self.tap("kain")

        self.assertEqual(WordUsage.objects.get(user=self.miguel, word="kain").use_count, 2)
        self.assertEqual(WordUsage.objects.get(user=self.miguel, word="inom").use_count, 1)
        self.assertEqual(WordUsage.objects.get(user=self.ana, word="kain").use_count, 1)

    def test_tap_without_a_word_is_rejected(self):
        self.login_as("miguel")
        response = self.tap("  ")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"ok": False, "error": "Walang word."})
        self.assertFalse(WordUsage.objects.exists())

    def test_tap_needs_post(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("increment_word_usage")).status_code, 405)

    def test_frequent_words_are_most_used_first(self):
        self.login_as("miguel")
        for word in ["inom", "kain", "kain", "laro", "laro", "laro"]:
            self.tap(word)

        response = self.client.get(reverse("list_frequent_words"))
        self.assertEqual(response.json()["items"], [
            {"word": "laro", "use_count": 3},
            {"word": "kain", "use_count": 2},
            {"word": "inom", "use_count": 1},
        ])

        limited = self.client.get(reverse("list_frequent_words"), {"limit": "1"}).json()["items"]
        self.assertEqual(limited, [{"word": "laro", "use_count": 3}])

        # An out-of-range or unreadable limit falls back to a usable one.
        self.assertEqual(len(self.client.get(reverse("list_frequent_words"), {"limit": "0"}).json()["items"]), 1)
        self.assertEqual(len(self.client.get(reverse("list_frequent_words"), {"limit": "abc"}).json()["items"]), 3)
