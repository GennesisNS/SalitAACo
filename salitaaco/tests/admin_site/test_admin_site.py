import importlib

from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import clear_url_caches, reverse

from salitaaco import urls
from salitaaco.models.site_setting import SiteSetting
from salitaaco.tests.users_base import UserBase


class AdminSiteTest(UserBase):
    """Every model of the app is in Django's admin site (/admin/, when SHOW_ADMIN_ROUTES is on)."""

    def setUp(self):
        # The URL patterns are built when salitaaco.urls is imported, so it is
        # reloaded with the admin site on, and again once the test is over.
        override = override_settings(SHOW_ADMIN_ROUTES=True)
        override.enable()
        importlib.reload(urls)
        clear_url_caches()

        def restore():
            override.disable()
            importlib.reload(urls)
            clear_url_caches()

        self.addCleanup(restore)
        User.objects.filter(pk=self.developer.pk).update(is_staff=True, is_superuser=True)
        self.login_as("developer")

    def models(self):
        return list(apps.get_app_config("salitaaco").get_models())

    def test_every_model_is_registered(self):
        missing = [model.__name__ for model in self.models() if not admin.site.is_registered(model)]
        self.assertEqual(missing, [])

    def test_every_models_list_opens_and_is_on_the_admin_index(self):
        SiteSetting.load()
        index = self.client.get(reverse("admin:index"))
        for model in self.models():
            name = model._meta.model_name
            with self.subTest(model=name):
                self.assertEqual(self.client.get(reverse(f"admin:salitaaco_{name}_changelist")).status_code, 200)
                self.assertContains(index, reverse(f"admin:salitaaco_{name}_changelist"))

    def test_the_site_settings_are_one_row_that_is_never_added_to_or_deleted(self):
        setting = SiteSetting.load()
        self.assertEqual(self.client.get(reverse("admin:salitaaco_sitesetting_add")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:salitaaco_sitesetting_delete", args=[setting.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:salitaaco_sitesetting_change", args=[setting.pk])).status_code, 200)
