from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.favorites.add_favorite_word import AddFavoriteWordForm, word_choices
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.favorite_word import FavoriteWord
from salitaaco.routes.favorites.favorites import favorite_words_for_board
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.board import board_data_sources
from salitaaco.utils.tile_audio import tile_words


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class FavoritesBase(UserBase):
    """Nanay is the guardian of Miguel and Ana. Tatay is a guardian of nobody."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel, cls.ana])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.ana_account = ChildAccount.objects.get(user=cls.ana)
        cls.url = reverse("favorites", args=[cls.miguel_account.uuid])

    def words(self, child=None):
        return [favorite.word for favorite in (child or self.miguel_account).favorite_words.order_by("favorite_word_id")]


class AddFavoriteWordFormTest(FavoritesBase):
    def test_the_choices_are_every_tile_word_grouped_by_board(self):
        groups = word_choices()
        self.assertEqual([name for name, words in groups], ["Tao", "Bagay", "Pagkain", "Lugar", "Pandiwa", "Pakiramdam"])
        offered = [word for name, words in groups for word, label in words]
        self.assertEqual(sorted(set(offered)), sorted(tile_words()))
        # A verb is offered as the board shows it: in each of its three aspects, never the root.
        verbs = [word for word, label in dict(groups)["Pandiwa"]]
        self.assertEqual(verbs[:3], ["kumain", "kumakain", "kakain"])
        self.assertNotIn("kain", verbs)

    def test_a_word_is_required_and_has_to_be_a_tile_word(self):
        form = AddFavoriteWordForm({"word": ""}, child=self.miguel_account)
        self.assertEqual(form.errors["word"], ["Pumili ng salita."])
        form = AddFavoriteWordForm({"word": "hindi-tile"}, child=self.miguel_account)
        self.assertEqual(form.errors["word"], ["Pumili ng salita mula sa listahan."])

    def test_a_word_cannot_be_a_favorite_twice_for_the_same_child(self):
        FavoriteWord.objects.create(child=self.miguel_account, word="mama")
        form = AddFavoriteWordForm({"word": "mama"}, child=self.miguel_account)
        self.assertEqual(form.errors["word"], ["Paborito na ang salitang ito."])
        self.assertTrue(AddFavoriteWordForm({"word": "mama"}, child=self.ana_account).is_valid())


class FavoritesPageTest(FavoritesBase):
    def test_only_the_childs_guardian_opens_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("tatay")
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {"word": "mama"}).status_code, 404)
        self.assertFalse(FavoriteWord.objects.exists())

    def test_page_starts_empty(self):
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wala pang paboritong salita.")
        self.assertContains(response, "Napiling bata")

    def test_adding_words_keeps_them_in_the_order_added(self):
        self.login_as("nanay")
        response = self.client.post(self.url, {"word": "tubig"})
        self.assertEqual(response.status_code, 200)  # "tubig" is not a tile word
        self.assertContains(response, "Pumili ng salita mula sa listahan.")

        for word in ["tulong", "mama", "kumain"]:
            response = self.client.post(self.url, {"word": word})
            self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Paborito na ni Miguel ang “kumain”."])
        self.assertEqual(self.words(), ["tulong", "mama", "kumain"])
        self.assertEqual(self.words(self.ana_account), [])

        response = self.client.post(self.url, {"word": "mama"})
        self.assertContains(response, "Paborito na ang salitang ito.")
        self.assertEqual(self.words(), ["tulong", "mama", "kumain"])

    def test_removing_a_word(self):
        favorite = FavoriteWord.objects.create(child=self.miguel_account, word="mama")
        FavoriteWord.objects.create(child=self.miguel_account, word="tulong")
        remove_url = reverse("remove_favorite", args=[self.miguel_account.uuid, favorite.uuid])

        self.login_as("tatay")
        self.assertEqual(self.client.post(remove_url).status_code, 404)

        self.login_as("nanay")
        self.assertEqual(self.client.get(remove_url).status_code, 405)
        # A favorite is removed through its own child's address only.
        wrong_child = reverse("remove_favorite", args=[self.ana_account.uuid, favorite.uuid])
        self.assertEqual(self.client.post(wrong_child).status_code, 404)
        self.assertEqual(self.words(), ["mama", "tulong"])

        response = self.client.post(remove_url)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Inalis na ang “mama” sa mga paborito ni Miguel."])
        self.assertEqual(self.words(), ["tulong"])

    def test_deleting_the_child_deletes_their_favorites(self):
        FavoriteWord.objects.create(child=self.miguel_account, word="mama")
        self.miguel.delete()
        self.assertFalse(FavoriteWord.objects.exists())


class FavoritesOnTheBoardTest(FavoritesBase):
    """The board hears of the words only through the function this feature registers."""

    def setUp(self):
        for word in ["tulong", "mama"]:
            FavoriteWord.objects.create(child=self.miguel_account, word=word)

    def test_the_feature_registers_itself_with_the_board(self):
        self.assertIn(favorite_words_for_board, board_data_sources)
        self.assertEqual(favorite_words_for_board(self.miguel_account), {"favorite_words": ["tulong", "mama"]})
        self.assertEqual(favorite_words_for_board(None), {})

    def test_the_childs_board_and_the_guardians_view_of_it_carry_the_words(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("board")).context["board_data"]["favorite_words"], ["tulong", "mama"])

        self.login_as("ana")
        self.assertEqual(self.client.get(reverse("board")).context["board_data"]["favorite_words"], [])

        self.login_as("nanay")
        child_board = reverse("child_board", args=[self.miguel_account.uuid])
        self.assertEqual(self.client.get(child_board).context["board_data"]["favorite_words"], ["tulong", "mama"])
        # A guardian's own board is not a child's: it has no favorites to carry.
        self.assertNotIn("favorite_words", self.client.get(reverse("board")).context["board_data"])
