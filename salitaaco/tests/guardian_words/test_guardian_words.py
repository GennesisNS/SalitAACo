import shutil
from datetime import timedelta
from unittest import mock

from django.core.files.storage import default_storage
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.defaults.plans import DEFAULT_FREE_WORD_LIMIT, DEFAULT_PLUS_WORD_LIMIT
from salitaaco.forms.guardian_words.guardian_word import PLUS_PICTURES, GuardianWordForm
from salitaaco.models.added_word import AddedWord
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.payment import Payment
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.guardian_boards.test_guardian_boards import KEYCAPS, NOT_EMOJIS
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.text_to_speech.test_text_to_speech import SharedTileAudioTestMixin
from salitaaco.tests.users_base import UserBase, image_upload, make_guardian
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.family_voice import family_voice_directory, family_voice_progress, generate_family_voice_words
from salitaaco.utils.guardian_words import guardian_word_audio_directory
from salitaaco.utils.plans import approve_payment
from salitaaco.utils.tile_audio import tile_audio_file_name


@override_settings(ELEVENLABS_API_KEY="", ELEVENLABS_VOICE_ID="")
class GuardianWordsBase(UserBase):
    """
    Nanay is Miguel's guardian and on Plus; Tatay is Ana's, on Free. ElevenLabs
    is not set up unless a test says otherwise, so nothing is sent to it.
    """
    url = reverse("guardian_words")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben", children=[cls.ana])
        approve_payment(make_payment(cls.nanay), cls.developer)

    def add(self, word="Kuya Jun", board="Tao", emoji="👦"):
        return self.client.post(self.url, {"word_form": "", "board": board, "word": word, "emoji": emoji})

    def make_word(self, guardian, word, board="Tao", emoji="👦"):
        return GuardianWord.objects.create(guardian=guardian, board=board, word=word, emoji=emoji)

    def board_items(self, route, *args):
        categories = self.client.get(reverse(route, args=args)).context["board_data"]["categories"]
        return {category["name"]: [item["w"] for item in category["items"]] for category in categories}

    def set_limits(self, **limits):
        """Change the plans' limits, as an admin does on System Settings > Mga Plano."""
        setting = SiteSetting.load()
        for field, value in limits.items():
            setattr(setting, field, value)
        setting.save()


class GuardianWordFormTest(GuardianWordsBase):
    def test_a_word_no_tile_has_yet(self):
        self.make_word(self.nanay, "Kuya Jun")
        for word, error in [
            ("Isda", "May tile na para sa salitang ito."),  # a default word
            ("kuya  JUN", "May tile ka na para sa salitang ito."),  # her own, spelled otherwise
        ]:
            form = GuardianWordForm({"board": "Tao", "word": word, "emoji": "👦"}, guardian=self.nanay)
            self.assertEqual(form.errors["word"], [error], word)
        # Another guardian's word is no concern of hers.
        self.assertTrue(GuardianWordForm({"board": "Tao", "word": "Kuya Jun", "emoji": "👦"}, guardian=self.tatay).is_valid())

    def test_keycap_number_emojis_are_emojis_and_plain_numbers_are_not(self):
        for keycap in KEYCAPS:
            form = GuardianWordForm({"board": "Tao", "word": "Kuya Jun", "emoji": keycap}, guardian=self.nanay)
            self.assertTrue(form.is_valid(), keycap)
            self.assertEqual(form.cleaned_data["emoji"], keycap)
        for number in NOT_EMOJIS:
            form = GuardianWordForm({"board": "Tao", "word": "Kuya Jun", "emoji": number}, guardian=self.nanay)
            self.assertEqual(form.errors["emoji"], ["Emoji ang ilagay, hindi titik o numero."], number)


class GuardianWordsPageTest(GuardianWordsBase):
    def test_only_guardians_open_the_page_and_it_is_in_the_sidebar(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')

    def test_on_plus_a_tile_is_added_and_counted(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, f"0 sa {DEFAULT_PLUS_WORD_LIMIT} na sariling tile")
        self.assertContains(response, 'name="word_form"')

        response = self.add()
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naidagdag na ang “Kuya Jun” sa board na “Tao”."])
        word = GuardianWord.objects.get()
        self.assertEqual((word.guardian, word.board, word.word, word.emoji), (self.nanay, "Tao", "Kuya Jun", "👦"))
        self.assertContains(self.client.get(self.url), f"1 sa {DEFAULT_PLUS_WORD_LIMIT} na sariling tile")

    def test_a_tile_is_added_with_a_keycap_number_emoji(self):
        self.login_as("nanay")
        self.assertRedirects(self.add(word="tatlo", board="Bagay", emoji="3️⃣"), self.url)
        self.assertEqual(GuardianWord.objects.get().emoji, "3️⃣")

    def test_on_free_with_no_tiles_allowed_nothing_can_be_added(self):
        self.assertEqual(DEFAULT_FREE_WORD_LIMIT, 0)
        expected = f"Para sa SalitAACo Plus ang sariling tile: hanggang {DEFAULT_PLUS_WORD_LIMIT}. Kunin ang Plus para makapagdagdag."
        self.login_as("tatay")
        response = self.client.get(self.url)
        self.assertContains(response, expected)
        self.assertContains(response, f'href="{reverse("plan")}"')
        self.assertNotContains(response, 'name="word_form"')

        response = self.add()
        self.assertEqual(messages_of(response), [expected])
        self.assertFalse(GuardianWord.objects.exists())

    def test_free_has_its_own_limit_an_admin_sets(self):
        self.set_limits(free_word_limit=1)
        self.login_as("tatay")
        self.assertContains(self.client.get(self.url), "0 sa 1 na sariling tile")
        self.assertRedirects(self.add(word="Lolo Ben"), self.url)

        response = self.client.get(self.url)
        self.assertContains(response, "Hanggang 1 na sariling tile lang sa libreng plano.")
        self.assertEqual(messages_of(self.add(word="Lola Nena")), [
            f"Hanggang 1 na sariling tile lang sa libreng plano. Kunin ang SalitAACo Plus para makapagdagdag ng hanggang {DEFAULT_PLUS_WORD_LIMIT}.",
        ])
        self.assertEqual(GuardianWord.objects.filter(guardian=self.tatay).count(), 1)

    def test_the_limit_is_shared_by_every_board_and_set_by_an_admin(self):
        self.set_limits(plus_word_limit=2)
        self.make_word(self.nanay, "Kuya Jun", board="Tao")
        self.make_word(self.nanay, "sinigang", board="Pagkain")

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "2 sa 2 na sariling tile")
        self.assertContains(response, "Naabot mo na ang 2 na sariling tile.")
        self.assertNotContains(response, 'name="word_form"')
        self.assertNotContains(response, 'href="/dashboard/plan/">Kunin ang Plus')

        response = self.add(word="bola", board="Bagay")
        self.assertEqual(messages_of(response), ["Naabot mo na ang 2 na sariling tile. Magbura muna ng isa para makapagdagdag ng bago."])
        self.assertEqual(GuardianWord.objects.filter(guardian=self.nanay).count(), 2)

        # Raising the limit opens it again.
        self.set_limits(plus_word_limit=3)
        self.assertRedirects(self.add(word="bola", board="Bagay"), self.url)
        self.assertEqual(GuardianWord.objects.filter(guardian=self.nanay).count(), 3)

    def test_over_the_limit_the_oldest_show_and_the_rest_are_hidden(self):
        for word in ["Kuya Jun", "sinigang", "bola"]:
            self.make_word(self.nanay, word, board="Tao")
        self.set_limits(plus_word_limit=2)

        self.login_as("miguel")
        self.assertEqual(self.board_items("board")["Tao"][-2:], ["Kuya Jun", "sinigang"])
        self.assertNotIn("bola", self.board_items("board")["Tao"])
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "Nakatago muna sa mga board ang 1 sa mga sariling tile mo")
        self.assertEqual([row["shown"] for row in response.context["words"]], [True, True, False])
        self.assertEqual(GuardianWord.objects.count(), 3)

    def test_deleting_a_tile_takes_its_counts_with_it(self):
        word = self.make_word(self.nanay, "Kuya Jun")
        for user in [self.miguel, self.nanay.user]:
            WordUsage.record_use(user, "Kuya Jun")
            DailyUsage.record(user, DailyUsage.WORD, "Kuya Jun")
        WordUsage.record_use(self.ana, "Kuya Jun")  # another family's, untouched

        self.login_as("nanay")
        self.client.post(reverse("remove_guardian_word", args=[word.uuid]))
        self.assertEqual(list(WordUsage.objects.filter(word="Kuya Jun").values_list("user__username", flat=True)), ["ana"])
        self.assertFalse(DailyUsage.objects.filter(name="Kuya Jun").exists())

    def test_only_shown_boards_can_be_picked_and_the_word_is_checked(self):
        self.login_as("nanay")
        response = self.add(word="isda")
        self.assertContains(response, "May tile na para sa salitang ito.")
        response = self.add(board="Walang ganito")
        self.assertContains(response, "Walang ganitong board.")
        self.assertFalse(GuardianWord.objects.exists())

    def test_deleting_is_her_own_and_works_on_free_too(self):
        own = self.make_word(self.tatay, "Lolo Ben")
        other = self.make_word(self.nanay, "Kuya Jun")

        self.login_as("tatay")
        self.assertEqual(self.client.post(reverse("remove_guardian_word", args=[other.uuid])).status_code, 404)
        response = self.client.post(reverse("remove_guardian_word", args=[own.uuid]))
        self.assertRedirects(response, self.url)
        self.assertEqual(list(GuardianWord.objects.all()), [other])


class GuardianWordsOnBoardsTest(GuardianWordsBase):
    def test_on_plus_her_tiles_are_on_her_board_and_every_childs(self):
        self.make_word(self.nanay, "Kuya Jun", board="Tao")
        self.make_word(self.nanay, "sinigang", board="Pagkain", emoji="🍲")

        self.login_as("nanay")
        own = self.board_items("board")
        child = self.board_items("child_board", self.nanay.children.get().uuid)
        for items in [own, child]:
            self.assertEqual(items["Tao"][-1], "Kuya Jun")
            self.assertEqual(items["Pagkain"][-1], "sinigang")

        # Miguel sees them on his own board, and the other family does not.
        self.login_as("miguel")
        self.assertEqual(self.board_items("board")["Tao"][-1], "Kuya Jun")
        self.login_as("ana")
        self.assertNotIn("Kuya Jun", self.board_items("board")["Tao"])
        self.login_as("developer")
        self.assertNotIn("Kuya Jun", self.board_items("board")["Tao"])

    def test_when_plus_ends_the_tiles_are_hidden_but_kept(self):
        self.make_word(self.nanay, "Kuya Jun", board="Tao")
        Payment.objects.filter(guardian=self.nanay).update(ends_at=timezone.now() - timedelta(days=1))

        self.login_as("miguel")
        self.assertNotIn("Kuya Jun", self.board_items("board")["Tao"])
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "Nakatago muna sa mga board ang 1 sa mga sariling tile mo")
        self.assertTrue(GuardianWord.objects.filter(word="Kuya Jun").exists())

        # Renewing brings them back.
        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("miguel")
        self.assertEqual(self.board_items("board")["Tao"][-1], "Kuya Jun")

    def test_a_word_an_admin_adds_later_is_not_shown_twice(self):
        self.make_word(self.nanay, "pandesal", board="Pagkain")
        AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")

        self.login_as("miguel")
        self.assertEqual(self.board_items("board")["Pagkain"].count("pandesal"), 1)

    def test_a_tile_on_a_board_the_child_does_not_see_is_not_shown(self):
        self.make_word(self.nanay, "Kuya Jun", board="Tao")
        self.nanay.children.get().hidden_boards.create(board="Tao")

        self.login_as("miguel")
        self.assertNotIn("Tao", self.board_items("board"))


class GuardianWordPictureTest(GuardianWordsBase):
    """On Plus, a tile's symbol may be an uploaded picture in place of an emoji."""

    def add_with_picture(self, word="Kuya Jun", board="Tao"):
        return self.client.post(self.url, {
            "word_form": "", "board": board, "word": word, "icon_kind": "image", "emoji": "",
            "icon_image": image_upload(),
        })

    def tile(self, word, route="board", *args):
        categories = self.client.get(reverse(route, args=args)).context["board_data"]["categories"]
        return next(item for category in categories for item in category["items"] if item["w"] == word)

    def test_on_plus_the_form_offers_the_picture(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="icon_kind" value="image"')
        self.assertContains(response, "📷 Pumili ng larawan")
        self.assertNotContains(response, PLUS_PICTURES)

    def test_a_tile_with_a_picture_is_on_the_boards_of_her_family_only(self):
        self.login_as("nanay")
        self.assertRedirects(self.add_with_picture(), self.url)
        word = GuardianWord.objects.get()
        self.assertTrue(word.icon_image.name.startswith("guardian-word-images/"))
        self.assertTrue(word.icon_image.name.endswith(".webp"))
        self.assertEqual((word.emoji, word.icon_mime), ("", "image/webp"))

        image_url = reverse("guardian_word_image", args=[word.uuid])
        self.assertContains(self.client.get(self.url), f'<img class="symbolImage" src="{image_url}?v=')
        self.assertTrue(self.tile("Kuya Jun")["img"].startswith(image_url))
        self.assertTrue(self.tile("Kuya Jun", "child_board", self.nanay.children.get().uuid)["img"].startswith(image_url))
        self.login_as("miguel")
        self.assertTrue(self.tile("Kuya Jun")["img"].startswith(image_url))

        for username, status in [("nanay", 200), ("miguel", 200), ("tatay", 404), ("ana", 404), ("developer", 404)]:
            self.login_as(username)
            self.assertEqual(self.client.get(image_url).status_code, status, username)

    def test_a_tile_with_a_picture_counts_toward_the_limit(self):
        self.set_limits(plus_word_limit=1)
        self.login_as("nanay")
        self.add_with_picture()
        response = self.add(word="sinigang", board="Pagkain")
        self.assertEqual(messages_of(response)[-1], "Naabot mo na ang 1 na sariling tile. Magbura muna ng isa para makapagdagdag ng bago.")
        self.assertEqual(GuardianWord.objects.count(), 1)

    def test_on_free_the_symbol_is_an_emoji(self):
        self.set_limits(free_word_limit=2)
        self.login_as("tatay")
        response = self.client.get(self.url)
        self.assertContains(response, PLUS_PICTURES)
        self.assertNotContains(response, 'name="icon_kind" value="image"')
        self.assertNotContains(response, "📷 Pumili ng larawan")

        response = self.add_with_picture(word="Lolo Ben")
        self.assertContains(response, PLUS_PICTURES)
        self.assertFalse(GuardianWord.objects.exists())
        # An emoji tile is still hers to add.
        self.assertRedirects(self.add(word="Lolo Ben"), self.url)

    def test_deleting_the_tile_its_board_or_her_account_deletes_its_picture(self):
        self.login_as("nanay")
        self.add_with_picture()
        name = GuardianWord.objects.get().icon_image.name
        self.client.post(reverse("remove_guardian_word", args=[GuardianWord.objects.get().uuid]))
        self.assertFalse(default_storage.exists(name))

        self.nanay.boards.create(name="Bahay ni Lola", emoji="🏡")
        self.add_with_picture(word="Lola Nena", board="Bahay ni Lola")
        name = GuardianWord.objects.get().icon_image.name
        board = self.nanay.boards.get()
        self.client.post(reverse("remove_own_board", args=[self.nanay.children.get().uuid, board.uuid]))
        self.assertFalse(default_storage.exists(name))

        # A guardian's account goes only without children, so a childless guardian's is deleted.
        tito = make_guardian("tito", "Tito Ben")
        approve_payment(make_payment(tito), self.developer)
        self.login_as("tito")
        self.add_with_picture()
        name = GuardianWord.objects.get(guardian=tito).icon_image.name
        delete_user_account(tito.user)
        self.assertFalse(default_storage.exists(name))


@override_settings(ELEVENLABS_API_KEY="susi", ELEVENLABS_VOICE_ID="pinoy-boses")
class GuardianWordAudioTest(SharedTileAudioTestMixin, GuardianWordsBase):
    """A new tile is voiced in the shared voice and in each of the guardian's family voices."""

    def setUp(self):
        super().setUp()
        # The guardians are the same in every test of the class, and so is their folder of
        # audio: emptied after each test, as the database is, so one test's files do not reach the next.
        self.addCleanup(shutil.rmtree, guardian_word_audio_directory(self.nanay).parent, ignore_errors=True)
        patcher = mock.patch("salitaaco.utils.family_voice.ElevenLabs")
        self.elevenlabs = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.elevenlabs.text_to_speech.side_effect = lambda voice_id, word: f"{voice_id}: {word}".encode()

    def make_family_voice(self, name):
        voice = FamilyVoice.objects.create(
            guardian=self.nanay, name=name, elevenlabs_voice_id=f"boses-{name}",
            consent_at=timezone.now(), consent_version=TERMS_VERSION,
        )
        ChildAccount.objects.filter(user=self.miguel).update(family_voice=voice)
        return voice

    def family_audio(self, voice, word):
        return family_voice_directory(voice) / tile_audio_file_name(word)

    def shared_audio(self, guardian, word):
        """A guardian's tile in the shared voice: in their own folder under media/, not in static/."""
        return guardian_word_audio_directory(guardian) / tile_audio_file_name(word)

    def test_adding_a_tile_voices_it_in_the_shared_voice_and_every_family_voice(self):
        lola, lolo = self.make_family_voice("Lola"), self.make_family_voice("Lolo")
        self.login_as("nanay")
        response = self.add()

        self.assertEqual(messages_of(response), ["Naidagdag na ang “Kuya Jun” sa board na “Tao”."])
        self.assertEqual(
            sorted(call.args for call in self.elevenlabs.text_to_speech.call_args_list),
            [("boses-Lola", "Kuya Jun"), ("boses-Lolo", "Kuya Jun"), ("pinoy-boses", "Kuya Jun")],
        )
        self.assertEqual(self.shared_audio(self.nanay, "Kuya Jun").read_bytes(), b"pinoy-boses: Kuya Jun")
        self.assertEqual(self.family_audio(lola, "Kuya Jun").read_bytes(), b"boses-Lola: Kuya Jun")
        self.assertEqual(self.family_audio(lolo, "Kuya Jun").read_bytes(), b"boses-Lolo: Kuya Jun")
        # The vocabulary's folder in static/ is left alone.
        self.assertEqual(list(self.audio_directory.iterdir()), [])

        # The page plays it, and the boards use it: Miguel hears it in his family voice.
        word = GuardianWord.objects.get()
        play_url = reverse("play_guardian_word", args=[word.uuid])
        self.assertContains(self.client.get(self.url), f'data-preview="{play_url}?v=')
        tile_audio = self.client.get(reverse("board")).context["board_data"]["tile_audio"]
        self.assertTrue(tile_audio["Kuya Jun"].startswith(f"{play_url}?v="))
        self.login_as("miguel")
        tile_audio = self.client.get(reverse("board")).context["board_data"]["tile_audio"]
        self.assertTrue(tile_audio["Kuya Jun"].startswith(reverse("play_family_voice_word", args=[lolo.uuid, "kuya-jun"])))

    def test_when_elevenlabs_refuses_the_tile_stays_and_can_be_voiced_later(self):
        self.elevenlabs.text_to_speech.side_effect = ElevenLabsError("ElevenLabs answered 401", 401)
        self.login_as("nanay")
        response = self.add()

        self.assertEqual(messages_of(response), [
            "Naidagdag na ang “Kuya Jun” sa board na “Tao”.",
            "Hindi pa nagawa ang boses nito, kaya boses muna ng device ang gagamitin. Subukan muli mamaya.",
        ])
        word = GuardianWord.objects.get()
        self.assertContains(self.client.get(self.url), f'action="{reverse("voice_guardian_word", args=[word.uuid])}"')

        self.elevenlabs.text_to_speech.side_effect = lambda voice_id, text: b"mp3"
        response = self.client.post(reverse("voice_guardian_word", args=[word.uuid]))
        self.assertEqual(messages_of(response), ["Nagawa na ang boses ng “Kuya Jun”."])
        self.assertTrue(self.shared_audio(self.nanay, "Kuya Jun").exists())

    def test_audio_already_made_is_not_made_again(self):
        shared = self.shared_audio(self.nanay, "Kuya Jun")
        shared.parent.mkdir(parents=True)
        shared.write_bytes(b"dati na")
        self.login_as("nanay")
        self.add()
        self.elevenlabs.text_to_speech.assert_not_called()
        self.assertEqual(shared.read_bytes(), b"dati na")

    def test_only_the_guardian_and_her_children_hear_her_tile(self):
        self.login_as("nanay")
        self.add()
        url = reverse("play_guardian_word", args=[GuardianWord.objects.get().uuid])

        for username in ["nanay", "miguel"]:
            self.login_as(username)
            response = self.client.get(url)
            self.assertEqual((response.status_code, response["Content-Type"]), (200, "audio/mpeg"), username)
            self.assertEqual(b"".join(response.streaming_content), b"pinoy-boses: Kuya Jun")
        for username in ["tatay", "ana", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 404, username)
        self.client.logout()
        self.assertRedirects(self.client.get(url), f"/login/?next={url}")

    @override_settings(ELEVENLABS_API_KEY="")
    def test_without_elevenlabs_the_tile_speaks_in_the_devices_voice(self):
        self.login_as("nanay")
        response = self.add()
        self.assertEqual(len(messages_of(response)), 1)
        self.elevenlabs.text_to_speech.assert_not_called()
        self.assertContains(self.client.get(self.url), "Boses ng device")

    def test_a_family_voice_made_later_says_the_guardians_tiles_too(self):
        self.make_word(self.nanay, "Kuya Jun")
        voice = self.make_family_voice("Lola")
        done, total = family_voice_progress(voice)
        self.assertEqual(done, 0)

        generate_family_voice_words(voice, total)
        self.assertTrue(self.family_audio(voice, "Kuya Jun").exists())
        self.assertEqual(family_voice_progress(voice), (total, total))

    def test_each_family_has_its_own_audio_and_deleting_removes_only_its_own(self):
        voice = self.make_family_voice("Lola")
        tito = make_guardian("tito", "Tito Ben")
        approve_payment(make_payment(tito), self.developer)
        for username in ["nanay", "tito"]:
            self.login_as(username)
            self.add()
        nanays, titos = self.shared_audio(self.nanay, "Kuya Jun"), self.shared_audio(tito, "Kuya Jun")
        self.assertTrue(nanays.exists() and titos.exists())

        self.login_as("nanay")
        self.client.post(reverse("remove_guardian_word", args=[GuardianWord.objects.get(guardian=self.nanay).uuid]))
        self.assertFalse(nanays.exists())
        self.assertFalse(self.family_audio(voice, "Kuya Jun").exists())
        self.assertTrue(titos.exists())

        delete_user_account(tito.user)
        self.assertFalse(guardian_word_audio_directory(tito).exists())

    def test_a_hidden_tile_is_not_voiced_again(self):
        word = self.make_word(self.tatay, "Lolo Ben")  # Free allows none, so it is hidden
        self.login_as("tatay")
        response = self.client.post(reverse("voice_guardian_word", args=[word.uuid]))
        self.assertEqual(messages_of(response), ["Nakatago ang tile na ito dahil lampas na ito sa limit ng plano mo."])
        self.elevenlabs.text_to_speech.assert_not_called()


class PlanLimitsTest(GuardianWordsBase):
    LIMITS = {"free_word_limit": "3", "plus_word_limit": "30", "free_board_limit": "1", "plus_board_limit": "8"}

    def test_an_admin_sets_the_four_limits_on_mga_plano(self):
        url = reverse("system_plans")
        self.login_as("developer")
        page = self.client.get(url)
        for field, value in [("free_word_limit", 0), ("plus_word_limit", 20), ("free_board_limit", 0), ("plus_board_limit", 5)]:
            self.assertContains(page, f'name="{field}" value="{value}"')

        response = self.client.post(url, {"limits_form": "", **self.LIMITS})
        self.assertRedirects(response, f"{url}#limits")
        self.assertEqual(messages_of(response), ["Naka-save na ang mga limit ng Free at Plus."])
        setting = SiteSetting.load()
        self.assertEqual(
            (setting.free_word_limit, setting.plus_word_limit, setting.free_board_limit, setting.plus_board_limit),
            (3, 30, 1, 8),
        )

        response = self.client.post(url, {"limits_form": "", **self.LIMITS, "plus_board_limit": "-1"})
        self.assertContains(response, "Hindi tama ang bilang.")
        self.assertEqual(SiteSetting.load().plus_board_limit, 8)

    def test_the_limits_are_grouped_by_plan_below_the_plan_cards(self):
        self.login_as("developer")
        content = self.client.get(reverse("system_plans")).content.decode()
        # Below the plan cards, Free's two fields together, then the paid plans' two.
        order = [
            'name="plus-name"', "<h2>Mga Limit ng Plano</h2>",
            '<h3 id="freeLimitsTitle">Free</h3>', 'name="free_word_limit"', 'name="free_board_limit"',
            '<h3 id="paidLimitsTitle">Mga bayad na plano</h3>', "Para sa mga naka-SalitAACo Plus.",
            'name="plus_word_limit"', 'name="plus_board_limit"', 'name="limits_form"',
        ]
        positions = [content.index(text) for text in order]
        self.assertEqual(positions, sorted(positions))

    def test_general_no_longer_has_them(self):
        self.login_as("developer")
        response = self.client.get(reverse("system_general"))
        self.assertNotContains(response, 'name="limits_form"')
        self.assertNotContains(response, 'name="plus_word_limit"')
        self.assertContains(response, f'href="{reverse("system_plans")}#limits"')

    def test_only_admins_set_them(self):
        self.login_as("nanay")
        self.client.post(reverse("system_plans"), {"limits_form": "", **self.LIMITS})
        self.assertEqual(SiteSetting.load().plus_word_limit, DEFAULT_PLUS_WORD_LIMIT)
