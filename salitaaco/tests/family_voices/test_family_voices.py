from unittest import mock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.defaults.family_voice import PREVIEW_WORD, TERMS_VERSION, WORDS_PER_REQUEST
from salitaaco.forms.family_voices.add_family_voice import AddFamilyVoiceForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.tests.users_base import UserBase, make_guardian, sound_upload
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.family_voice import family_voice_directory, family_voice_progress
from salitaaco.utils.tile_audio import tile_audio_file_name, tile_word_slug, tile_words

ELEVENLABS = "salitaaco.utils.family_voice.ElevenLabs"


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


@override_settings(ELEVENLABS_API_KEY="susi")
class FamilyVoiceBase(UserBase):
    """Nanay is the guardian of Miguel and Ana. Tatay is another guardian, of nobody."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel, cls.ana])
        cls.tatay = make_guardian("tatay", "Tatay Ben")

    def setUp(self):
        patcher = mock.patch(ELEVENLABS)
        self.client_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.elevenlabs = self.client_class.return_value
        self.elevenlabs.add_voice.return_value = "elevenlabs-boses"
        self.elevenlabs.text_to_speech.side_effect = lambda voice_id, word: f"{voice_id}: {word}".encode()

    def make_voice(self, guardian=None, name="Lola"):
        return FamilyVoice.objects.create(
            guardian=guardian or self.nanay, name=name, elevenlabs_voice_id=f"boses-{name}",
            consent_at=timezone.now(), consent_version=TERMS_VERSION,
        )

    def write_words(self, voice, *words):
        directory = family_voice_directory(voice)
        directory.mkdir(parents=True, exist_ok=True)
        for word in words:
            (directory / f"{word.replace(' ', '-').lower()}.mp3").write_bytes(word.encode())


class AddFamilyVoiceFormTest(FamilyVoiceBase):
    def test_valid(self):
        form = AddFamilyVoiceForm({"name": "Nanay", "consent": "on"}, {"sample": sound_upload()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_consent_name_and_recording_are_required(self):
        form = AddFamilyVoiceForm({"name": "", "consent": ""}, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], ["Ilagay kung kaninong boses ito."])
        self.assertEqual(form.errors["sample"], ["Mag-record o mag-upload muna ng boses."])
        self.assertEqual(form.errors["consent"], ["Kailangang sumang-ayon sa Paalala at Kasunduan bago gawin ang boses."])

    def test_recording_must_be_audio_up_to_10_megabytes(self):
        for sample, error in [
            (sound_upload(content_type="text/html"), "Hindi suportadong file type ng tunog."),
            (sound_upload(size=11 * 1024 * 1024), "Masyadong malaki ang recording (max 10MB)."),
        ]:
            form = AddFamilyVoiceForm({"name": "Nanay", "consent": "on"}, {"sample": sample})
            self.assertFalse(form.is_valid())
            self.assertEqual(form.errors["sample"], [error])


class FamilyVoicesAccessTest(FamilyVoiceBase):
    def test_only_guardians_open_the_page(self):
        response = self.client.get(reverse("family_voices"))
        self.assertTrue(response.url.startswith("/login/"))
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertTrue(self.client.get(reverse("family_voices")).url.startswith("/login/"), username)

        self.login_as("nanay")
        response = self.client.get(reverse("family_voices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paalala at Kasunduan sa Boses ng Pamilya")
        self.assertContains(response, reverse("family_voices"))  # the sidebar item

    @override_settings(ELEVENLABS_API_KEY="")
    def test_without_elevenlabs_set_up_nothing_can_be_added(self):
        self.login_as("nanay")
        response = self.client.get(reverse("family_voices"))
        self.assertContains(response, "Hindi pa naka-set up ang paggawa ng boses")
        self.assertNotContains(response, "Magdagdag ng boses")

        self.client.post(reverse("family_voices"), {"name": "Nanay", "consent": "on", "sample": sound_upload()})
        self.assertFalse(FamilyVoice.objects.exists())


class AddFamilyVoiceTest(FamilyVoiceBase):
    def add(self, **changes):
        data = {"name": "Nanay", "consent": "on", "sample": sound_upload(), **changes}
        return self.client.post(reverse("family_voices"), data)

    def test_voice_is_cloned_saved_with_the_consent_and_given_to_the_children(self):
        ChildAccount.objects.filter(user=self.ana).update(family_voice=self.make_voice(name="Lola"))
        self.login_as("nanay")

        response = self.add()

        self.assertRedirects(response, reverse("family_voices"))
        self.assertEqual(messages_of(response), ["Nagawa na ang boses ni Nanay. Ginagawa na ang mga salita nito."])

        add_voice = self.elevenlabs.add_voice.call_args.kwargs
        self.assertIn("Nanay", add_voice["name"])
        self.assertEqual((add_voice["sample_mime"], add_voice["sample"][:4]), ("audio/webm", b"\x1a\x45\xdf\xa3"))

        voice = FamilyVoice.objects.get(name="Nanay")
        self.assertEqual((voice.guardian, voice.elevenlabs_voice_id, voice.consent_version), (self.nanay, "elevenlabs-boses", TERMS_VERSION))
        self.assertIsNotNone(voice.consent_at)
        # A child with no family voice gets the new one; a child who has one keeps it.
        self.assertEqual(ChildAccount.objects.get(user=self.miguel).family_voice, voice)
        self.assertEqual(ChildAccount.objects.get(user=self.ana).family_voice.name, "Lola")

    def test_without_consent_nothing_is_sent_or_saved(self):
        self.login_as("nanay")
        response = self.add(consent="")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_add_family_voice_modal"])
        self.assertContains(response, "Kailangang sumang-ayon sa Paalala at Kasunduan")
        self.elevenlabs.add_voice.assert_not_called()
        self.assertFalse(FamilyVoice.objects.exists())

    def test_elevenlabs_refusal_shows_an_error_and_saves_nothing(self):
        self.elevenlabs.add_voice.side_effect = ElevenLabsError("ElevenLabs answered 402: quota", 402)
        self.login_as("nanay")

        response = self.add()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hindi nagawa ang boses ngayon.")
        self.assertFalse(FamilyVoice.objects.exists())

    def test_the_recording_is_not_kept(self):
        self.login_as("nanay")
        self.add()
        voice = FamilyVoice.objects.get()
        self.assertFalse(family_voice_directory(voice).exists())
        self.assertFalse(any(field.name == "sample" for field in FamilyVoice._meta.get_fields()))


class GenerateWordsTest(FamilyVoiceBase):
    def test_each_request_makes_the_next_few_words_until_all_are_done(self):
        voice = self.make_voice()
        self.login_as("nanay")
        url = reverse("generate_family_voice", args=[voice.uuid])
        total = len(tile_words())

        first = self.client.post(url).json()
        self.assertEqual(first, {"ok": True, "done": WORDS_PER_REQUEST, "total": total, "finished": False})
        self.assertEqual((family_voice_directory(voice) / "ako.mp3").read_bytes(), b"boses-Lola: ako")

        result = first
        while not result["finished"]:
            result = self.client.post(url).json()
        self.assertEqual(result["done"], total)
        self.assertEqual(self.elevenlabs.text_to_speech.call_count, total)

        # Nothing left to make: no more calls.
        self.client.post(url)
        self.assertEqual(self.elevenlabs.text_to_speech.call_count, total)

    def test_elevenlabs_refusal_keeps_the_words_made(self):
        voice = self.make_voice()
        calls = []

        def text_to_speech(voice_id, word):
            calls.append(word)
            if len(calls) > 2:
                raise ElevenLabsError("ElevenLabs answered 429: slow down", 429)
            return b"ok"

        self.elevenlabs.text_to_speech.side_effect = text_to_speech
        self.login_as("nanay")

        response = self.client.post(reverse("generate_family_voice", args=[voice.uuid]))

        self.assertEqual(response.status_code, 502)
        self.assertEqual((response.json()["ok"], response.json()["done"]), (False, 2))
        self.assertEqual(family_voice_progress(voice)[0], 2)

    def test_only_the_voices_guardian_can_generate_and_only_by_post(self):
        voice = self.make_voice()
        url = reverse("generate_family_voice", args=[voice.uuid])
        self.login_as("tatay")
        self.assertEqual(self.client.post(url).status_code, 404)
        self.login_as("nanay")
        self.assertEqual(self.client.get(url).status_code, 405)


class PlayFamilyVoiceWordTest(FamilyVoiceBase):
    def test_the_guardian_and_their_children_hear_it_and_nobody_else(self):
        voice = self.make_voice()
        self.write_words(voice, "salamat")
        url = reverse("play_family_voice_word", args=[voice.uuid, "salamat"])

        for username in ["nanay", "miguel", "ana"]:
            self.login_as(username)
            response = self.client.get(url)
            self.assertEqual((response.status_code, response["Content-Type"]), (200, "audio/mpeg"), username)
            self.assertEqual(b"".join(response.streaming_content), b"salamat")

        for username in ["tatay", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 404, username)

    def test_word_not_generated_yet_is_not_found(self):
        voice = self.make_voice()
        self.login_as("nanay")
        self.assertEqual(self.client.get(reverse("play_family_voice_word", args=[voice.uuid, "opo"])).status_code, 404)


class RemoveFamilyVoiceTest(FamilyVoiceBase):
    def test_deleting_removes_it_at_elevenlabs_and_here(self):
        voice = self.make_voice()
        self.write_words(voice, "opo")
        ChildAccount.objects.filter(user=self.miguel).update(family_voice=voice)
        self.login_as("nanay")

        response = self.client.post(reverse("remove_family_voice", args=[voice.uuid]))

        self.assertRedirects(response, reverse("family_voices"))
        self.assertEqual(messages_of(response), ["Permanente nang nabura ang boses ni Lola."])
        self.elevenlabs.delete_voice.assert_called_once_with("boses-Lola")
        self.assertFalse(FamilyVoice.objects.exists())
        self.assertFalse(family_voice_directory(voice).exists())
        # The child goes back to the app's shared voice.
        self.assertIsNone(ChildAccount.objects.get(user=self.miguel).family_voice)

    def test_a_voice_elevenlabs_no_longer_has_counts_as_deleted(self):
        voice = self.make_voice()
        self.elevenlabs.delete_voice.side_effect = ElevenLabsError("not found", 404)
        self.login_as("nanay")
        self.client.post(reverse("remove_family_voice", args=[voice.uuid]))
        self.assertFalse(FamilyVoice.objects.exists())

    def test_elevenlabs_refusal_keeps_the_voice_so_it_can_be_retried(self):
        voice = self.make_voice()
        self.elevenlabs.delete_voice.side_effect = ElevenLabsError("ElevenLabs answered 500: oops", 500)
        self.login_as("nanay")

        response = self.client.post(reverse("remove_family_voice", args=[voice.uuid]))

        self.assertEqual(messages_of(response), ["Hindi nabura ang boses ni Lola ngayon. Pakisubukan muli mamaya."])
        self.assertTrue(FamilyVoice.objects.filter(pk=voice.pk).exists())

    def test_only_the_voices_guardian_can_delete_it(self):
        voice = self.make_voice()
        self.login_as("tatay")
        self.assertEqual(self.client.post(reverse("remove_family_voice", args=[voice.uuid])).status_code, 404)
        self.assertTrue(FamilyVoice.objects.exists())

    def test_deleting_the_guardians_account_deletes_their_voices_even_if_elevenlabs_refuses(self):
        voice = self.make_voice(guardian=self.tatay)
        self.write_words(voice, "opo")
        self.elevenlabs.delete_voice.side_effect = ElevenLabsError("ElevenLabs answered 500: oops", 500)

        delete_user_account(User.objects.get(username="tatay"))

        self.elevenlabs.delete_voice.assert_called_once_with("boses-Lola")
        self.assertFalse(FamilyVoice.objects.exists())
        self.assertFalse(family_voice_directory(voice).exists())


class ChooseChildsVoiceTest(FamilyVoiceBase):
    def test_guardian_chooses_which_voice_a_child_hears(self):
        lola = self.make_voice(name="Lola")
        self.make_voice(guardian=self.tatay, name="Hindi kanya")
        self.login_as("nanay")
        child = ChildAccount.objects.get(user=self.miguel)
        url = reverse("manage_child", args=[child.uuid])

        choices = self.client.get(url).context["voice_form"].fields["family_voice"].choices
        self.assertEqual(choices, [("", "Karaniwang boses ng app"), (str(lola.uuid), "Lola")])

        response = self.client.post(url, {"voice_form": "", "family_voice": str(lola.uuid)})
        self.assertRedirects(response, url)
        self.assertEqual(ChildAccount.objects.get(pk=child.pk).family_voice, lola)

        self.client.post(url, {"voice_form": "", "family_voice": ""})
        self.assertIsNone(ChildAccount.objects.get(pk=child.pk).family_voice)

    def test_another_guardians_voice_cannot_be_chosen(self):
        other = self.make_voice(guardian=self.tatay, name="Hindi kanya")
        self.login_as("nanay")
        child = ChildAccount.objects.get(user=self.miguel)

        response = self.client.post(reverse("manage_child", args=[child.uuid]), {"voice_form": "", "family_voice": str(other.uuid)})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(ChildAccount.objects.get(pk=child.pk).family_voice)


class ChildChoosesVoiceInSettingsTest(FamilyVoiceBase):
    def choose(self, value):
        return self.client.post(reverse("settings"), {"voice_form": "", "family_voice": value})

    def test_child_sees_their_familys_voices_and_hears_each_first(self):
        lola = self.make_voice(name="Lola")
        nanay = self.make_voice(name="Nanay")
        # The preview word is generated the way the real command makes it, from the tile's word.
        (family_voice_directory(nanay)).mkdir(parents=True, exist_ok=True)
        (family_voice_directory(nanay) / tile_audio_file_name(PREVIEW_WORD)).write_bytes(b"ID3")  # Lola has not got it yet
        self.make_voice(guardian=self.tatay, name="Hindi kanya")
        self.login_as("miguel")

        response = self.client.get(reverse("settings"))

        self.assertContains(response, "Boses ng mga Tile")
        choices = [(radio.data["value"], radio.choice_label, preview) for radio, preview in response.context["voice_choices"]]
        self.assertEqual(choices, [
            ("", "Karaniwang boses ng app", None),
            (str(lola.uuid), "Lola", None),
            (str(nanay.uuid), "Nanay", reverse("play_family_voice_word", args=[nanay.uuid, tile_word_slug(PREVIEW_WORD)])),
        ])

    def test_the_preview_word_is_a_real_tile_word(self):
        # Otherwise it is never generated and every ▶ stays greyed out.
        self.assertIn(PREVIEW_WORD, tile_words())

    def test_child_picks_a_voice_and_can_go_back_to_the_apps(self):
        lola = self.make_voice(name="Lola")
        self.login_as("miguel")

        response = self.choose(str(lola.uuid))

        self.assertRedirects(response, reverse("settings"))
        self.assertEqual(messages_of(response), ["Naka-save na ang boses ng iyong mga tile."])
        self.assertEqual(ChildAccount.objects.get(user=self.miguel).family_voice, lola)
        # Only Miguel's choice changed.
        self.assertIsNone(ChildAccount.objects.get(user=self.ana).family_voice)
        # The guardian's page shows what the child picked.
        self.login_as("nanay")
        child_page = self.client.get(reverse("manage_child", args=[ChildAccount.objects.get(user=self.miguel).uuid]))
        self.assertEqual(child_page.context["voice_form"]["family_voice"].value(), str(lola.uuid))

        self.login_as("miguel")
        self.choose("")
        self.assertIsNone(ChildAccount.objects.get(user=self.miguel).family_voice)

    def test_child_cannot_pick_another_familys_voice(self):
        self.make_voice(name="Lola")
        other = self.make_voice(guardian=self.tatay, name="Hindi kanya")
        self.login_as("miguel")

        response = self.choose(str(other.uuid))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(ChildAccount.objects.get(user=self.miguel).family_voice)

    def test_no_choice_without_family_voices_or_for_other_accounts(self):
        # Miguel's guardian has no voices yet.
        self.login_as("miguel")
        self.assertIsNone(self.client.get(reverse("settings")).context["voice_form"])
        self.assertEqual(self.choose("").status_code, 200)

        # Guardians choose on the child's page, and admins have no family voices.
        self.make_voice(name="Lola")
        for username in ["nanay", "developer"]:
            self.login_as(username)
            self.assertIsNone(self.client.get(reverse("settings")).context["voice_form"], username)

    def test_child_without_a_guardian_has_no_choice(self):
        ChildAccount.objects.filter(user=self.ana).update(guardian=None)
        self.make_voice(name="Lola")
        self.login_as("ana")
        self.assertIsNone(self.client.get(reverse("settings")).context["voice_form"])


class BoardUsesTheFamilyVoiceTest(FamilyVoiceBase):
    def test_family_voice_words_take_the_place_of_the_shared_voice(self):
        voice = self.make_voice()
        self.write_words(voice, "opo")
        ChildAccount.objects.filter(user=self.miguel).update(family_voice=voice)
        shared = {"opo": "/static/audio/text-to-speech/opo.mp3?v=1", "ako": "/static/audio/text-to-speech/ako.mp3?v=1"}

        # A fresh dict per call, as the real tile_audio_urls() returns.
        with mock.patch("salitaaco.routes.board.board.tile_audio_urls", side_effect=lambda: dict(shared)):
            self.login_as("miguel")
            miguel_audio = self.client.get(reverse("board")).context["board_data"]["tile_audio"]
            self.login_as("ana")
            ana_audio = self.client.get(reverse("board")).context["board_data"]["tile_audio"]
            self.login_as("nanay")
            child_board = reverse("child_board", args=[ChildAccount.objects.get(user=self.miguel).uuid])
            guardian_view_of_miguel = self.client.get(child_board).context["board_data"]["tile_audio"]

        # "opo" is in Miguel's family voice; "ako" is not generated yet, so it stays in the shared voice.
        self.assertTrue(miguel_audio["opo"].startswith(reverse("play_family_voice_word", args=[voice.uuid, "opo"])))
        self.assertEqual(miguel_audio["ako"], shared["ako"])
        # Ana has no family voice; the guardian hears Miguel's board as Miguel does.
        self.assertEqual(ana_audio, shared)
        self.assertEqual(guardian_view_of_miguel, miguel_audio)
