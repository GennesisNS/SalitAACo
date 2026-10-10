from django.contrib.messages import get_messages
from django.urls import reverse

from salitaaco.forms.settings.tile_size import TileSizeForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.tests.users_base import UserBase, make_guardian
from salitaaco.utils.account import find_user_account


class TileSizeFormTest(UserBase):
    def test_the_three_sizes_are_valid(self):
        for size in ["small", "medium", "large"]:
            form = TileSizeForm({"tile_size": size})
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data["tile_size"], size)

    def test_missing_or_unknown_size_is_rejected(self):
        for size in ["", "huge"]:
            form = TileSizeForm({"tile_size": size})
            self.assertFalse(form.is_valid(), size)
            self.assertEqual(form.errors["tile_size"], ["Pumili ng laki ng tile."])


class TileSizeSettingTest(UserBase):
    def test_new_accounts_start_at_medium(self):
        self.login_as("miguel")
        self.assertEqual(ChildAccount.objects.get(user=self.miguel).tile_size, "medium")

        settings_page = self.client.get(reverse("settings"))
        self.assertEqual(settings_page.context["tile_size_form"]["tile_size"].value(), "medium")
        self.assertContains(settings_page, 'class="grid tiles-medium" id="tileDemoGrid"')
        self.assertContains(self.client.get(reverse("board")), 'class="grid tiles-medium" id="grid"')

    def test_every_kind_of_account_can_change_its_tile_size(self):
        make_guardian("nanay", "Nanay Rosa")
        for username, size in [("miguel", "large"), ("nanay", "small"), ("developer", "large")]:
            user = self.login_as(username)
            response = self.client.post(reverse("settings"), {"tile_size_form": "", "tile_size": size})

            self.assertRedirects(response, reverse("settings"))
            self.assertEqual(
                [str(message) for message in get_messages(response.wsgi_request)], ["Naka-save na ang laki ng tile."],
            )
            self.assertEqual(find_user_account(user).tile_size, size)
            # The demo on the settings page and the real board are both drawn at the saved size.
            self.assertContains(self.client.get(reverse("settings")), f'class="grid tiles-{size}" id="tileDemoGrid"')
            self.assertContains(self.client.get(reverse("board")), f'class="grid tiles-{size}" id="grid"')

    def test_one_accounts_size_does_not_change_anothers(self):
        self.login_as("miguel")
        self.client.post(reverse("settings"), {"tile_size_form": "", "tile_size": "large"})
        self.assertEqual(ChildAccount.objects.get(user=self.ana).tile_size, "medium")

    def test_unknown_size_shows_the_error_and_saves_nothing(self):
        self.login_as("miguel")
        response = self.client.post(reverse("settings"), {"tile_size_form": "", "tile_size": "huge"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pumili ng laki ng tile.")
        self.assertEqual(ChildAccount.objects.get(user=self.miguel).tile_size, "medium")

    def test_guardian_sees_a_childs_board_at_the_childs_size(self):
        guardian = make_guardian("nanay", "Nanay Rosa", children=[self.miguel])
        ChildAccount.objects.filter(user=self.miguel).update(tile_size="large")
        guardian.tile_size = "small"
        guardian.save()
        self.login_as("nanay")

        child_board = reverse("child_board", args=[ChildAccount.objects.get(user=self.miguel).uuid])
        self.assertContains(self.client.get(child_board), 'class="grid tiles-large" id="grid"')
        self.assertContains(self.client.get(reverse("board")), 'class="grid tiles-small" id="grid"')
