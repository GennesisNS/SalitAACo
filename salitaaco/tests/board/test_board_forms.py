from django.test import SimpleTestCase

from salitaaco.forms.board.tile_word import TileWordForm
from salitaaco.forms.board.upload_tile_sound import UploadTileSoundForm
from salitaaco.tests.users_base import sound_upload
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE


class UploadTileSoundFormTest(SimpleTestCase):
    def test_valid(self):
        form = UploadTileSoundForm({"word": "mama"}, {"sound": sound_upload()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_codec_suffix_is_accepted(self):
        form = UploadTileSoundForm({"word": "mama"}, {"sound": sound_upload(content_type="audio/webm;codecs=opus")})
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_sound(self):
        form = UploadTileSoundForm({"word": "mama"}, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["sound"], ["Walang natanggap na tunog."])

    def test_file_that_is_not_audio(self):
        form = UploadTileSoundForm({"word": "mama"}, {"sound": sound_upload(content_type="text/html")})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["sound"], ["Hindi suportadong file type ng tunog."])

    def test_sound_over_five_megabytes(self):
        form = UploadTileSoundForm({"word": "mama"}, {"sound": sound_upload(size=MAX_UPLOAD_SIZE)})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["sound"], ["Masyadong malaki ang tunog (max 5MB)."])


class TileWordFormTest(SimpleTestCase):
    def test_valid(self):
        form = TileWordForm({"word": " gusto ko "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["word"], "gusto ko")

    def test_word_is_required(self):
        form = TileWordForm({"word": "   "})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["word"], ["Walang word."])
