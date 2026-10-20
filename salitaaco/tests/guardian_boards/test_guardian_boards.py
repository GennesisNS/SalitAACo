from django.test import override_settings
from django.urls import reverse

from salitaaco.defaults.plans import DEFAULT_PLUS_BOARD_LIMIT
from salitaaco.forms.guardian_words.guardian_board import GuardianBoardForm
from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils import admin_stats, analytics
from salitaaco.utils.board import board_names
from salitaaco.utils.plans import approve_payment


@override_settings(ELEVENLABS_API_KEY="", ELEVENLABS_VOICE_ID="")
class GuardianBoardsBase(UserBase):
    """
    Nanay is Miguel's guardian and on Plus; Tatay is Ana's, on Free. ElevenLabs
    is not set up, so nothing is sent to it.
    """
    url = reverse("guardian_boards")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben", children=[cls.ana])
        approve_payment(make_payment(cls.nanay), cls.developer)

    def add(self, name="Bahay ni Lola", emoji="🏡"):
        return self.client.post(self.url, {"board_form": "", "name": name, "emoji": emoji})

    def make_board(self, guardian, name="Bahay ni Lola", emoji="🏡", tiles=()):
        board = GuardianBoard.objects.create(guardian=guardian, name=name, emoji=emoji)
        for word in tiles:
            GuardianWord.objects.create(guardian=guardian, board=name, word=word, emoji="⭐")
        return board

    def boards_on(self, route="board", *args):
        """{board name: its tiles' words} of a board page."""
        categories = self.client.get(reverse(route, args=args)).context["board_data"]["categories"]
        return {category["name"]: [item["w"] for item in category["items"]] for category in categories}

    def set_limits(self, **limits):
        setting = SiteSetting.load()
        for field, value in limits.items():
            setattr(setting, field, value)
        setting.save()


class GuardianBoardFormTest(GuardianBoardsBase):
    def test_a_name_no_board_has_and_an_emoji(self):
        self.make_board(self.nanay, "Bahay ni Lola")
        for name in ["Tao", "tao", "bahay ni  LOLA"]:
            form = GuardianBoardForm({"name": name, "emoji": "🏡"}, guardian=self.nanay)
            self.assertEqual(form.errors["name"], ["May board na may ganitong pangalan."], name)
        form = GuardianBoardForm({"name": "Paaralan", "emoji": "ABC"}, guardian=self.nanay)
        self.assertEqual(form.errors["emoji"], ["Emoji ang ilagay, hindi titik o numero."])

        form = GuardianBoardForm({"name": "  Paaralan  ni  Miguel ", "emoji": "🏫"}, guardian=self.nanay)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Paaralan ni Miguel")
        # Another family's board name is no concern of hers.
        self.assertTrue(GuardianBoardForm({"name": "Bahay ni Lola", "emoji": "🏡"}, guardian=self.tatay).is_valid())

    def test_her_tiles_can_go_on_her_boards(self):
        self.make_board(self.nanay, "Bahay ni Lola")
        choices = [value for value, label in GuardianWordForm(guardian=self.nanay).fields["board"].choices]
        self.assertEqual(choices, ["", *board_names(), "Bahay ni Lola"])
        self.assertNotIn("Bahay ni Lola", dict(GuardianWordForm(guardian=self.tatay).fields["board"].choices))


class GuardianBoardsPageTest(GuardianBoardsBase):
    def test_only_guardians_open_the_page_and_it_is_in_the_sidebar(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, f'<a class="sidebarItem active" href="{self.url}" aria-current="page">')

    def test_on_plus_a_board_is_made_and_counted(self):
        self.login_as("nanay")
        self.assertContains(self.client.get(self.url), f"0 sa {DEFAULT_PLUS_BOARD_LIMIT} na sariling board")

        response = self.add()
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nagawa na ang board na “Bahay ni Lola”. Lagyan ito ng tile sa Sariling Tile."])
        board = GuardianBoard.objects.get()
        self.assertEqual((board.guardian, board.name, board.emoji), (self.nanay, "Bahay ni Lola", "🏡"))
        response = self.client.get(self.url)
        self.assertContains(response, f"1 sa {DEFAULT_PLUS_BOARD_LIMIT} na sariling board")
        self.assertContains(response, "Wala pang tile")

    def test_on_free_with_no_boards_allowed_nothing_can_be_made(self):
        expected = f"Para sa SalitAACo Plus ang sariling board: hanggang {DEFAULT_PLUS_BOARD_LIMIT}. Kunin ang Plus para makapagdagdag."
        self.login_as("tatay")
        response = self.client.get(self.url)
        self.assertContains(response, expected)
        self.assertNotContains(response, 'name="board_form"')
        self.assertEqual(messages_of(self.add()), [expected])
        self.assertFalse(GuardianBoard.objects.exists())

        # An admin can let Free have some.
        self.set_limits(free_board_limit=1)
        self.assertRedirects(self.add(), self.url)
        self.assertEqual(GuardianBoard.objects.filter(guardian=self.tatay).count(), 1)

    def test_the_limit_counts_every_board_of_hers(self):
        self.set_limits(plus_board_limit=1)
        self.make_board(self.nanay, "Bahay ni Lola")
        self.login_as("nanay")
        self.assertEqual(messages_of(self.add(name="Paaralan")), [
            "Naabot mo na ang 1 na sariling board. Magbura muna ng isa para makapagdagdag ng bago.",
        ])

    def test_deleting_a_board_deletes_its_tiles_switches_and_counts(self):
        board = self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena", "duyan"])
        GuardianWord.objects.create(guardian=self.nanay, board="Tao", word="Kuya Jun", emoji="👦")
        HiddenBoard.objects.create(child=self.nanay.children.get(), board="Bahay ni Lola")
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Bahay ni Lola")
        WordUsage.record_use(self.miguel, "duyan")
        other = self.make_board(self.tatay, "Bahay ni Lola")  # another family's, untouched

        self.login_as("tatay")
        self.assertEqual(self.client.post(reverse("remove_guardian_board", args=[board.uuid])).status_code, 404)
        self.login_as("nanay")
        response = self.client.post(reverse("remove_guardian_board", args=[board.uuid]))

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nabura na ang board na “Bahay ni Lola” at ang mga tile nito."])
        self.assertEqual(list(GuardianBoard.objects.all()), [other])
        self.assertEqual(list(GuardianWord.objects.values_list("word", flat=True)), ["Kuya Jun"])
        self.assertFalse(HiddenBoard.objects.exists())
        self.assertFalse(DailyUsage.objects.filter(kind=DailyUsage.BOARD).exists())
        self.assertFalse(WordUsage.objects.filter(word="duyan").exists())


class GuardianBoardsOnTheBoardsTest(GuardianBoardsBase):
    def test_a_board_with_a_tile_shows_after_the_apps_on_every_board_of_the_family(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena", "duyan"])
        self.make_board(self.nanay, "Paaralan")  # no tile yet: nothing to show

        self.login_as("nanay")
        for boards in [self.boards_on("board"), self.boards_on("child_board", self.nanay.children.get().uuid)]:
            self.assertEqual(list(boards)[-1], "Bahay ni Lola")
            self.assertEqual(boards["Bahay ni Lola"], ["Lola Nena", "duyan"])
            self.assertNotIn("Paaralan", boards)

        self.login_as("miguel")
        self.assertEqual(self.boards_on()["Bahay ni Lola"], ["Lola Nena", "duyan"])
        for other in ["ana", "developer"]:
            self.login_as(other)
            self.assertNotIn("Bahay ni Lola", self.boards_on(), other)

    def test_over_the_limit_the_oldest_boards_show_and_the_others_hide_with_their_tiles(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        self.make_board(self.nanay, "Paaralan", tiles=["guro"])
        self.set_limits(plus_board_limit=1)

        self.login_as("miguel")
        boards = self.boards_on()
        self.assertIn("Bahay ni Lola", boards)
        self.assertNotIn("Paaralan", boards)

        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertEqual([row["shown"] for row in response.context["boards"]], [True, False])
        self.assertContains(response, "Nakatago muna sa mga board ang 1 sa mga sariling board mo")
        words = {row["word"].word: row["shown"] for row in self.client.get(reverse("guardian_words")).context["words"]}
        self.assertEqual(words, {"Lola Nena": True, "guro": False})

    def test_her_board_is_turned_on_and_off_for_each_child(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        child = self.nanay.children.get()
        url = reverse("child_boards", args=[child.uuid])

        self.login_as("nanay")
        response = self.client.get(url)
        self.assertContains(response, "🏡 Bahay ni Lola")
        self.assertContains(response, '<span class="planTag">Sarili</span>', count=1)

        shown = [name for name in board_names() if name != "Tao"]
        self.assertRedirects(self.client.post(url, {"boards_form": "", "boards": shown}), url)
        self.assertEqual(set(child.hidden_boards.values_list("board", flat=True)), {"Tao", "Bahay ni Lola"})

        self.login_as("miguel")
        self.assertNotIn("Bahay ni Lola", self.boards_on())

    def test_the_children_table_counts_her_boards(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        self.login_as("nanay")
        child = self.client.get(reverse("children")).context["children"][0]
        self.assertEqual((child.shown_boards, child.total_boards), (len(board_names()) + 1, len(board_names()) + 1))

    def test_opening_her_board_is_counted_and_another_familys_is_not(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        self.make_board(self.tatay, "Kubo", tiles=["kubo"])
        self.set_limits(free_board_limit=1, free_word_limit=1)

        self.login_as("miguel")
        self.assertEqual(self.client.post(reverse("record_board_open"), {"board": "Bahay ni Lola"}).status_code, 200)
        self.assertEqual(self.client.post(reverse("record_board_open"), {"board": "Kubo"}).status_code, 400)
        self.assertEqual(list(DailyUsage.objects.filter(kind=DailyUsage.BOARD).values_list("name", flat=True)), ["Bahay ni Lola"])

        # The guardian sees it on the child's usage page, with its picture.
        self.login_as("nanay")
        boards = self.client.get(reverse("child_usage", args=[self.nanay.children.get().uuid])).context["boards"]
        self.assertEqual([(row["name"], row["icon"]) for row in boards], [("Bahay ni Lola", "🏡")])


class AdminStatsTest(GuardianBoardsBase):
    def test_a_familys_own_boards_and_tiles_are_not_in_the_admins_numbers(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Bahay ni Lola")
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Tao")
        WordUsage.record_use(self.miguel, "Lola Nena")
        WordUsage.record_use(self.miguel, "ako")

        self.assertEqual([row["name"] for row in admin_stats.board_opens()], ["Tao"])
        self.assertEqual([row["word"] for row in analytics.top_words()], ["ako"])
