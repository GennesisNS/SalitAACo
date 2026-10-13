import tempfile
from pathlib import Path

from django.test import override_settings
from django.urls import reverse

from salitaaco.models.site_setting import SiteSetting
from salitaaco.routes.technical_status.technical_status import recent_errors, unapplied_migrations
from salitaaco.tests.users_base import UserBase, make_guardian


class TechnicalStatusTest(UserBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nanay = make_guardian("nanay", "Nanay Rosa")
        cls.url = reverse("system_status")

    def checks(self, response):
        return {check["name"]: check for check in response.context["checks"]}

    def test_only_admins_open_the_page(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")
        for username in ["miguel", "nanay"]:
            self.login_as(username)
            self.assertEqual(self.client.get(self.url).status_code, 302, username)
        self.login_as("developer")
        self.assertEqual(self.client.get(self.url).status_code, 200)

    @override_settings(DEBUG=False, ELEVENLABS_API_KEY="susi")
    def test_what_is_in_order_is_shown_as_such(self):
        self.login_as("developer")
        checks = self.checks(self.client.get(self.url))

        self.assertEqual(unapplied_migrations(), 0)
        for name in ["Database", "Mga migration", "Debug mode", "Maintenance mode", "ElevenLabs (boses ng pamilya)"]:
            self.assertTrue(checks[name]["ok"], name)
        self.assertEqual(checks["Mga migration"]["detail"], "Naka-apply na lahat")

    @override_settings(DEBUG=True, ELEVENLABS_API_KEY="")
    def test_what_needs_looking_at_is_counted_and_explained(self):
        setting = SiteSetting.load()
        setting.maintenance_mode = True
        setting.save()
        self.login_as("developer")

        response = self.client.get(self.url)
        checks = self.checks(response)

        for name in ["Debug mode", "Maintenance mode", "ElevenLabs (boses ng pamilya)"]:
            self.assertFalse(checks[name]["ok"], name)
        self.assertGreaterEqual(response.context["problem_count"], 3)
        self.assertContains(response, "hindi makakagawa ng boses ng pamilya")
        self.assertContains(response, '<span class="statusBadge pending">Tingnan</span>')

    def test_the_last_errors_of_the_log_newest_first(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "salitaaco.log"
            log.write_text(
                "2026-10-12 10:00:00 INFO salitaaco: maayos\n"
                "2026-10-12 10:01:00 ERROR salitaaco: una\n"
                "2026-10-12 10:02:00 WARNING salitaaco: babala\n"
                "2026-10-12 10:03:00 ERROR salitaaco: pangalawa\n",
                encoding="utf-8",
            )
            with override_settings(LOG_FILE=log):
                self.assertEqual([line.rsplit(": ", 1)[1] for line in recent_errors()], ["pangalawa", "una"])
                self.assertEqual(len(recent_errors(limit=1)), 1)

                self.login_as("developer")
                response = self.client.get(self.url)
                self.assertContains(response, "ERROR salitaaco: pangalawa")
                self.assertNotContains(response, "babala")

            with override_settings(LOG_FILE=Path(folder) / "walang-ganito.log"):
                self.assertEqual(recent_errors(), [])
                self.assertContains(self.client.get(self.url), "Walang error sa dulo ng log.")
