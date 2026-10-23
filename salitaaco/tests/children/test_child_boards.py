from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.children.child_boards import ChildBoardsForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.board import board_names
from salitaaco.utils.guardian_boards import child_boards

ALL_BOARDS = ["Tao", "Bagay", "Pagkain", "Lugar", "Pandiwa", "Pakiramdam"]


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class ChildBoardsBase(UserBase):
    """Nanay is the guardian of Miguel and Ana. Tatay is a guardian of nobody."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel, cls.ana])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.ana_account = ChildAccount.objects.get(user=cls.ana)
        cls.url = reverse("child_boards", args=[cls.miguel_account.uuid])

    def hidden(self, child=None):
        return sorted(HiddenBoard.objects.filter(child=child or self.miguel_account).values_list("board", flat=True))

    def save(self, *shown):
        return self.client.post(self.url, {"boards_form": "", "boards": list(shown)})


class ChildBoardsFormTest(ChildBoardsBase):
    def test_the_choices_are_the_boards_it_is_given(self):
        # The page gives it the family's boards: the vocabulary's, then the guardian's own.
        self.assertEqual(board_names(), ALL_BOARDS)
        form = ChildBoardsForm(names=ALL_BOARDS + ["Bahay ni Lola"])
        self.assertEqual([value for value, label in form.fields["boards"].choices], ALL_BOARDS + ["Bahay ni Lola"])

    def test_at_least_one_board_has_to_stay_on(self):
        form = ChildBoardsForm({"boards": []}, names=ALL_BOARDS)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["boards"], ["Kailangang may kahit isang board na naka-on para sa bata."])
        self.assertTrue(ChildBoardsForm({"boards": ["Tao"]}, names=ALL_BOARDS).is_valid())

    def test_a_board_that_does_not_exist_is_refused(self):
        form = ChildBoardsForm({"boards": ["Tao", "Wala Nito"]}, names=ALL_BOARDS)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["boards"], ["Walang ganitong board."])


class ChildBoardsPageTest(ChildBoardsBase):
    def test_only_the_childs_guardian_opens_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("tatay")
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.save("Tao").status_code, 404)
        self.assertEqual(self.hidden(), [])

    def test_every_board_starts_on_and_each_is_a_switch(self):
        self.login_as("nanay")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["board"]["name"] for row in response.context["rows"]], ALL_BOARDS)
        self.assertEqual(response.context["boards_form"].initial["boards"], ALL_BOARDS)
        self.assertEqual(response.context["rows"][0]["word_count"], 15)
        self.assertEqual(len(response.context["rows"][0]["preview"]), 4)
        self.assertContains(response, '<label class="switch">', count=len(ALL_BOARDS))
        self.assertContains(response, 'type="checkbox" name="boards" value="Tao"')
        self.assertContains(response, "checked", count=len(ALL_BOARDS))
        self.assertContains(response, "Napiling bata")

    def test_turning_boards_off_stores_only_the_ones_turned_off(self):
        self.login_as("nanay")
        response = self.save("Tao", "Pagkain", "Pandiwa", "Pakiramdam")

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang mga board ni Miguel."])
        self.assertEqual(self.hidden(), ["Bagay", "Lugar"])
        # Only Miguel's boards changed.
        self.assertEqual(self.hidden(self.ana_account), [])

        response = self.client.get(self.url)
        self.assertEqual(response.context["boards_form"].initial["boards"], ["Tao", "Pagkain", "Pandiwa", "Pakiramdam"])
        self.assertContains(response, "checked", count=4)

        # Saving again replaces the choice instead of adding to it.
        self.save("Bagay")
        self.assertEqual(self.hidden(), ["Lugar", "Pagkain", "Pakiramdam", "Pandiwa", "Tao"])

    def test_the_last_board_cannot_be_turned_off(self):
        self.login_as("nanay")
        self.save("Tao")

        response = self.save()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kailangang may kahit isang board na naka-on para sa bata.")
        self.assertEqual(len(self.hidden()), 5)

    def test_an_unknown_board_saves_nothing(self):
        self.login_as("nanay")
        response = self.save("Tao", "Wala Nito")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Walang ganitong board.")
        self.assertEqual(self.hidden(), [])

    def test_restoring_turns_every_board_back_on(self):
        self.login_as("nanay")
        self.save("Tao")
        HiddenBoard.objects.create(child=self.ana_account, board="Lugar")

        response = self.client.post(self.url, {"restore_boards_form": ""})

        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response)[-1], "Naka-on na muli ang lahat ng board ni Miguel.")
        self.assertEqual(self.hidden(), [])
        self.assertEqual(self.hidden(self.ana_account), ["Lugar"])


class BoardsOnTheBoardTest(ChildBoardsBase):
    def board_names_on(self, url):
        return [board["name"] for board in self.client.get(url).context["board_data"]["categories"]]

    def test_a_child_sees_only_the_boards_left_on(self):
        for name in ["Bagay", "Pakiramdam"]:
            HiddenBoard.objects.create(child=self.miguel_account, board=name)

        self.login_as("miguel")
        self.assertEqual(self.board_names_on(reverse("board")), ["Tao", "Pagkain", "Lugar", "Pandiwa"])
        # The quick words stay on Home whatever board they come from.
        board_data = self.client.get(reverse("board")).context["board_data"]
        self.assertEqual(len(board_data["quick_words"]), 6)

        # Ana's boards are her own.
        self.login_as("ana")
        self.assertEqual(self.board_names_on(reverse("board")), ALL_BOARDS)

    def test_the_guardian_sees_the_childs_board_as_the_child_does_and_their_own_in_full(self):
        HiddenBoard.objects.create(child=self.miguel_account, board="Bagay")
        self.login_as("nanay")
        child_board = reverse("child_board", args=[self.miguel_account.uuid])
        self.assertEqual(self.board_names_on(child_board), ["Tao", "Pagkain", "Lugar", "Pandiwa", "Pakiramdam"])
        self.assertEqual(self.board_names_on(reverse("board")), ALL_BOARDS)

    def test_a_child_is_never_left_without_a_board(self):
        # Rows for boards the vocabulary no longer has are ignored.
        HiddenBoard.objects.create(child=self.miguel_account, board="Lumang Board")
        self.assertEqual([board["name"] for board in child_boards(self.miguel_account)], ALL_BOARDS)

        # Rows that would hide everything show everything.
        for name in ALL_BOARDS:
            HiddenBoard.objects.create(child=self.miguel_account, board=name)
        self.assertEqual([board["name"] for board in child_boards(self.miguel_account)], ALL_BOARDS)

    def test_deleting_the_child_deletes_their_rows(self):
        HiddenBoard.objects.create(child=self.miguel_account, board="Bagay")
        self.miguel.delete()
        self.assertFalse(HiddenBoard.objects.exists())


class ChildVoicePageTest(ChildBoardsBase):
    def test_only_the_childs_guardian_opens_the_page(self):
        url = reverse("child_voice", args=[self.miguel_account.uuid])
        self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        self.login_as("tatay")
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_without_family_voices_the_apps_voice_is_the_only_choice(self):
        self.login_as("nanay")
        response = self.client.get(reverse("child_voice", args=[self.miguel_account.uuid]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["voice_choices"]), 1)
        self.assertFalse(response.context["has_family_voices"])
        self.assertContains(response, "Karaniwang boses ng app")
        self.assertContains(response, "Wala pang boses ng pamilya.")
        self.assertContains(response, f'href="{reverse("family_voices")}"')
