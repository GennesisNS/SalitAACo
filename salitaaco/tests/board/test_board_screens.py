from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse

from salitaaco.defaults.board import BOARD_ICONS, FEELINGS_BOARD, QUICK_WORDS
from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.board import boards, quick_words

BOARD_NAMES = [category["name"] for category in CATEGORIES]


class BoardDefaultsTest(SimpleTestCase):
    """defaults/board.py lays the vocabulary out; a name it misspells would quietly show nothing."""

    def test_quick_words_are_words_of_the_vocabulary(self):
        vocabulary = {item["w"] for category in CATEGORIES for item in category["items"]}
        for word in QUICK_WORDS:
            self.assertIn(word, vocabulary)
        self.assertEqual([tile["w"] for tile in quick_words()], QUICK_WORDS)

    def test_a_quick_word_the_vocabulary_lacks_is_left_out(self):
        with mock.patch("salitaaco.utils.board.QUICK_WORDS", ["oo", "wala-nito", "hindi"]):
            self.assertEqual([tile["w"] for tile in quick_words()], ["oo", "hindi"])

    def test_the_feelings_board_and_the_icons_name_real_boards(self):
        self.assertIn(FEELINGS_BOARD, BOARD_NAMES)
        for name in BOARD_ICONS:
            self.assertIn(name, BOARD_NAMES)

    def test_every_board_has_a_picture(self):
        self.assertEqual([board["name"] for board in boards()], BOARD_NAMES)
        for board in boards():
            self.assertEqual(board["icon"], BOARD_ICONS[board["name"]])

        # A board nobody chose a picture for is shown with its first word's.
        with mock.patch("salitaaco.utils.board.BOARD_ICONS", {}):
            for board, category in zip(boards(), CATEGORIES):
                self.assertEqual(board["icon"], category["items"][0]["e"])

    def test_the_vocabulary_itself_is_left_as_it_is(self):
        boards()
        for category in CATEGORIES:
            self.assertEqual(sorted(category), ["items", "name"])


class BoardScreensTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])

    def test_board_carries_what_the_home_screen_shows(self):
        self.login_as("miguel")
        board_data = self.client.get(reverse("board")).context["board_data"]

        self.assertEqual([tile["w"] for tile in board_data["quick_words"]], QUICK_WORDS)
        self.assertEqual(board_data["feelings_board"], "Pakiramdam")
        self.assertEqual(board_data["verb_category"], "Pandiwa")
        self.assertEqual([board["icon"] for board in board_data["categories"]], list(BOARD_ICONS.values()))

    def test_board_page_has_the_screens_and_the_sentence_buttons(self):
        self.login_as("miguel")
        response = self.client.get(reverse("board"))

        for button in ['id="playBtn"', 'id="undoBtn"', 'id="clearBtn"']:
            self.assertContains(response, button, count=1)
        self.assertContains(response, "↩ Ibalik")
        self.assertContains(response, '<h1 class="screenTitle" id="screenTitle">Ano ang gusto mong sabihin?</h1>')
        self.assertContains(response, '<a class="iconbtn hidden" id="backToBoards" href="#boards">')
        self.assertContains(response, "Mabilis na Salita")
        self.assertContains(response, "Ang Nararamdaman Ko")
        # Both grids are drawn at the size chosen in Settings.
        self.assertContains(response, 'class="grid tiles-medium" id="grid"')
        self.assertContains(response, 'class="grid tiles-medium" id="feelingsGrid"')

    def navigation(self, route):
        return {
            item["id"]: item
            for category in self.client.get(reverse(route)).context["navigation_items"]
            for item in category["items"]
        }

    def test_a_childs_navigation_leads_to_the_boards_screens(self):
        self.login_as("miguel")
        items = self.navigation("board")

        board = reverse("board")
        self.assertEqual(
            {item_id: item["url"] for item_id, item in items.items()},
            {
                "home": f"{board}#home",
                "boards": f"{board}#boards",
                "favorites": f"{board}#favorites",
                "profile": reverse("profile"),
            },
        )
        # The page arrives with Home lit; board.js moves the light as the screens change.
        self.assertEqual([item_id for item_id, item in items.items() if item["active"]], ["home"])

    def test_profile_stays_lit_on_a_childs_settings_page(self):
        self.login_as("miguel")
        for route in ["profile", "settings"]:
            items = self.navigation(route)
            self.assertEqual([item_id for item_id, item in items.items() if item["active"]], ["profile"], route)

    def test_a_guardian_on_a_board_gets_the_screens_and_nothing_else_along_the_bottom(self):
        self.login_as("nanay")
        child = self.nanay.children.get()
        for url in [reverse("board"), reverse("child_board", args=[child.uuid])]:
            response = self.client.get(url)
            for screen in ["home", "boards", "favorites"]:
                self.assertContains(response, f'<a href="#{screen}">')
            self.assertNotContains(response, f'href="{reverse("profile")}"')

    def test_a_childs_navigation_is_not_replaced_on_the_board(self):
        self.login_as("miguel")
        response = self.client.get(reverse("board"))
        self.assertContains(response, f'href="{reverse("board")}#boards"')
        self.assertNotContains(response, '<a href="#boards">')


class ChildProfileTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])

    def test_a_childs_profile_opens_with_who_they_are_and_leads_to_settings(self):
        self.login_as("miguel")
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "<h1>Miguel</h1>")
        self.assertContains(response, "@miguel · 7 taong gulang")
        self.assertContains(response, f'<a class="iconbtn" href="{reverse("settings")}">')
        # A child logs in to their own account, so there is no caretaker area and no PIN.
        self.assertNotContains(response, "PIN")
        # What the account could do before is still here.
        for text in ["Impormasyon ng Account", "Palitan ang Password", "Burahin ang Account"]:
            self.assertContains(response, text)

    def test_a_child_without_an_age_shows_none(self):
        self.login_as("ana")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "<h1>Ana</h1>")
        self.assertNotContains(response, "taong gulang")

    def test_the_other_roles_keep_the_plain_profile_page(self):
        for username in ["nanay", "developer"]:
            self.login_as(username)
            response = self.client.get(reverse("profile"))
            self.assertNotContains(response, "profileHero")
            self.assertContains(response, "Impormasyon ng Account")

    def test_a_childs_settings_page_leads_back_to_the_profile(self):
        self.login_as("miguel")
        self.assertContains(self.client.get(reverse("settings")), f'<a class="iconbtn" href="{reverse("profile")}">← Profile</a>')
        self.login_as("nanay")
        self.assertNotContains(self.client.get(reverse("settings")), "← Profile")
