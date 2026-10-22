from django.contrib.messages import get_messages
from django.core.files.storage import default_storage
from django.urls import reverse

from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.forms.vocabulary.word import WordForm
from salitaaco.models.added_word import AddedWord
from salitaaco.models.child_account import ChildAccount
from salitaaco.tests.users_base import UserBase, image_upload, make_guardian
from salitaaco.utils.board import all_boards
from salitaaco.utils.tile_audio import tile_words

DEFAULT_WORD_COUNT = 105


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class WordsBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.url = reverse("words")

    def add(self, word="pandesal", board="Pagkain", emoji="🥖"):
        return self.client.post(self.url, {"board": board, "word": word, "emoji": emoji})

    def words_on(self, board, url=None):
        board_data = self.client.get(url or reverse("board")).context["board_data"]
        return [item["w"] for category in board_data["categories"] if category["name"] == board for item in category["items"]]


class WordFormTest(WordsBase):
    def form(self, **changes):
        return WordForm({"board": "Pagkain", "word": "pandesal", "emoji": "🥖", **changes})

    def test_valid_and_tidied(self):
        form = self.form(word="  mainit   na  tsokolate ")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["word"], "mainit na tsokolate")

    def test_everything_is_required_and_the_board_has_to_exist(self):
        form = WordForm({})
        self.assertEqual(
            (form.errors["board"], form.errors["word"], form.errors["emoji"]),
            (["Pumili ng board."], ["Ilagay ang salita."], ["Ilagay ang simbolo."]),
        )
        self.assertEqual(self.form(board="Wala Nito").errors["board"], ["Walang ganitong board."])

    def test_no_two_tiles_say_the_same_thing(self):
        # A default word, a verb form, and the same word in other letter case are all taken.
        for taken in ["isda", "kumain", "ISDA", "Tawagan si nanay"]:
            self.assertEqual(self.form(word=taken).errors["word"], ["May tile na para sa salitang ito."], taken)

        AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        self.assertEqual(self.form().errors["word"], ["May tile na para sa salitang ito."])
        # Two words whose audio files would have the same name are the same tile too.
        self.assertEqual(self.form(word="pandesal!").errors["word"], ["May tile na para sa salitang ito."])

    def test_a_word_needs_letters_and_a_symbol_needs_none(self):
        self.assertEqual(self.form(word="!!!").errors["word"], ["Kailangang may titik o numero ang salita."])
        self.assertEqual(self.form(emoji="tinapay").errors["emoji"], ["Emoji ang ilagay, hindi titik o numero."])
        self.assertEqual(self.form(word="a" * 41).errors["word"], ["Masyadong mahaba ang salita (hanggang 40 character)."])

    def test_a_word_being_edited_is_not_a_copy_of_itself(self):
        added = AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        form = WordForm({"board": "Bagay", "word": "pandesal", "emoji": "🍞"}, editing=added)
        self.assertTrue(form.is_valid(), form.errors)
        # But it still cannot take another tile's word.
        self.assertFalse(WordForm({"board": "Bagay", "word": "isda", "emoji": "🍞"}, editing=added).is_valid())


class WordsPageTest(WordsBase):
    def test_only_admins_open_the_page_and_add_words(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.add().status_code, 302)
        self.assertFalse(AddedWord.objects.exists())

    def test_page_lists_every_default_word_with_an_action_column(self):
        self.login_as("developer")
        response = self.client.get(self.url)

        self.assertEqual(response.context["word_count"], 75)  # 60 plain words and 15 verbs, each verb one row
        self.assertEqual(len(response.context["words"]), 20)
        self.assertEqual(response.context["added_count"], 0)
        self.assertContains(response, "<th>Aksyon</th>")
        self.assertContains(response, "Bahagi ng default")
        self.assertContains(response, 'data-modal="add-word" data-open="false"')

        verbs = self.client.get(self.url, {"board": "Pandiwa"}).context["words"]
        self.assertEqual(verbs[0]["word"], "kumain · kumakain · kakain")

    def test_search_and_board_filter(self):
        AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        self.login_as("developer")

        def found(**query):
            return [row["word"] for row in self.client.get(self.url, query).context["words"]]

        self.assertEqual(found(board="Pagkain"), ["bigas", "isda", "gulay", "prutas", "pandesal"])
        self.assertEqual(found(query="PANDE"), ["pandesal"])
        self.assertEqual(found(query="sal", board="Pagkain"), ["pandesal"])
        self.assertEqual(found(query="walang ganito"), [])
        # A board that does not exist is no filter at all.
        self.assertEqual(self.client.get(self.url, {"board": "Wala Nito"}).context["word_count"], 76)

    def test_adding_a_word(self):
        self.login_as("developer")
        response = self.add()

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naidagdag na ang “pandesal” sa board na “Pagkain”."])
        added = AddedWord.objects.get()
        self.assertEqual((added.board, added.word, added.emoji), ("Pagkain", "pandesal", "🥖"))

        response = self.client.get(self.url, {"query": "pandesal"})
        self.assertContains(response, '<span class="statusBadge pending">Idinagdag</span>')
        self.assertContains(response, f'href="{reverse("edit_word", args=[added.uuid])}"')

    def test_a_word_that_is_not_valid_reopens_the_form_and_saves_nothing(self):
        self.login_as("developer")
        response = self.add(word="isda")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "May tile na para sa salitang ito.")
        self.assertContains(response, 'data-modal="add-word" data-open="true"')
        self.assertFalse(AddedWord.objects.exists())

    def test_editing_and_deleting_an_added_word(self):
        added = AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        edit_url = reverse("edit_word", args=[added.uuid])
        delete_url = reverse("delete_word", args=[added.uuid])

        self.login_as("nanay")
        self.assertEqual(self.client.get(edit_url).status_code, 302)
        self.assertEqual(self.client.post(delete_url).status_code, 302)

        self.login_as("developer")
        self.assertContains(self.client.get(edit_url), 'value="pandesal"')
        response = self.client.post(edit_url, {"board": "Bagay", "word": "pandesal", "emoji": "🍞"})
        self.assertRedirects(response, self.url)
        added.refresh_from_db()
        self.assertEqual((added.board, added.emoji), ("Bagay", "🍞"))

        response = self.client.post(edit_url, {"board": "Bagay", "word": "isda", "emoji": "🍞"})
        self.assertContains(response, "May tile na para sa salitang ito.")

        self.assertEqual(self.client.get(delete_url).status_code, 405)
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response)[-1], "Nabura na ang “pandesal”. Wala na ito sa mga board.")
        self.assertFalse(AddedWord.objects.exists())
        self.assertEqual(self.client.get(edit_url).status_code, 404)


class AddedWordEverywhereTest(WordsBase):
    """A word an admin added is a tile like any other, and the default vocabulary is left alone."""

    def setUp(self):
        self.vocabulary_before = [[dict(item) for item in category["items"]] for category in CATEGORIES]
        AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        AddedWord.objects.create(board="Pagkain", word="adobo", emoji="🍲")

    def test_it_is_at_the_end_of_its_board_for_everyone(self):
        expected = ["bigas", "isda", "gulay", "prutas", "pandesal", "adobo"]
        for username in ["miguel", "nanay", "developer"]:
            self.login_as(username)
            self.assertEqual(self.words_on("Pagkain"), expected, username)
        self.login_as("nanay")
        self.assertEqual(self.words_on("Pagkain", reverse("child_board", args=[self.miguel_account.uuid])), expected)

    def test_the_default_vocabulary_is_not_touched(self):
        all_boards()
        self.assertEqual([[dict(item) for item in category["items"]] for category in CATEGORIES], self.vocabulary_before)
        self.assertEqual(len(next(c for c in CATEGORIES if c["name"] == "Pagkain")["items"]), 4)

    def test_it_is_a_word_to_voice_and_to_count(self):
        words = tile_words()
        self.assertEqual(len(words), DEFAULT_WORD_COUNT + 2)
        self.assertEqual(words[-2:], ["pandesal", "adobo"])

        self.login_as("miguel")
        self.assertEqual(self.client.post(reverse("increment_word_usage"), {"word": "pandesal"}).json(), {"ok": True})
        self.assertEqual(self.client.get(reverse("board")).context["board_data"]["frequent_words"], [{"word": "pandesal", "use_count": 1}])


class WordPictureTest(WordsBase):
    """A word's symbol may be an uploaded picture in place of an emoji."""

    def add_with_picture(self, word="kakanin", picture=None):
        return self.client.post(self.url, {
            "board": "Pagkain", "word": word, "icon_kind": "image", "emoji": "",
            "icon_image": picture or image_upload(),
        })

    def tile(self, word, url=None):
        board_data = self.client.get(url or reverse("board")).context["board_data"]
        return next(item for category in board_data["categories"] for item in category["items"] if item["w"] == word)

    def test_the_form_takes_an_emoji_or_a_jpg_png_or_webp_picture(self):
        form = WordForm({"board": "Pagkain", "word": "kakanin", "icon_kind": "image"})
        self.assertEqual(form.errors["icon_image"], ["Pumili ng larawan ng salita."])
        self.assertNotIn("emoji", form.errors)
        for picture, error in [
            (image_upload("kakanin.gif", "GIF", "image/gif"), "JPEG, PNG o WebP lang ang puwedeng larawan."),
            (image_upload(padding=5 * 1024 * 1024), "Masyadong malaki ang larawan (max 5MB)."),
        ]:
            form = WordForm({"board": "Pagkain", "word": "kakanin", "icon_kind": "image"}, {"icon_image": picture})
            self.assertEqual(form.errors["icon_image"], [error])
        form = WordForm({"board": "Pagkain", "word": "kakanin", "icon_kind": "image"}, {"icon_image": image_upload()})
        self.assertTrue(form.is_valid(), form.errors)
        # The board and the word stay required whichever the symbol is.
        form = WordForm({"icon_kind": "image"}, {"icon_image": image_upload()})
        self.assertEqual((form.errors["board"], form.errors["word"]), (["Pumili ng board."], ["Ilagay ang salita."]))

    def test_the_add_window_offers_the_choice(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="icon_kind" value="image"')
        self.assertContains(response, "📷 Pumili ng larawan")
        self.assertContains(response, "JPG, PNG o WEBP, hanggang 5 MB.")
        self.assertContains(response, "js/picture_choice.js")

    def test_a_word_with_a_picture_is_on_everyones_boards(self):
        self.login_as("developer")
        self.assertRedirects(self.add_with_picture(), self.url)
        added = AddedWord.objects.get()
        self.assertTrue(added.icon_image.name.startswith("word-images/"))
        self.assertTrue(added.icon_image.name.endswith(".webp"))
        self.assertEqual((added.emoji, added.icon_mime), ("", "image/webp"))

        image_url = reverse("added_word_image", args=[added.uuid])
        self.assertContains(self.client.get(self.url, {"query": "kakanin"}), f'<img class="symbolImage" src="{image_url}?v=')
        for username in ["miguel", "nanay", "developer"]:
            self.login_as(username)
            self.assertTrue(self.tile("kakanin")["img"].startswith(image_url), username)
            self.assertEqual(self.client.get(image_url).status_code, 200, username)
        self.login_as("nanay")
        self.assertTrue(self.tile("kakanin", reverse("child_board", args=[self.miguel_account.uuid]))["img"].startswith(image_url))
        # A tile with an emoji has no picture to load.
        AddedWord.objects.create(board="Pagkain", word="pandesal", emoji="🥖")
        self.assertNotIn("img", self.tile("pandesal"))

        self.client.logout()
        self.assertEqual(self.client.get(image_url).status_code, 302)

    def test_editing_keeps_replaces_or_drops_the_picture(self):
        self.login_as("developer")
        self.add_with_picture()
        added = AddedWord.objects.get()
        edit_url = reverse("edit_word", args=[added.uuid])
        first = added.icon_image.name

        response = self.client.get(edit_url)
        self.assertContains(response, 'value="image" class="iconKind" id="id_icon_kind_1" checked')
        self.assertContains(response, "Ang kasalukuyang larawan")

        # Saved without a new picture, it keeps its own.
        self.client.post(edit_url, {"board": "Bagay", "word": "kakanin", "icon_kind": "image", "emoji": ""})
        added.refresh_from_db()
        self.assertEqual((added.board, added.icon_image.name), ("Bagay", first))

        # A new picture takes the old one's place.
        self.client.post(edit_url, {"board": "Bagay", "word": "kakanin", "icon_kind": "image", "icon_image": image_upload()})
        added.refresh_from_db()
        self.assertNotEqual(added.icon_image.name, first)
        self.assertFalse(default_storage.exists(first))

        # An emoji in its place removes the picture.
        second = added.icon_image.name
        self.client.post(edit_url, {"board": "Bagay", "word": "kakanin", "icon_kind": "emoji", "emoji": "🍡"})
        added.refresh_from_db()
        self.assertEqual((added.emoji, added.has_icon_image), ("🍡", False))
        self.assertFalse(default_storage.exists(second))

        # An emoji word becomes a picture one only with a picture.
        response = self.client.post(edit_url, {"board": "Bagay", "word": "kakanin", "icon_kind": "image", "emoji": "🍡"})
        self.assertContains(response, "Pumili ng larawan ng salita.")

    def test_deleting_a_word_deletes_its_picture(self):
        self.login_as("developer")
        self.add_with_picture()
        added = AddedWord.objects.get()
        name = added.icon_image.name
        self.assertTrue(default_storage.exists(name))
        self.client.post(reverse("delete_word", args=[added.uuid]))
        self.assertFalse(default_storage.exists(name))
        self.assertEqual(self.client.get(reverse("added_word_image", args=[added.uuid])).status_code, 404)
