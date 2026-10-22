import io
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from PIL import Image

from salitaaco.defaults.plans import DEFAULT_PLUS_BOARD_LIMIT
from salitaaco.forms.guardian_words.guardian_board import GuardianBoardForm
from salitaaco.forms.guardian_words.guardian_word import GuardianWordForm
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.payment import Payment
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.payments_base import make_payment, messages_of
from salitaaco.tests.users_base import UserBase, image_bytes, image_upload, make_guardian
from salitaaco.utils import admin_stats, analytics
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.board import board_names
from salitaaco.utils.plans import approve_payment

NEW = "new-board"


@override_settings(ELEVENLABS_API_KEY="", ELEVENLABS_VOICE_ID="")
class GuardianBoardsBase(UserBase):
    """
    Custom boards, set up on a child's Mga Board. Nanay is Miguel's guardian
    and on Plus; Tatay is Ana's, on Free. ElevenLabs is not set up, so nothing
    is sent to it.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.tatay = make_guardian("tatay", "Tatay Ben", children=[cls.ana])
        approve_payment(make_payment(cls.nanay), cls.developer)

    def setUp(self):
        super().setUp()
        self.child = self.nanay.children.get()
        self.url = reverse("child_boards", args=[self.child.uuid])

    def add(self, name="Bahay ni Lola", emoji="🏡", kind="emoji", image=None, url=None):
        data = {"new_board_form": "", f"{NEW}-name": name, f"{NEW}-icon_kind": kind, f"{NEW}-emoji": emoji}
        if image is not None:
            data[f"{NEW}-icon_image"] = image
        return self.client.post(url or self.url, data)

    def edit(self, board, **fields):
        prefix = f"board-{board.pk}"
        data = {"name": board.name, "icon_kind": "image" if board.has_icon_image else "emoji", "emoji": board.emoji, **fields}
        return self.client.post(self.url, {"edit_board_form": str(board.uuid), **{f"{prefix}-{key}": value for key, value in data.items()}})

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
    def form(self, guardian=None, editing=None, files=None, **data):
        return GuardianBoardForm({"icon_kind": "emoji", **data}, files or {}, guardian=guardian or self.nanay, editing=editing)

    def test_a_name_no_board_has(self):
        self.make_board(self.nanay, "Bahay ni Lola")
        for name in ["", "Tao", "tao", "bahay ni  LOLA"]:
            self.assertIn("name", self.form(name=name, emoji="🏡").errors, name)
        self.assertEqual(self.form(name="Tao", emoji="🏡").errors["name"], ["May board na may ganitong pangalan."])

        form = self.form(name="  Paaralan  ni  Miguel ", emoji="🏫")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["name"], "Paaralan ni Miguel")
        # Another family's board name is no concern of hers, and a board keeps its own.
        self.assertTrue(self.form(guardian=self.tatay, name="Bahay ni Lola", emoji="🏡").is_valid())
        board = GuardianBoard.objects.get()
        self.assertTrue(self.form(editing=board, name="Bahay ni Lola", emoji="🏡").is_valid())

    def test_the_picture_is_an_emoji_or_an_uploaded_jpg_png_or_webp(self):
        self.assertEqual(self.form(name="Paaralan").errors["emoji"], ["Ilagay ang emoji ng board."])
        self.assertEqual(self.form(name="Paaralan", emoji="ABC").errors["emoji"], ["Emoji ang ilagay, hindi titik o numero."])

        self.assertEqual(self.form(name="Paaralan", icon_kind="image").errors["icon_image"], ["Pumili ng larawan ng board."])
        for picture, error in [
            (image_upload("icon.gif", "GIF", "image/gif"), "JPEG, PNG o WebP lang ang puwedeng larawan."),
            (image_upload(padding=5 * 1024 * 1024), "Masyadong malaki ang larawan (max 5MB)."),
        ]:
            form = self.form(name="Paaralan", icon_kind="image", files={"icon_image": picture})
            self.assertEqual(form.errors["icon_image"], [error])
        self.assertTrue(self.form(name="Paaralan", icon_kind="image", files={"icon_image": image_upload()}).is_valid())

    def test_her_tiles_can_go_on_her_boards(self):
        self.make_board(self.nanay, "Bahay ni Lola")
        choices = [value for value, label in GuardianWordForm(guardian=self.nanay).fields["board"].choices]
        self.assertEqual(choices, ["", *board_names(), "Bahay ni Lola"])
        self.assertNotIn("Bahay ni Lola", dict(GuardianWordForm(guardian=self.tatay).fields["board"].choices))


class MgaBoardPageTest(GuardianBoardsBase):
    def test_the_sariling_board_tab_is_gone_and_mga_board_has_the_add_button(self):
        with self.assertRaises(NoReverseMatch):
            reverse("guardian_boards")
        self.login_as("nanay")
        self.assertEqual(self.client.get("/dashboard/own-boards/").status_code, 404)
        response = self.client.get(self.url)
        self.assertContains(response, 'data-open-modal="new-board">＋ Magdagdag ng board</button>')
        self.assertContains(response, 'name="new_board_form">I-save</button>')
        self.assertContains(response, 'data-close-modal="new-board">Kanselahin</button>')
        self.assertContains(response, f"0 sa {DEFAULT_PLUS_BOARD_LIMIT} na custom board")
        # The app's boards cannot be changed or deleted here.
        self.assertContains(response, "Board ng app", count=len(board_names()))

    def test_a_new_board_shows_in_the_table_at_once_marked_custom(self):
        self.login_as("nanay")
        response = self.add()
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nagawa na ang board na “Bahay ni Lola”. Lagyan ito ng tile sa Sariling Tile."])
        board = GuardianBoard.objects.get()
        self.assertEqual((board.guardian, board.name, board.emoji, board.has_icon_image), (self.nanay, "Bahay ni Lola", "🏡", False))

        response = self.client.get(self.url)
        row = response.context["rows"][-1]
        self.assertEqual((row["board"]["name"], row["own"], row["word_count"]), ("Bahay ni Lola", board, 0))
        self.assertIsNotNone(row["switch"])
        self.assertContains(response, '<span class="planTag">Custom</span>', count=1)
        self.assertContains(response, f'data-open-modal="edit-board-{board.uuid}">I-edit</button>')
        self.assertContains(response, f'data-open-modal="delete-board-{board.uuid}">Burahin</button>')
        self.assertContains(response, f"1 sa {DEFAULT_PLUS_BOARD_LIMIT} na custom board")

    def test_a_board_with_an_uploaded_picture(self):
        self.login_as("nanay")
        self.add(name="Paaralan", kind="image", emoji="", image=image_upload())
        board = GuardianBoard.objects.get()
        self.assertTrue(board.icon_image.name.startswith("guardian-board-icons/"))
        self.assertTrue(board.icon_image.name.endswith(".webp"))
        self.assertEqual((board.emoji, board.icon_mime), ("", "image/webp"))

        icon = reverse("guardian_board_icon", args=[board.uuid])
        self.assertContains(self.client.get(self.url), f'<img class="boardIcon" src="{icon}?v=')
        GuardianWord.objects.create(guardian=self.nanay, board="Paaralan", word="guro", emoji="🧑‍🏫")
        self.assertTrue(self.client.get(reverse("board")).context["board_data"]["categories"][-1]["icon_url"].startswith(icon))

        # Only the family sees it.
        for username, status in [("nanay", 200), ("miguel", 200), ("tatay", 404), ("ana", 404), ("developer", 404)]:
            self.login_as(username)
            self.assertEqual(self.client.get(icon).status_code, status, username)

    def test_a_big_picture_is_made_small_before_it_is_kept(self):
        buffer = io.BytesIO()
        Image.new("RGB", (2000, 1000), "teal").save(buffer, "JPEG", quality=95)
        upload = SimpleUploadedFile("malaki.jpg", buffer.getvalue(), content_type="image/jpeg")

        self.login_as("nanay")
        self.add(name="Paaralan", kind="image", emoji="", image=upload)
        board = GuardianBoard.objects.get()
        with Image.open(board.icon_image.path) as stored:
            self.assertEqual((stored.format, stored.size), ("WEBP", (256, 128)))
        self.assertLess(board.icon_image.size, len(buffer.getvalue()))

    def test_the_window_has_the_name_and_picture_fields_without_a_tile_preview(self):
        self.make_board(self.nanay, "Bahay ni Lola", emoji="🏡")
        self.login_as("nanay")
        response = self.client.get(self.url)
        self.assertContains(response, 'value="Bahay ni Lola"')
        self.assertContains(response, 'value="🏡"')
        self.assertNotContains(response, "data-preview-name")
        self.assertNotContains(response, "Bagong board")
        self.assertContains(response, "📷 Pumili ng larawan", count=2)

    def test_a_form_that_is_not_valid_reopens_and_saves_nothing(self):
        self.login_as("nanay")
        response = self.add(name="Tao")
        self.assertContains(response, "May board na may ganitong pangalan.")
        self.assertContains(response, 'data-modal="new-board" data-open="true"')
        self.assertFalse(GuardianBoard.objects.exists())

    def test_on_free_with_no_boards_allowed_nothing_can_be_made(self):
        tatays = reverse("child_boards", args=[self.tatay.children.get().uuid])
        expected = f"Para sa SalitAACo Plus ang sariling board: hanggang {DEFAULT_PLUS_BOARD_LIMIT}. Kunin ang Plus para makapagdagdag."
        self.login_as("tatay")
        response = self.client.get(tatays)
        self.assertContains(response, expected)
        self.assertNotContains(response, 'data-open-modal="new-board"')
        self.assertEqual(messages_of(self.add(url=tatays)), [expected])
        self.assertFalse(GuardianBoard.objects.exists())

        # An admin can let Free have some.
        self.set_limits(free_board_limit=1)
        self.assertRedirects(self.add(url=tatays), tatays)
        self.assertEqual(GuardianBoard.objects.filter(guardian=self.tatay).count(), 1)

    def test_the_limit_counts_every_board_of_hers(self):
        self.set_limits(plus_board_limit=1)
        self.make_board(self.nanay, "Bahay ni Lola")
        self.login_as("nanay")
        self.assertEqual(messages_of(self.add(name="Paaralan")), [
            "Naabot mo na ang 1 na sariling board. Magbura muna ng isa para makapagdagdag ng bago.",
        ])

    def test_another_familys_child_page_is_not_hers(self):
        self.login_as("tatay")
        self.assertEqual(self.add().status_code, 404)
        self.assertFalse(GuardianBoard.objects.exists())


class EditBoardTest(GuardianBoardsBase):
    def test_renaming_takes_its_tiles_switches_and_counts_along(self):
        board = self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        HiddenBoard.objects.create(child=self.child, board="Bahay ni Lola")
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Bahay ni Lola")

        self.login_as("nanay")
        response = self.edit(board, name="Bahay nina Lola at Lolo", emoji="🏠")
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang board na “Bahay nina Lola at Lolo”."])

        board.refresh_from_db()
        self.assertEqual((board.name, board.emoji), ("Bahay nina Lola at Lolo", "🏠"))
        self.assertEqual(GuardianWord.objects.get().board, "Bahay nina Lola at Lolo")
        self.assertEqual(HiddenBoard.objects.get().board, "Bahay nina Lola at Lolo")
        self.assertEqual(DailyUsage.objects.get(kind=DailyUsage.BOARD).name, "Bahay nina Lola at Lolo")
        # The creation date stays.
        self.assertEqual(GuardianBoard.objects.get().created_at, board.created_at)

    def test_the_picture_changes_between_emoji_and_upload(self):
        board = self.make_board(self.nanay, "Paaralan", emoji="🏫")
        self.login_as("nanay")

        self.edit(board, icon_kind="image", icon_image=image_upload())
        board.refresh_from_db()
        first = board.icon_image.name
        self.assertTrue(board.has_icon_image)
        self.assertEqual(board.emoji, "")

        # Saving without a new picture keeps it; a new one replaces it.
        self.edit(board, name="Paaralan ni Miguel")
        board.refresh_from_db()
        self.assertEqual((board.name, board.icon_image.name), ("Paaralan ni Miguel", first))
        self.edit(board, icon_image=image_upload("bago.png"))
        board.refresh_from_db()
        self.assertNotEqual(board.icon_image.name, first)
        self.assertFalse(default_storage.exists(first))

        # Back to an emoji removes the picture.
        second = board.icon_image.name
        self.edit(board, icon_kind="emoji", emoji="🎒")
        board.refresh_from_db()
        self.assertEqual((board.emoji, board.has_icon_image), ("🎒", False))
        self.assertFalse(default_storage.exists(second))

    def test_a_form_that_is_not_valid_reopens_its_own_window(self):
        board = self.make_board(self.nanay, "Bahay ni Lola")
        other = self.make_board(self.nanay, "Paaralan")
        self.login_as("nanay")
        response = self.edit(board, name="Paaralan")
        self.assertContains(response, "May board na may ganitong pangalan.")
        self.assertContains(response, f'data-modal="edit-board-{board.uuid}" data-open="true"')
        self.assertContains(response, f'data-modal="edit-board-{other.uuid}" data-open="false"')
        board.refresh_from_db()
        self.assertEqual(board.name, "Bahay ni Lola")

    def test_another_familys_board_is_not_hers_to_change(self):
        tatays = self.make_board(self.tatay, "Kubo")
        self.login_as("nanay")
        response = self.client.post(self.url, {"edit_board_form": str(tatays.uuid), f"board-{tatays.pk}-name": "Akin na"})
        self.assertEqual(response.status_code, 404)
        tatays.refresh_from_db()
        self.assertEqual(tatays.name, "Kubo")


class DeleteBoardTest(GuardianBoardsBase):
    def test_deleting_says_what_becomes_of_its_tiles_and_takes_them_along(self):
        board = self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena", "duyan"])
        board.set_icon_image("icon.png", ContentFile(image_bytes()), "image/png")
        icon = board.icon_image.name
        GuardianWord.objects.create(guardian=self.nanay, board="Tao", word="Kuya Jun", emoji="👦")
        HiddenBoard.objects.create(child=self.child, board="Bahay ni Lola")
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Bahay ni Lola")
        WordUsage.record_use(self.miguel, "duyan")
        other = self.make_board(self.tatay, "Bahay ni Lola")  # another family's, untouched

        self.login_as("nanay")
        self.assertContains(self.client.get(self.url), "Mabubura rin ang 2 tile nito, kasama ang boses nila.")

        delete_url = reverse("remove_own_board", args=[self.child.uuid, board.uuid])
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Nabura na ang board na “Bahay ni Lola” at ang mga tile nito."])
        self.assertEqual(list(GuardianBoard.objects.all()), [other])
        self.assertEqual(list(GuardianWord.objects.values_list("word", flat=True)), ["Kuya Jun"])
        self.assertFalse(HiddenBoard.objects.exists())
        self.assertFalse(DailyUsage.objects.filter(kind=DailyUsage.BOARD).exists())
        self.assertFalse(WordUsage.objects.filter(word="duyan").exists())
        self.assertFalse(default_storage.exists(icon))

    def test_only_her_own_board_from_her_own_childs_page(self):
        tatays = self.make_board(self.tatay, "Kubo")
        self.login_as("nanay")
        self.assertEqual(self.client.post(reverse("remove_own_board", args=[self.child.uuid, tatays.uuid])).status_code, 404)
        self.assertTrue(GuardianBoard.objects.filter(pk=tatays.pk).exists())

    def test_deleting_the_guardian_deletes_her_boards_pictures(self):
        guardian = make_guardian("tito", "Tito Ben")
        board = self.make_board(guardian, "Kubo")
        board.set_icon_image("icon.png", ContentFile(image_bytes()), "image/png")
        icon = board.icon_image.name
        delete_user_account(guardian.user)
        self.assertFalse(default_storage.exists(icon))


class GuardianBoardsOnTheBoardsTest(GuardianBoardsBase):
    def test_a_board_with_a_tile_shows_after_the_apps_on_every_board_of_the_family(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena", "duyan"])
        self.make_board(self.nanay, "Paaralan")  # no tile yet: nothing to show on a board

        self.login_as("nanay")
        for boards in [self.boards_on("board"), self.boards_on("child_board", self.child.uuid)]:
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
        hidden = response.context["rows"][-1]
        self.assertEqual((hidden["board"]["name"], hidden["switch"]), ("Paaralan", None))
        self.assertContains(response, "Nakatago muna sa mga board ang 1 sa mga sariling board mo")
        words = {row["word"].word: row["shown"] for row in self.client.get(reverse("guardian_words")).context["words"]}
        self.assertEqual(words, {"Lola Nena": True, "guro": False})

    def test_her_board_is_turned_on_and_off_for_each_child_and_one_stays_on(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])

        self.login_as("nanay")
        shown = [name for name in board_names() if name != "Tao"]
        self.assertRedirects(self.client.post(self.url, {"boards_form": "", "boards": shown}), self.url)
        self.assertEqual(set(self.child.hidden_boards.values_list("board", flat=True)), {"Tao", "Bahay ni Lola"})
        self.assertContains(self.client.post(self.url, {"boards_form": "", "boards": []}),
                            "Kailangang may kahit isang board na naka-on para sa bata.")

        self.login_as("miguel")
        self.assertNotIn("Bahay ni Lola", self.boards_on())

    def test_saving_the_switches_keeps_a_hidden_boards_own_switch(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        self.make_board(self.nanay, "Paaralan", tiles=["guro"])
        HiddenBoard.objects.create(child=self.child, board="Paaralan")
        self.set_limits(plus_board_limit=1)

        self.login_as("nanay")
        self.client.post(self.url, {"boards_form": "", "boards": [*board_names(), "Bahay ni Lola"]})
        self.assertEqual(list(self.child.hidden_boards.values_list("board", flat=True)), ["Paaralan"])

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
        boards = self.client.get(reverse("child_usage", args=[self.child.uuid])).context["boards"]
        self.assertEqual([(row["name"], row["icon"]) for row in boards], [("Bahay ni Lola", "🏡")])

    def test_when_plus_ends_her_boards_are_hidden_and_come_back_on_renewal(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        Payment.objects.filter(guardian=self.nanay).update(ends_at=timezone.now() - timedelta(days=1))
        self.login_as("miguel")
        self.assertNotIn("Bahay ni Lola", self.boards_on())
        self.assertTrue(GuardianBoard.objects.filter(name="Bahay ni Lola").exists())

        approve_payment(make_payment(self.nanay), self.developer)
        self.assertIn("Bahay ni Lola", self.boards_on())


class AdminStatsTest(GuardianBoardsBase):
    def test_a_familys_own_boards_and_tiles_are_not_in_the_admins_numbers(self):
        self.make_board(self.nanay, "Bahay ni Lola", tiles=["Lola Nena"])
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Bahay ni Lola")
        DailyUsage.record(self.miguel, DailyUsage.BOARD, "Tao")
        WordUsage.record_use(self.miguel, "Lola Nena")
        WordUsage.record_use(self.miguel, "ako")

        self.assertEqual([row["name"] for row in admin_stats.board_opens()], ["Tao"])
        self.assertEqual([row["word"] for row in analytics.top_words()], ["ako"])
