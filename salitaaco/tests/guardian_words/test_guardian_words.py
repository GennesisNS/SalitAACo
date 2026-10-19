from datetime import timedelta
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.defaults.family_voice import TERMS_VERSION
from salitaaco.defaults.plans import DEFAULT_GUARDIAN_WORD_LIMIT
from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.models.added_word import AddedWord
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.payment import Payment
from salitaaco.models.site_setting import SiteSetting
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.text_to_speech.test_text_to_speech import SharedTileAudioTestMixin
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.family_voice import family_voice_directory, family_voice_progress, generate_family_voice_words
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

    def set_limit(self, limit):
        setting = SiteSetting.load()
        setting.guardian_word_limit = limit
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
        self.assertContains(response, f"0 sa {DEFAULT_GUARDIAN_WORD_LIMIT} na sariling tile")
        self.assertContains(response, 'name="word_form"')

        response = self.add()
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naidagdag na ang “Kuya Jun” sa board na “Tao”."])
        word = GuardianWord.objects.get()
        self.assertEqual((word.guardian, word.board, word.word, word.emoji), (self.nanay, "Tao", "Kuya Jun", "👦"))
        self.assertContains(self.client.get(self.url), f"1 sa {DEFAULT_GUARDIAN_WORD_LIMIT} na sariling tile")

    def test_on_free_nothing_can_be_added(self):
        self.login_as("tatay")
        response = self.client.get(self.url)
        self.assertContains(response, "Para sa SalitAACo Plus lang ang sariling tile.")
        self.assertContains(response, f'href="{reverse("plan")}"')
        self.assertNotContains(response, 'name="word_form"')

        response = self.add()
        self.assertEqual(messages_of(response), ["Para sa SalitAACo Plus lang ang pagdagdag ng sariling tile."])
        self.assertFalse(GuardianWord.objects.exists())

    def test_the_limit_is_shared_by_every_board_and_set_by_an_admin(self):
        self.set_limit(2)
        self.make_word(self.nanay, "Kuya Jun", board="Tao")
        self.make_word(self.nanay, "sinigang", board="Pagkain")

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, "2 sa 2 na sariling tile")
        self.assertContains(response, "Naabot mo na ang 2 na sariling tile.")
        self.assertNotContains(response, 'name="word_form"')

        response = self.add(word="bola", board="Bagay")
        self.assertEqual(messages_of(response), ["Naabot mo na ang 2 na sariling tile. Magbura muna ng isa para makapagdagdag."])
        self.assertEqual(GuardianWord.objects.filter(guardian=self.nanay).count(), 2)

        # Raising the limit opens it again.
        self.set_limit(3)
        self.assertRedirects(self.add(word="bola", board="Bagay"), self.url)
        self.assertEqual(GuardianWord.objects.filter(guardian=self.nanay).count(), 3)

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
        self.assertContains(response, "Nakatago muna sa mga board ang 1 tile mo")
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


@override_settings(ELEVENLABS_API_KEY="susi", ELEVENLABS_VOICE_ID="pinoy-boses")
class GuardianWordAudioTest(SharedTileAudioTestMixin, GuardianWordsBase):
    """A new tile is voiced in the shared voice and in each of the guardian's family voices."""

    def setUp(self):
        super().setUp()
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

    def test_adding_a_tile_voices_it_in_the_shared_voice_and_every_family_voice(self):
        lola, lolo = self.make_family_voice("Lola"), self.make_family_voice("Lolo")
        self.login_as("nanay")
        response = self.add()

        self.assertEqual(messages_of(response), ["Naidagdag na ang “Kuya Jun” sa board na “Tao”."])
        self.assertEqual(
            sorted(call.args for call in self.elevenlabs.text_to_speech.call_args_list),
            [("boses-Lola", "Kuya Jun"), ("boses-Lolo", "Kuya Jun"), ("pinoy-boses", "Kuya Jun")],
        )
        self.assertEqual((self.audio_directory / "kuya-jun.mp3").read_bytes(), b"pinoy-boses: Kuya Jun")
        self.assertEqual(self.family_audio(lola, "Kuya Jun").read_bytes(), b"boses-Lola: Kuya Jun")
        self.assertEqual(self.family_audio(lolo, "Kuya Jun").read_bytes(), b"boses-Lolo: Kuya Jun")

        # The page plays it, and the boards use it: Miguel hears it in his family voice.
        self.assertContains(self.client.get(self.url), "▶ Pakinggan")
        tile_audio = self.client.get(reverse("board")).context["board_data"]["tile_audio"]
        self.assertIn("kuya-jun.mp3", tile_audio["Kuya Jun"])
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
        self.assertTrue((self.audio_directory / "kuya-jun.mp3").exists())

    def test_audio_already_made_is_not_made_again(self):
        (self.audio_directory / "kuya-jun.mp3").write_bytes(b"dati na")
        self.login_as("nanay")
        self.add()
        self.elevenlabs.text_to_speech.assert_not_called()
        self.assertEqual((self.audio_directory / "kuya-jun.mp3").read_bytes(), b"dati na")

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

    def test_deleting_the_tile_deletes_its_audio_unless_another_family_has_the_word(self):
        voice = self.make_family_voice("Lola")
        self.login_as("nanay")
        self.add()
        word = GuardianWord.objects.get()
        shared = self.audio_directory / "kuya-jun.mp3"

        tito = make_guardian("tito", "Tito Ben")
        self.make_word(tito, "Kuya Jun")
        self.client.post(reverse("remove_guardian_word", args=[word.uuid]))
        self.assertFalse(self.family_audio(voice, "Kuya Jun").exists())
        self.assertTrue(shared.exists())  # Tito's tile still says it

        delete_user_account(tito.user)
        self.assertFalse(shared.exists())

    def test_a_tile_on_free_is_not_voiced_again(self):
        word = self.make_word(self.tatay, "Lolo Ben")
        self.login_as("tatay")
        response = self.client.post(reverse("voice_guardian_word", args=[word.uuid]))
        self.assertEqual(messages_of(response), ["Para sa SalitAACo Plus lang ang sariling tile."])
        self.elevenlabs.text_to_speech.assert_not_called()


class PlusSettingsTest(GuardianWordsBase):
    def test_an_admin_sets_the_limit(self):
        url = reverse("system_general")
        self.login_as("developer")
        self.assertContains(self.client.get(url), f'name="guardian_word_limit" value="{DEFAULT_GUARDIAN_WORD_LIMIT}"')

        response = self.client.post(url, {"plus_form": "", "guardian_word_limit": "5"})
        self.assertRedirects(response, url)
        self.assertEqual(messages_of(response), ["Naka-save na ang mga setting ng Plus."])
        self.assertEqual(SiteSetting.load().guardian_word_limit, 5)

        response = self.client.post(url, {"plus_form": "", "guardian_word_limit": "-1"})
        self.assertContains(response, "Hindi tama ang bilang.")
        self.assertEqual(SiteSetting.load().guardian_word_limit, 5)

    def test_only_admins_set_it(self):
        self.login_as("nanay")
        self.client.post(reverse("system_general"), {"plus_form": "", "guardian_word_limit": "500"})
        self.assertEqual(SiteSetting.load().guardian_word_limit, DEFAULT_GUARDIAN_WORD_LIMIT)
