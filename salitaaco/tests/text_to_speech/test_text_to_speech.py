import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabs, ElevenLabsError
from salitaaco.utils.tile_audio import tile_audio_file_name, tile_audio_urls, tile_words

REQUEST = "salitaaco.backends.text_to_speech.elevenlabs.requests.request"


def fake_response(status_code=200, content=b"ID3 fake mp3", json=None):
    response = requests.Response()
    response.status_code = status_code
    if json is not None:
        import json as json_module
        content = json_module.dumps(json).encode()
    response._content = content
    return response


class ElevenLabsClientTest(SimpleTestCase):
    def test_needs_an_api_key(self):
        with self.assertRaises(ValueError):
            ElevenLabs(api_key="")

    @mock.patch(REQUEST)
    def test_text_to_speech_sends_the_word_to_the_voice(self, request):
        request.return_value = fake_response(content=b"ID3 kumain")

        audio = ElevenLabs(api_key="susi", model_id="eleven_multilingual_v2").text_to_speech("boses-123", "kumain")

        self.assertEqual(audio, b"ID3 kumain")
        self.assertEqual(request.call_args.args, ("POST", "https://api.elevenlabs.io/v1/text-to-speech/boses-123"))
        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs["headers"], {"xi-api-key": "susi"})
        self.assertEqual(kwargs["params"], {"output_format": "mp3_44100_128"})
        self.assertEqual(kwargs["json"], {"text": "kumain", "model_id": "eleven_multilingual_v2"})

    @mock.patch(REQUEST)
    def test_add_voice_uploads_the_recording_and_returns_the_voice_id(self, request):
        request.return_value = fake_response(json={"voice_id": "bagong-boses", "requires_verification": False})

        voice_id = ElevenLabs(api_key="susi").add_voice("Nanay", "boses.webm", b"recording", "audio/webm", "isang paglalarawan")

        self.assertEqual(voice_id, "bagong-boses")
        self.assertEqual(request.call_args.args, ("POST", "https://api.elevenlabs.io/v1/voices/add"))
        self.assertEqual(request.call_args.kwargs["data"], {"name": "Nanay", "description": "isang paglalarawan"})
        self.assertEqual(request.call_args.kwargs["files"], [("files", ("boses.webm", b"recording", "audio/webm"))])

    @mock.patch(REQUEST)
    def test_delete_voice(self, request):
        request.return_value = fake_response(json={"status": "ok"})
        ElevenLabs(api_key="susi").delete_voice("lumang-boses")
        self.assertEqual(request.call_args.args, ("DELETE", "https://api.elevenlabs.io/v1/voices/lumang-boses"))

    @mock.patch(REQUEST)
    def test_refusal_and_network_failure_raise(self, request):
        request.return_value = fake_response(status_code=401, content=b"invalid api key")
        with self.assertRaisesRegex(ElevenLabsError, "401: invalid api key") as raised:
            ElevenLabs(api_key="mali").text_to_speech("boses-123", "opo")
        self.assertEqual(raised.exception.status_code, 401)

        request.side_effect = requests.ConnectionError("no internet")
        with self.assertRaisesRegex(ElevenLabsError, "Could not reach ElevenLabs"):
            ElevenLabs(api_key="susi").text_to_speech("boses-123", "opo")


class TileWordsTest(SimpleTestCase):
    def test_every_tile_label_including_all_verb_forms(self):
        words = tile_words()
        for word in ["ako", "tawagan si Nanay", "masakit dito", "kumain", "kumakain", "kakain", "malamig"]:
            self.assertIn(word, words)
        # A verb tile shows one of its forms, never the root.
        self.assertNotIn("kain", words)
        self.assertEqual(len(words), len(set(words)))

    def test_every_word_gets_its_own_file_name(self):
        names = [tile_audio_file_name(word) for word in tile_words()]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(tile_audio_file_name("tawagan si Nanay"), "tawagan-si-nanay.mp3")


class SharedTileAudioTestMixin:
    """Points the shared tile audio folder at a temporary one for the test."""

    def setUp(self):
        super().setUp()
        self.audio_directory = Path(tempfile.mkdtemp(prefix="salitaaco-test-audio-"))
        self.addCleanup(shutil.rmtree, self.audio_directory, ignore_errors=True)
        for module in ["salitaaco.utils.tile_audio", "salitaaco.management.commands.generate_tile_audio"]:
            patcher = mock.patch(f"{module}.tile_audio_directory", return_value=self.audio_directory)
            patcher.start()
            self.addCleanup(patcher.stop)


@override_settings(ELEVENLABS_API_KEY="susi", ELEVENLABS_MODEL="eleven_multilingual_v2", ELEVENLABS_VOICE_ID="pinoy-boses")
class GenerateTileAudioCommandTest(SharedTileAudioTestMixin, SimpleTestCase):
    def run_command(self, *args):
        output = StringIO()
        call_command("generate_tile_audio", *args, stdout=output)
        return output.getvalue()

    @mock.patch("salitaaco.management.commands.generate_tile_audio.ElevenLabs")
    def test_makes_one_file_per_tile_word_in_the_shared_voice(self, client_class):
        client_class.return_value.text_to_speech.side_effect = lambda voice, word: f"{voice}: {word}".encode()

        output = self.run_command()

        client_class.assert_called_once_with(api_key="susi", model_id="eleven_multilingual_v2")
        self.assertEqual(sorted(path.name for path in self.audio_directory.iterdir()),
                         sorted(tile_audio_file_name(word) for word in tile_words()))
        self.assertEqual((self.audio_directory / "tawagan-si-nanay.mp3").read_bytes(), b"pinoy-boses: tawagan si Nanay")
        self.assertIn(f"Done: {len(tile_words())} new, 0 already there.", output)

    @mock.patch("salitaaco.management.commands.generate_tile_audio.ElevenLabs")
    def test_only_the_words_asked_for_and_existing_files_are_kept(self, client_class):
        text_to_speech = client_class.return_value.text_to_speech
        text_to_speech.return_value = b"bago"
        (self.audio_directory / "opo.mp3").write_bytes(b"luma")

        output = self.run_command("--words", "opo", "gusto ko")

        self.assertEqual([call.args[1] for call in text_to_speech.call_args_list], ["gusto ko"])
        self.assertEqual((self.audio_directory / "opo.mp3").read_bytes(), b"luma")
        self.assertIn("Done: 1 new, 1 already there.", output)

        self.run_command("--words", "opo", "--overwrite")
        self.assertEqual((self.audio_directory / "opo.mp3").read_bytes(), b"bago")

    def test_unknown_words_are_refused(self):
        with self.assertRaisesRegex(CommandError, "Not tile words: kain, hello"):
            self.run_command("--words", "kain", "hello", "opo")

    @override_settings(ELEVENLABS_API_KEY="")
    def test_needs_the_api_key(self):
        with self.assertRaisesRegex(CommandError, "ELEVENLABS_API_KEY"):
            self.run_command()

    @override_settings(ELEVENLABS_VOICE_ID="")
    def test_needs_the_shared_voice(self):
        with self.assertRaisesRegex(CommandError, "ELEVENLABS_VOICE_ID"):
            self.run_command()

    @mock.patch("salitaaco.management.commands.generate_tile_audio.ElevenLabs")
    def test_a_failure_keeps_the_files_already_made(self, client_class):
        def text_to_speech(voice, word):
            if word == "ako":
                return b"ako"
            raise ElevenLabsError("ElevenLabs answered 429: too many requests", 429)

        client_class.return_value.text_to_speech.side_effect = text_to_speech

        with self.assertRaisesRegex(CommandError, "Stopped at 'ko' after 1 new files: .*429"):
            self.run_command("--words", "ako", "ko", "ikaw")
        self.assertEqual([path.name for path in self.audio_directory.iterdir()], ["ako.mp3"])

    def test_urls_are_given_for_generated_words_only(self):
        (self.audio_directory / "gusto-ko.mp3").write_bytes(b"ID3")
        urls = tile_audio_urls()
        self.assertEqual(list(urls), ["gusto ko"])
        self.assertRegex(urls["gusto ko"], r"^/static/audio/text-to-speech/gusto-ko\.mp3\?v=\d+$")
