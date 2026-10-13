from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.vocabulary.set_board_status import SetBoardStatusForm
from salitaaco.models.board_status import BoardStatus
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.board import all_boards, board_names, boards, every_board

ALL_BOARDS = ["Tao", "Bagay", "Pagkain", "Lugar", "Pandiwa", "Pakiramdam"]


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class AdminBoardsBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.url = reverse("admin_boards")

    def set_status(self, board, published):
        data = {"board": board, **({"published": "on"} if published else {})}
        return self.client.post(reverse("set_board_status"), data)


class BoardStatusTest(AdminBoardsBase):
    def test_every_board_is_published_until_an_admin_hides_it(self):
        self.assertEqual(board_names(), ALL_BOARDS)
        self.assertTrue(all(board["is_published"] for board in every_board()))

        BoardStatus.objects.create(board="Lugar", is_published=False)

        self.assertEqual(board_names(), ["Tao", "Bagay", "Pagkain", "Pandiwa", "Pakiramdam"])
        self.assertEqual([board["name"] for board in every_board()], ALL_BOARDS)
        self.assertEqual([board["name"] for board in every_board() if not board["is_published"]], ["Lugar"])
        # What a board page is given has no status on it: only boards that can be shown.
        self.assertEqual(sorted(all_boards()[0]), ["icon", "items", "name"])

    def test_the_last_published_board_cannot_be_hidden(self):
        for name in ALL_BOARDS[1:]:
            BoardStatus.objects.create(board=name, is_published=False)

        form = SetBoardStatusForm({"board": "Tao"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Kailangang may kahit isang board na naka-publish."])
        # Publishing is always allowed, and so is hiding while another stays.
        self.assertTrue(SetBoardStatusForm({"board": "Bagay", "published": "on"}).is_valid())
        BoardStatus.objects.filter(board="Bagay").update(is_published=True)
        self.assertTrue(SetBoardStatusForm({"board": "Tao"}).is_valid())

    def test_a_board_that_does_not_exist_is_refused(self):
        form = SetBoardStatusForm({"board": "Wala Nito"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["board"], ["Walang ganitong board."])


class AdminBoardsPageTest(AdminBoardsBase):
    def test_only_admins_open_the_page_and_change_a_status(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.set_status("Lugar", False).status_code, 302)
        self.assertFalse(BoardStatus.objects.exists())

    def test_page_lists_every_board_with_its_numbers_and_an_action(self):
        DailyUsage.objects.create(user=self.miguel, day="2026-10-01", kind=DailyUsage.BOARD, name="Tao", use_count=4)
        DailyUsage.objects.create(user=self.ana, day="2026-10-02", kind=DailyUsage.BOARD, name="Tao", use_count=3)
        BoardStatus.objects.create(board="Lugar", is_published=False)
        self.login_as("developer")

        response = self.client.get(self.url)

        rows = {board["name"]: board for board in response.context["boards"]}
        self.assertEqual(list(rows), ALL_BOARDS)
        self.assertEqual((rows["Tao"]["word_count"], rows["Tao"]["opens"], rows["Tao"]["is_published"]), (15, 7, True))
        self.assertEqual((rows["Lugar"]["opens"], rows["Lugar"]["is_published"]), (0, False))
        self.assertIsNotNone(rows["Lugar"]["updated_at"])
        self.assertIsNone(rows["Tao"]["updated_at"])
        self.assertEqual(response.context["published_count"], 5)
        self.assertContains(response, "<th>Aksyon</th>")
        self.assertContains(response, ">Itago</button>", count=5)
        self.assertContains(response, ">I-publish</button>", count=1)

    def test_hiding_and_publishing(self):
        self.login_as("developer")
        self.assertEqual(self.client.get(reverse("set_board_status")).status_code, 405)

        response = self.set_status("Lugar", False)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nakatago na sa lahat ang board na “Lugar”."])
        self.assertFalse(BoardStatus.objects.get(board="Lugar").is_published)

        response = self.set_status("Lugar", True)
        self.assertEqual(messages_of(response)[-1], "Naka-publish na ang board na “Lugar”.")
        self.assertEqual(BoardStatus.objects.count(), 1)
        self.assertTrue(BoardStatus.objects.get().is_published)

    def test_what_cannot_be_done_is_said_and_changes_nothing(self):
        for name in ALL_BOARDS[1:]:
            BoardStatus.objects.create(board=name, is_published=False)
        self.login_as("developer")

        self.assertEqual(messages_of(self.set_status("Tao", False)), ["Kailangang may kahit isang board na naka-publish."])
        self.assertEqual(messages_of(self.set_status("Wala Nito", False))[-1], "Walang ganitong board.")
        self.assertEqual(board_names(), ["Tao"])
        # The page offers no way to hide the last one.
        self.assertContains(self.client.get(self.url), 'disabled title="Ito na lang ang naka-publish"', count=1)


class HiddenBoardEverywhereTest(AdminBoardsBase):
    """A board an admin hid is shown to nobody."""

    def setUp(self):
        BoardStatus.objects.create(board="Lugar", is_published=False)

    def test_no_board_page_shows_it(self):
        expected = ["Tao", "Bagay", "Pagkain", "Pandiwa", "Pakiramdam"]
        pages = [("miguel", reverse("board")), ("nanay", reverse("board")),
                 ("nanay", reverse("child_board", args=[self.miguel_account.uuid])), ("developer", reverse("board"))]
        for username, url in pages:
            self.login_as(username)
            board_data = self.client.get(url).context["board_data"]
            self.assertEqual([board["name"] for board in board_data["categories"]], expected, f"{username} {url}")

    def test_a_guardian_is_not_offered_it_and_the_numbers_leave_it_out(self):
        self.login_as("nanay")
        response = self.client.get(reverse("child_boards", args=[self.miguel_account.uuid]))
        self.assertEqual([row["board"]["name"] for row in response.context["rows"]], ["Tao", "Bagay", "Pagkain", "Pandiwa", "Pakiramdam"])

        child = self.client.get(reverse("overview")).context["children"][0]
        self.assertEqual((child.shown_boards, child.total_boards), (5, 5))

        # Turning it on by hand in the form is refused: it is not among the choices.
        response = self.client.post(reverse("child_boards", args=[self.miguel_account.uuid]), {"boards_form": "", "boards": ["Lugar"]})
        self.assertContains(response, "Walang ganitong board.")

    def test_opening_it_is_no_longer_counted(self):
        self.login_as("miguel")
        self.assertEqual(self.client.post(reverse("record_board_open"), {"board": "Lugar"}).status_code, 400)
        self.assertEqual(self.client.post(reverse("record_board_open"), {"board": "Tao"}).status_code, 200)

    def test_a_child_whose_only_board_was_hidden_gets_the_published_ones(self):
        for name in ["Tao", "Bagay", "Pagkain", "Pandiwa", "Pakiramdam"]:
            HiddenBoard.objects.create(child=self.miguel_account, board=name)
        # The guardian left only Lugar on, and then the admin hid Lugar.
        self.assertEqual([board["name"] for board in boards(self.miguel_account)], ["Tao", "Bagay", "Pagkain", "Pandiwa", "Pakiramdam"])
