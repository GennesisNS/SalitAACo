from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse

from salitaaco.tests.users_base import UserBase, make_guardian

CHILD_LAYOUT = "layouts/child.html"
DASHBOARD_LAYOUT = "layouts/dashboard.html"

CSS = Path(settings.BASE_DIR) / "static" / "css"


def templates_of(response):
    return [template.name for template in response.templates]


class LayoutBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])


class LayoutPerRoleTest(LayoutBase):
    def test_a_childs_pages_use_the_child_layout_and_palette(self):
        self.login_as("miguel")
        for route in ["board", "profile", "settings"]:
            response = self.client.get(reverse(route))
            self.assertIn(CHILD_LAYOUT, templates_of(response), route)
            self.assertNotIn(DASHBOARD_LAYOUT, templates_of(response), route)
            self.assertContains(response, '<html lang="tl" data-palette="ocean">')
            self.assertContains(response, 'class="bottomNav"')
            self.assertNotContains(response, 'id="sidebar"')

    def test_a_guardians_and_an_admins_pages_use_the_dashboard_layout_and_palette(self):
        pages = {
            "nanay": [
                "overview", "children", "family_voices", "guardian_boards", "guardian_words", "plan", "plan_transactions", "support",
                "profile", "settings",
            ],
            "developer": [
                "analytics", "reports", "users", "admin_boards", "words", "institutions", "revenue", "subscriptions",
                "feedback", "system_general", "system_plans", "system_access", "system_privacy", "profile", "settings",
            ],
        }
        for username, routes in pages.items():
            self.login_as(username)
            for route in routes:
                response = self.client.get(reverse(route))
                self.assertIn(DASHBOARD_LAYOUT, templates_of(response), route)
                self.assertNotIn(CHILD_LAYOUT, templates_of(response), route)
                self.assertContains(response, '<html lang="tl" data-palette="navy">')
                self.assertContains(response, 'id="sidebar"')
                self.assertNotContains(response, 'class="bottomNav"')

    def test_the_board_is_in_the_child_layout_for_everyone(self):
        homes = {"nanay": "overview", "developer": "analytics"}
        for username, home in homes.items():
            self.login_as(username)
            response = self.client.get(reverse("board"))
            self.assertIn(CHILD_LAYOUT, templates_of(response))
            # Where a child has their name, they have the way back to their dashboard.
            self.assertContains(response, f'<a class="kidBack" href="{reverse(home)}">')
            self.assertNotContains(response, 'class="accountLink"')

        self.login_as("miguel")
        self.assertNotContains(self.client.get(reverse("board")), 'class="kidBack"')

    def test_a_guardian_sees_a_childs_board_in_the_child_layout(self):
        self.login_as("nanay")
        child = self.nanay.children.get()
        response = self.client.get(reverse("child_board", args=[child.uuid]))
        self.assertIn(CHILD_LAYOUT, templates_of(response))
        self.assertContains(response, f'<a class="kidBack" href="{reverse("overview")}">')

    def test_login_and_error_pages_use_the_navy_palette(self):
        for response in [self.client.get(reverse("login")), self.client.get(reverse("register"))]:
            self.assertContains(response, '<html lang="tl" data-palette="navy">')
        self.assertContains(self.client.get("/walang-ganito/"), 'data-palette="navy"', status_code=404)


class NavigationPerRoleTest(LayoutBase):
    def navigation(self, route):
        return [
            item["id"]
            for category in self.client.get(reverse(route)).context["navigation_items"]
            for item in category["items"]
        ]

    def test_each_role_gets_its_own_navigation(self):
        self.login_as("miguel")
        self.assertEqual(self.navigation("board"), ["home", "boards", "favorites", "profile"])
        self.login_as("nanay")
        self.assertEqual(self.navigation("children"), [
            "overview", "children", "family_voices", "guardian_boards", "guardian_words",
            "child_boards", "child_voice", "child_usage",
            "board", "plan", "support", "settings", "profile",
        ])
        self.login_as("developer")
        self.assertEqual(self.navigation("analytics"), [
            "analytics", "reports", "users", "admin_boards", "words", "institutions",
            "revenue", "subscriptions", "feedback",
            "system_general", "system_plans", "system_access", "system_privacy",
            "board", "settings", "profile",
        ])

    def test_the_technical_status_page_is_gone(self):
        # It showed developers' details (server paths, API errors, voice IDs), not an admin's work.
        self.login_as("developer")
        self.assertEqual(self.client.get("/dashboard/system/status/").status_code, 404)
        with self.assertRaises(NoReverseMatch):
            reverse("system_status")

    def test_a_child_logs_out_from_the_profile_page(self):
        # The sidebar holds the log out button; the child layout has no sidebar.
        self.login_as("miguel")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, f'action="{reverse("logout")}"', count=1)
        self.assertContains(response, "Mag-log out")

        self.login_as("nanay")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, f'action="{reverse("logout")}"', count=1)
        self.assertNotContains(response, "Mag-log out")


class SharedPiecesTest(LayoutBase):
    def test_the_dark_theme_toggle_is_a_switch(self):
        self.login_as("nanay")
        response = self.client.get(reverse("settings"))
        self.assertContains(
            response,
            '<label class="switch">'
            '<input type="checkbox" id="darkToggle" aria-label="Madilim na tema" />'
            '<span class="slider"></span>'
            '</label>',
            html=True,
        )

    def test_the_tile_demo_is_drawn_in_the_childs_palette_for_a_guardian(self):
        self.login_as("nanay")
        self.assertContains(self.client.get(reverse("settings")), '<div class="tileDemo" data-palette="ocean">')

    def test_pages_load_the_shared_stylesheets_and_their_layouts_own(self):
        self.login_as("miguel")
        response = self.client.get(reverse("board"))
        for name in ["tokens.css", "base.css", "child.css"]:
            self.assertContains(response, f"css/{name}")
        self.assertNotContains(response, "css/dashboard.css")

        self.login_as("nanay")
        response = self.client.get(reverse("children"))
        for name in ["tokens.css", "base.css", "dashboard.css"]:
            self.assertContains(response, f"css/{name}")
        self.assertNotContains(response, "css/child.css")


class PaletteTest(SimpleTestCase):
    """The stylesheets themselves: the palettes are complete, and nothing still uses a colour outside them."""

    def read(self, name):
        return (CSS / name).read_text(encoding="utf-8")

    def palette(self, name):
        tokens = self.read("tokens.css")
        block = tokens.split(f'[data-palette="{name}"] {{', 1)[1].split("}", 1)[0]
        return dict(
            (part.strip() for part in line.strip().rstrip(";").split(":", 1))
            for line in block.splitlines()
            if line.strip().startswith("--")
        )

    def test_both_palettes_define_the_same_colours_for_both_themes(self):
        navy, ocean = self.palette("navy"), self.palette("ocean")
        self.assertEqual(sorted(navy), sorted(ocean))
        light = {name[4:] for name in navy if name.startswith("--l-")}
        dark = {name[4:] for name in navy if name.startswith("--d-")}
        self.assertEqual(light, dark)
        self.assertEqual(len(light) + len(dark), len(navy))

    def test_the_palettes_hold_the_colours_that_were_chosen(self):
        navy = set(self.palette("navy").values())
        for colour in ["#0f1e3a", "#1e2f4f", "#a7b4d0", "#ffffff"]:
            self.assertIn(colour, navy)
        ocean = set(self.palette("ocean").values())
        for colour in ["#03045e", "#023eba", "#00b4d8", "#caf0f8", "#fbb02d"]:
            self.assertIn(colour, ocean)

    def test_every_colour_the_pages_use_is_given_a_name(self):
        tokens = self.read("tokens.css")
        for name in ["base.css", "dashboard.css", "child.css"]:
            for used in set(part.split(")")[0].split(",")[0] for part in self.read(name).split("var(")[1:]):
                self.assertIn(f"{used}:", tokens + self.read(name), f"{used} in {name}")

    def test_the_switch_takes_its_on_colour_from_the_palette(self):
        self.assertIn("--color-green: var(--switch-on);", self.read("base.css"))

    def test_the_old_stylesheets_are_gone(self):
        self.assertFalse((CSS / "index.css").exists())
        self.assertFalse((CSS / "admin.css").exists())
