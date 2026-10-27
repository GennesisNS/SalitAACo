import os

from django.contrib.messages import get_messages
from django.urls import NoReverseMatch, reverse

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
            self.assertContains(response, "▶ Patugtugin")

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
    """A tile's own recording, made on the board. A tile's picture is not changed on the board."""

    def upload_sound(self, word="mama", **upload):
        return self.client.post(reverse("board"), {"tile_sound_form": "1", "word": word, "sound": sound_upload(**upload)})

    def test_a_recording_is_kept_for_the_word(self):
        self.login_as("miguel")
        response = self.upload_sound()
        self.assertRedirects(response, reverse("board"))
        self.assertEqual(messages_of(response), ["Nai-save na ang tunog ng tile."])

        customization = Customization.objects.get(user=self.miguel, word="mama")
        self.assertTrue(customization.has_sound)
        self.assertEqual(customization.sound_mime, "audio/webm")
        self.assertTrue(customization.sound.name.startswith("customization-sounds/"))

    def test_a_new_recording_removes_the_old_file(self):
        self.login_as("miguel")
        self.upload_sound()
        old_path = Customization.objects.get(word="mama").sound.path
        self.upload_sound(content_type="audio/ogg")

        customization = Customization.objects.get(word="mama")
        self.assertEqual(customization.sound_mime, "audio/ogg")
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(customization.sound.path))

    def test_there_is_no_picture_to_change_on_the_board(self):
        self.login_as("miguel")
        response = self.client.get(reverse("board"))
        self.assertNotContains(response, "tileImageForm")
        with self.assertRaises(NoReverseMatch):
            reverse("view_customization_image", args=[Customization.objects.create(user=self.miguel, word="mama").uuid])
        # A picture sent the old way is not taken.
        response = self.client.post(reverse("board"), {"tile_image_form": "1", "word": "papa", "image": image_upload()})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customization.objects.filter(word="papa").exists())

    def test_a_recording_is_only_for_a_tile_on_the_board(self):
        self.login_as("miguel")
        response = self.upload_sound(word="kahit ano")
        self.assertRedirects(response, reverse("board"))
        self.assertEqual(messages_of(response)[-1], "Walang ganitong tile sa board.")
        self.assertFalse(Customization.objects.exists())
        # A verb tile is set up in the form it shows.
        self.assertEqual(messages_of(self.upload_sound(word="kumain"))[-1], "Nai-save na ang tunog ng tile.")

    def test_owner_is_served_the_recording(self):
        self.login_as("miguel")
        self.upload_sound()
        customization = Customization.objects.get(word="mama")

        response = self.client.get(reverse("view_customization_sound", args=[customization.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "audio/webm")
        self.assertEqual(response["Cache-Control"], "private, max-age=86400")
        response.close()

    def test_other_users_cannot_hear_or_reset_a_customization(self):
        self.login_as("miguel")
        self.upload_sound()
        customization = Customization.objects.get(word="mama")

        self.login_as("ana")
        self.assertEqual(self.client.get(reverse("view_customization_sound", args=[customization.uuid])).status_code, 404)
        self.assertEqual(self.client.post(reverse("reset_customization", args=[customization.uuid])).status_code, 404)
        self.assertTrue(Customization.objects.filter(pk=customization.pk).exists())

    def test_missing_media_is_not_found(self):
        self.login_as("miguel")
        customization = Customization.objects.create(user=self.miguel, word="mama")
        self.assertEqual(self.client.get(reverse("view_customization_sound", args=[customization.uuid])).status_code, 404)

    def test_reset_deletes_the_row_and_its_recording(self):
        self.login_as("miguel")
        self.upload_sound()
        customization = Customization.objects.get(word="mama")
        path = customization.sound.path

        self.assertEqual(self.client.get(reverse("reset_customization", args=[customization.uuid])).status_code, 405)
        response = self.client.post(reverse("reset_customization", args=[customization.uuid]))

        self.assertRedirects(response, reverse("board"))
        self.assertFalse(Customization.objects.exists())
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

    def test_only_a_word_on_the_users_boards_is_counted(self):
        self.login_as("miguel")
        # A word, a verb in one of its forms, and a quick word of the Home screen are tiles.
        for word in ["isda", "kumain", "oo"]:
            self.assertEqual(self.tap(word).json(), {"ok": True}, word)
        # Anything else is not counted, so it never reaches the admin's lists.
        for word in ["kahit ano", "<script>", "Kuya Jun"]:
            response = self.tap(word)
            self.assertEqual(response.status_code, 400, word)
            self.assertEqual(response.json(), {"ok": False, "error": "Walang ganitong tile sa board."})
        self.assertEqual(sorted(WordUsage.objects.values_list("word", flat=True)), ["isda", "kumain", "oo"])

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
