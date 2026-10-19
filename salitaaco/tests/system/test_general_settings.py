from django.contrib.messages import get_messages
from django.core.files.storage import default_storage
from django.urls import reverse

from salitaaco.forms.system.general_settings import GeneralSettingsForm
from salitaaco.models.site_setting import SiteSetting
from salitaaco.tests.users_base import UserBase, image_upload, make_guardian


def messages_of(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class SystemBase(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa", children=[cls.miguel])
        cls.url = reverse("system_general")


class SiteSettingTest(SystemBase):
    def test_there_is_one_row_made_on_first_use(self):
        self.assertFalse(SiteSetting.objects.exists())
        setting = SiteSetting.load()
        self.assertEqual((setting.contact_email, setting.maintenance_mode), ("", False))

        setting.contact_email = "tulong@halimbawa.ph"
        setting.save()
        SiteSetting(contact_phone="0917").save()  # saving another is saving the same one

        self.assertEqual(SiteSetting.objects.count(), 1)
        self.assertEqual(SiteSetting.load().contact_phone, "0917")

    def test_form(self):
        self.assertTrue(GeneralSettingsForm({}).is_valid())
        self.assertEqual(GeneralSettingsForm({"contact_email": "hindi-email"}).errors["contact_email"], ["Hindi tama ang email address."])
        self.assertEqual(
            GeneralSettingsForm({"maintenance_message": "a" * 301}).errors["maintenance_message"],
            ["Masyadong mahaba ang mensahe (hanggang 300 character)."],
        )


class GeneralSettingsPageTest(SystemBase):
    def test_only_admins_open_and_save(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
            self.assertEqual(self.client.post(self.url, {"maintenance_mode": "on"}).status_code, 302)
        self.assertFalse(SiteSetting.load().maintenance_mode)

    def test_saving_the_contact_details_shows_them_to_guardians(self):
        self.login_as("developer")
        response = self.client.post(self.url, {"contact_email": "tulong@halimbawa.ph", "contact_phone": "0917 000 0000"})
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang mga setting."])
        self.assertContains(self.client.get(self.url), 'value="tulong@halimbawa.ph"')

        self.login_as("nanay")
        response = self.client.get(reverse("support"))
        self.assertContains(response, 'href="mailto:tulong@halimbawa.ph"')
        self.assertContains(response, "0917 000 0000")

    def test_the_support_page_says_nothing_about_contact_details_that_are_not_set(self):
        self.login_as("nanay")
        self.assertNotContains(self.client.get(reverse("support")), "Maaari ka ring makipag-ugnayan")

    def test_maintenance_mode_is_a_switch(self):
        self.login_as("developer")
        response = self.client.get(self.url)
        self.assertContains(response, '<label class="switch">', count=1)
        self.assertContains(response, 'type="checkbox" name="maintenance_mode"')

    def test_a_form_that_is_not_valid_saves_nothing(self):
        self.login_as("developer")
        response = self.client.post(self.url, {"contact_email": "hindi-email", "maintenance_mode": "on"})
        self.assertContains(response, "Hindi tama ang email address.")
        self.assertFalse(SiteSetting.load().maintenance_mode)


class GcashSettingsTest(SystemBase):
    def send(self, **data):
        return self.client.post(self.url, {"payment_form": "", **data})

    def test_uploading_the_qr_code_and_the_account(self):
        self.login_as("developer")
        self.assertContains(self.client.get(self.url), "Wala pang QR code. Hindi pa makakabayad ang mga tagapag-alaga.")

        response = self.send(gcash_qr=image_upload(), gcash_name="Juan D.", gcash_number="0917 000 0000")
        self.assertRedirects(response, self.url)
        self.assertEqual(messages_of(response), ["Naka-save na ang bayaran sa GCash."])
        setting = SiteSetting.load()
        self.assertTrue(setting.gcash_qr.name.startswith("payment-qr/"))
        self.assertEqual((setting.gcash_qr_mime, setting.gcash_name, setting.gcash_number),
                         ("image/png", "Juan D.", "0917 000 0000"))
        self.assertContains(self.client.get(self.url), f'class="qrPreview" src="{reverse("view_gcash_qr")}?v=')

    def test_saving_without_a_new_picture_keeps_the_old_one_and_a_new_one_replaces_it(self):
        self.login_as("developer")
        self.send(gcash_qr=image_upload())
        first = SiteSetting.load().gcash_qr.name

        self.send(gcash_name="Bagong Pangalan")
        setting = SiteSetting.load()
        self.assertEqual((setting.gcash_qr.name, setting.gcash_name), (first, "Bagong Pangalan"))

        self.send(gcash_qr=image_upload("bago.png"))
        self.assertNotEqual(SiteSetting.load().gcash_qr.name, first)
        self.assertFalse(default_storage.exists(first))

    def test_removing_the_qr_code(self):
        self.login_as("developer")
        self.send(gcash_qr=image_upload())
        name = SiteSetting.load().gcash_qr.name

        response = self.client.post(self.url, {"remove_gcash_qr": ""})
        self.assertRedirects(response, self.url)
        self.assertFalse(SiteSetting.load().has_gcash_qr)
        self.assertFalse(default_storage.exists(name))

    def test_what_is_not_valid_saves_nothing(self):
        self.login_as("developer")
        response = self.send(gcash_qr=image_upload("qr.gif", "GIF", "image/gif"), gcash_number="tawagan mo ako")
        self.assertContains(response, "JPEG, PNG o WebP lang ang puwedeng larawan.")
        self.assertContains(response, "Mga numero lang ang puwede sa GCash number.")
        self.assertFalse(SiteSetting.load().has_gcash_qr)

    def test_saving_the_qr_code_leaves_the_other_settings_alone(self):
        setting = SiteSetting.load()
        setting.contact_email = "tulong@halimbawa.ph"
        setting.save()

        self.login_as("developer")
        self.send(gcash_qr=image_upload())
        self.assertEqual(SiteSetting.load().contact_email, "tulong@halimbawa.ph")

    def test_only_admins_set_it(self):
        self.login_as("nanay")
        self.assertEqual(self.send(gcash_qr=image_upload()).status_code, 302)
        self.assertEqual(self.client.post(self.url, {"remove_gcash_qr": ""}).status_code, 302)
        self.assertFalse(SiteSetting.load().has_gcash_qr)


class MaintenanceModeTest(SystemBase):
    def turn_on(self, message=""):
        setting = SiteSetting.load()
        setting.maintenance_mode = True
        setting.maintenance_message = message
        setting.save()

    def test_off_by_default(self):
        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("board")).status_code, 200)

    def test_everyone_but_admins_gets_the_maintenance_page(self):
        self.turn_on("Babalik kami mamayang 6:00 ng gabi.")

        for username in ["miguel", "nanay"]:
            self.login_as(username)
            for route in ["board", "profile", "settings"]:
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 503, f"{username} {route}")
                self.assertEqual(response["Retry-After"], "3600")
            self.assertContains(response, "Inaayos namin ang app", status_code=503)
            self.assertContains(response, "Babalik kami mamayang 6:00 ng gabi.", status_code=503)
            # The board's background requests are closed as well.
            self.assertEqual(self.client.post(reverse("increment_word_usage"), {"word": "kain"}).status_code, 503)

        self.login_as("developer")
        for route in ["analytics", "board", "system_general"]:
            self.assertEqual(self.client.get(reverse(route)).status_code, 200, route)

    def test_logging_in_stays_open_so_that_an_admin_can_turn_it_off(self):
        self.turn_on()
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        # Someone not logged in sees the maintenance page too, not a redirect to the app.
        self.assertContains(self.client.get(reverse("register")), "Babalik ito sa lalong madaling panahon.", status_code=503)

        response = self.client.post(reverse("login"), {"username": "developer", "password": "dev-password"})
        self.assertRedirects(response, reverse("analytics"))
        self.assertContains(self.client.get(self.url), "Naka-on ang maintenance mode.")

        response = self.client.post(self.url, {})  # the switch left off
        self.assertRedirects(response, self.url)
        self.assertFalse(SiteSetting.load().maintenance_mode)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)

        self.login_as("miguel")
        self.assertEqual(self.client.get(reverse("board")).status_code, 200)

    def test_someone_logged_in_to_another_account_can_get_to_the_login_form(self):
        # The login page sends whoever is logged in to their own first page, which
        # during maintenance is the maintenance page: without a way to log out
        # from there, an admin logged in as a guardian would be stuck.
        self.turn_on()
        self.login_as("nanay")
        self.assertRedirects(self.client.get(reverse("login")), reverse("overview"), target_status_code=503)

        page = self.client.get(reverse("overview"))
        self.assertContains(page, f'<form class="authAlt" method="post" action="{reverse("logout")}">', status_code=503)
        self.assertContains(page, 'name="csrfmiddlewaretoken"', status_code=503)
        self.assertContains(page, "Mag-log out at mag-log in bilang admin", status_code=503)
        self.assertNotContains(page, f'<a href="{reverse("login")}">', status_code=503)

        # Logging out leads to the login form, and from there an admin gets in.
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, "Mag-log in")
        response = self.client.post(reverse("login"), {"username": "developer", "password": "dev-password"})
        self.assertRedirects(response, reverse("analytics"))

    def test_someone_not_logged_in_is_offered_the_login_form(self):
        self.turn_on()
        page = self.client.get(reverse("register"))
        self.assertContains(page, f'<a href="{reverse("login")}">Mag-log in</a>', status_code=503)
        self.assertNotContains(page, 'method="post"', status_code=503)

    def test_the_maintenance_page_is_not_logged_as_an_error(self):
        self.turn_on()
        self.login_as("miguel")
        with self.assertNoLogs("django.request", level="ERROR"):
            self.assertEqual(self.client.get(reverse("board")).status_code, 503)

    def test_an_admin_turns_it_on_from_the_page(self):
        self.login_as("developer")
        self.client.post(self.url, {"maintenance_mode": "on", "maintenance_message": "Sandali lang."})
        setting = SiteSetting.load()
        self.assertEqual((setting.maintenance_mode, setting.maintenance_message), (True, "Sandali lang."))

        self.login_as("miguel")
        self.assertContains(self.client.get(reverse("board")), "Sandali lang.", status_code=503)
