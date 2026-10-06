from django.test import SimpleTestCase

from salitaaco.forms.board.tile_word import TileWordForm
from salitaaco.forms.board.upload_tile_image import UploadTileImageForm
from salitaaco.forms.board.upload_tile_sound import UploadTileSoundForm
from salitaaco.tests.users_base import image_upload, sound_upload
from salitaaco.utils.uploads import MAX_UPLOAD_SIZE


class UploadTileImageFormTest(SimpleTestCase):
    def test_valid(self):
        form = UploadTileImageForm({"word": "mama"}, {"image": image_upload()})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["image"].content_type, "image/png")

    def test_the_real_type_is_used_not_the_one_the_browser_claims(self):
        form = UploadTileImageForm({"word": "mama"}, {"image": image_upload(content_type="text/html")})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["image"].content_type, "image/png")

    def test_missing_image(self):
        form = UploadTileImageForm({"word": "mama"}, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["image"], ["Walang natanggap na larawan."])

    def test_missing_word(self):
        form = UploadTileImageForm({"word": ""}, {"image": image_upload()})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["word"], ["Walang natanggap na larawan."])

    def test_file_that_is_not_an_image(self):
        not_an_image = sound_upload(name="larawan.png", content_type="image/png")
        form = UploadTileImageForm({"word": "mama"}, {"image": not_an_image})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["image"], ["Hindi suportadong file type ng larawan."])

    def test_unsupported_image_type(self):
        bitmap = image_upload(name="larawan.bmp", image_format="BMP", content_type="image/bmp")
        form = UploadTileImageForm({"word": "mama"}, {"image": bitmap})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["image"], ["Hindi suportadong file type ng larawan."])

    def test_image_over_five_megabytes(self):
        form = UploadTileImageForm({"word": "mama"}, {"image": image_upload(padding=MAX_UPLOAD_SIZE)})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["image"], ["Masyadong malaki ang larawan (max 5MB)."])


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
