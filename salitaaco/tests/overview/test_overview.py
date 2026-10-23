from django.urls import reverse

from salitaaco.models.child_account import ChildAccount
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.word_usage import WordUsage
from salitaaco.tests.payments_base import make_payment
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.plans import approve_payment


class GuardianBase(UserBase):
    """Nanay is the guardian of Miguel and Ana. Tatay is a guardian of nobody."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel, cls.ana])
        cls.tatay = make_guardian("tatay", "Tatay Ben")
        cls.miguel_account = ChildAccount.objects.get(user=cls.miguel)
        cls.ana_account = ChildAccount.objects.get(user=cls.ana)


class OverviewTest(GuardianBase):
    def test_only_guardians_open_the_overview(self):
        url = reverse("overview")
        self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        for username in ["miguel", "developer"]:
            self.login_as(username)
            self.assertEqual(self.client.get(url).status_code, 302, username)
        self.login_as("nanay")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_children_are_a_table_with_their_numbers(self):
        WordUsage.objects.create(user=self.miguel, word="kain", use_count=5)
        WordUsage.objects.create(user=self.miguel, word="inom", use_count=2)
        HiddenBoard.objects.create(child=self.ana_account, board="Lugar")
        HiddenBoard.objects.create(child=self.ana_account, board="Bagay")
        self.login_as("nanay")

        response = self.client.get(reverse("overview"))

        children = response.context["children"]
        self.assertEqual(
            [(child.display_name, child.total_taps, child.shown_boards, child.total_boards) for child in children],
            [("Ana", 0, 4, 6), ("Miguel", 7, 6, 6)],
        )
        self.assertEqual(
            [(card["label"], card["value"]) for card in response.context["stat_cards"]],
            [("Mga bata", 2), ("Mga board na naka-on", 10), ("Kabuuang pindot", 7), ("Boses ng pamilya", 0)],
        )
        # A table, with a row and its two actions for each child.
        self.assertContains(response, "<table>")
        self.assertContains(response, "4 sa 6 naka-on")
        for child in [self.miguel_account, self.ana_account]:
            self.assertContains(response, f'href="{reverse("child_board", args=[child.uuid])}"')
            self.assertContains(response, f'href="{reverse("manage_child", args=[child.uuid])}"')

    def test_a_guardian_sees_only_their_own_children(self):
        self.login_as("tatay")
        response = self.client.get(reverse("overview"))
        self.assertEqual(response.context["children"], [])
        self.assertContains(response, "Wala ka pang naidadagdag na bata.")
        self.assertNotContains(response, "<table>")
        self.assertNotContains(response, "Miguel")

    def test_add_a_child_leads_to_the_form_already_open(self):
        # On Plus, Nanay's two children leave room for a third.
        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("nanay")
        add_url = f'{reverse("children")}?add=1'
        self.assertContains(self.client.get(reverse("overview")), f'href="{add_url}"')

        self.assertContains(self.client.get(add_url), 'data-modal="create-child" data-open="true"')
        self.assertContains(self.client.get(reverse("children")), 'data-modal="create-child" data-open="false"')


class ChildrenPageTest(GuardianBase):
    def test_children_are_a_table_and_the_form_is_a_modal(self):
        approve_payment(make_payment(self.nanay), self.developer)
        self.login_as("nanay")
        response = self.client.get(reverse("children"))

        self.assertContains(response, "<table>")
        self.assertEqual([child.shown_boards for child in response.context["children"]], [6, 6])
        self.assertContains(response, 'role="dialog" aria-modal="true" aria-labelledby="createChildTitle"')
        self.assertContains(response, 'name="create_child_form"')


class SelectedChildTest(GuardianBase):
    """The sidebar's child pages lead to the child whose page was opened last."""

    def child_urls(self, response):
        return {
            item["id"]: item["url"]
            for category in response.context["navigation_items"]
            for item in category["items"]
            if item.get("child")
        }

    def test_the_first_child_is_selected_until_another_ones_page_is_opened(self):
        self.login_as("nanay")
        response = self.client.get(reverse("overview"))
        self.assertEqual(response.context["selected_child"], self.ana_account)
        self.assertEqual(self.child_urls(response), {
            "child_boards": reverse("child_boards", args=[self.ana_account.uuid]),
            "child_voice": reverse("child_voice", args=[self.ana_account.uuid]),
            "child_usage": reverse("child_usage", args=[self.ana_account.uuid]),
        })

        self.client.get(reverse("child_usage", args=[self.miguel_account.uuid]))

        response = self.client.get(reverse("overview"))
        self.assertEqual(response.context["selected_child"], self.miguel_account)
        self.assertEqual(self.child_urls(response)["child_boards"], reverse("child_boards", args=[self.miguel_account.uuid]))

    def test_the_picker_opens_the_same_page_for_another_child(self):
        self.login_as("nanay")
        response = self.client.get(reverse("child_voice", args=[self.miguel_account.uuid]))
        self.assertEqual(
            [(option["child"].display_name, option["url"], option["selected"]) for option in response.context["child_picker"]],
            [
                ("Ana", reverse("child_voice", args=[self.ana_account.uuid]), False),
                ("Miguel", reverse("child_voice", args=[self.miguel_account.uuid]), True),
            ],
        )
        self.assertContains(response, '<select class="childPicker" id="childPicker" aria-label="Napiling bata">')

        # From a page that is not about a child, it opens the child's boards.
        response = self.client.get(reverse("overview"))
        self.assertEqual(
            [option["url"] for option in response.context["child_picker"]],
            [reverse("child_boards", args=[child.uuid]) for child in [self.ana_account, self.miguel_account]],
        )

    def test_the_picker_falls_back_to_the_boards_on_other_addresses_with_a_child_in_them(self):
        self.login_as("nanay")
        for url in [
            reverse("child_board", args=[self.miguel_account.uuid]),
            reverse("view_child_avatar", args=[self.miguel_account.uuid]),  # 404: no picture
        ]:
            response = self.client.get(url)
            self.assertEqual(
                [option["url"] for option in response.context["child_picker"]],
                [reverse("child_boards", args=[child.uuid]) for child in [self.ana_account, self.miguel_account]],
            )

    def test_a_guardian_without_children_has_no_child_pages(self):
        self.login_as("tatay")
        response = self.client.get(reverse("overview"))
        self.assertIsNone(response.context["selected_child"])
        self.assertEqual(self.child_urls(response), {})
        self.assertNotContains(response, 'id="childPicker"')
        self.assertNotContains(response, "Napiling Bata")

    def test_a_deleted_childs_selection_falls_back_to_the_first_child(self):
        self.login_as("nanay")
        self.client.get(reverse("child_usage", args=[self.miguel_account.uuid]))
        self.miguel.delete()
        self.assertEqual(self.client.get(reverse("overview")).context["selected_child"], self.ana_account)

    def test_the_other_roles_have_no_children_in_their_pages(self):
        for username in ["miguel", "developer"]:
            self.login_as(username)
            response = self.client.get(reverse("settings"))
            self.assertIsNone(response.context["selected_child"])
            self.assertEqual(response.context["child_picker"], [])
