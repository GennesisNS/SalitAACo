from pathlib import Path
from unittest import mock

from django.apps import apps
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import resolve, reverse

from salitaaco.defaults.plans import PLANS
from salitaaco.models.site_setting import SiteSetting
from salitaaco.tests.users_base import UserBase, make_guardian

PUBLIC_FOLDER = Path(apps.get_app_config("public").path)


class PublicHomeTest(TestCase):
    def test_the_sites_root_is_the_public_page(self):
        self.assertEqual(reverse("index"), "/")
        self.assertEqual(resolve("/").func.__module__, "public.views")

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/home.html")
        self.assertContains(response, '<html lang="tl">')

    def test_page_has_the_hero_about_us_the_plans_and_the_footer(self):
        response = self.client.get("/")

        for piece in ['<section class="hero"', 'id="about"', 'id="plans"', '<footer class="siteFooter">']:
            self.assertContains(response, piece, count=1)
        self.assertContains(response, "Tungkol sa Amin")
        self.assertContains(response, "Mga Plano")
        # What the name is made of, from the business draft.
        for part in ["<dt>salita</dt>", "<dt>AAC</dt>", "<dt>-o</dt>"]:
            self.assertContains(response, part)

    def test_get_started_leads_to_sign_up(self):
        response = self.client.get("/")
        self.assertContains(response, f'<a class="btn cta" href="{reverse("register")}">Magsimula</a>')
        self.assertContains(response, f'href="{reverse("login")}"')

    def test_the_plans_are_the_plan_data_not_words_in_the_page(self):
        response = self.client.get("/")
        self.assertEqual([plan["name"] for plan in response.context["plans"]], ["Free", "SalitAACo Plus"])
        for text in ["₱0", "₱149", "habambuhay", "kada buwan", "Boses ng pamilya (family voice banking)"]:
            self.assertContains(response, text)

        # Change the data, and the page changes with it.
        changed = [
            {**PLANS[0], "offered": False},
            {**PLANS[1], "name": "SalitAACo Pamilya", "price": 199, "features": ["Lahat ng nasa Free", "Bagong kasama"]},
        ]
        with mock.patch("salitaaco.utils.plans.PLANS", changed):
            response = self.client.get("/")
        self.assertEqual([plan["name"] for plan in response.context["plans"]], ["SalitAACo Pamilya"])
        self.assertContains(response, "₱199")
        self.assertContains(response, "Bagong kasama")
        for gone in ["₱149", "₱0", "SalitAACo Plus", "habambuhay"]:
            self.assertNotContains(response, gone)

    def test_with_no_plan_offered_the_page_says_so(self):
        with mock.patch("salitaaco.utils.plans.PLANS", []):
            response = self.client.get("/")
        self.assertContains(response, "Inaayos pa ang mga plano.")

    def test_the_footer_shows_the_contact_details_an_admin_set(self):
        self.assertNotContains(self.client.get("/"), "Makipag-ugnayan")

        setting = SiteSetting.load()
        setting.contact_email = "tulong@halimbawa.ph"
        setting.contact_phone = "0917 000 0000"
        setting.save()

        response = self.client.get("/")
        self.assertContains(response, 'href="mailto:tulong@halimbawa.ph"')
        self.assertContains(response, "0917 000 0000")


class PublicAppStandsByItselfTest(TestCase):
    def test_its_templates_styles_and_script_are_in_its_own_folder(self):
        for name in ["public/css/public.css", "public/js/public.js"]:
            found = finders.find(name)
            self.assertIsNotNone(found, name)
            self.assertTrue(Path(found).is_relative_to(PUBLIC_FOLDER), name)
        self.assertTrue((PUBLIC_FOLDER / "templates" / "public" / "home.html").is_file())

    def test_the_page_loads_nothing_from_the_apps_own_static_files(self):
        response = self.client.get("/")
        self.assertContains(response, "public/css/public.css")
        self.assertContains(response, "public/js/public.js")
        for other in ["css/tokens.css", "css/base.css", "css/dashboard.css", "css/child.css", "js/main.js"]:
            self.assertNotContains(response, other)

    def test_the_stylesheet_uses_only_colours_it_names_itself(self):
        css = (PUBLIC_FOLDER / "static" / "public" / "css" / "public.css").read_text(encoding="utf-8")
        used = {part.split(")")[0].split(",")[0].strip() for part in css.split("var(")[1:]}
        for name in used:
            self.assertIn(f"{name}:", css, name)


class LoggedInVisitorsTest(UserBase):
    def test_someone_logged_in_goes_to_their_own_first_page(self):
        make_guardian("nanay", "Nanay Rosa")
        for username, route in [("miguel", "board"), ("nanay", "overview"), ("developer", "analytics")]:
            self.login_as(username)
            self.assertRedirects(self.client.get("/"), reverse(route), msg_prefix=username)

    def test_the_page_is_closed_with_the_app_during_maintenance(self):
        setting = SiteSetting.load()
        setting.maintenance_mode = True
        setting.save()
        self.assertContains(self.client.get("/"), "Inaayos namin ang app", status_code=503)
