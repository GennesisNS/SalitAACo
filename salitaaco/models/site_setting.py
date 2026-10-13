from django.db import models


class SiteSetting(models.Model):
    """
    The settings of the whole site, which an admin edits on System Settings >
    General. There is one row; `SiteSetting.load()` returns it, creating it
    with the defaults the first time.
    """
    ONLY_ROW = 1

    site_setting_id = models.AutoField(primary_key=True)
    # How guardians can reach the people who run the app. Shown on Tulong at Suporta.
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    # While on, everyone but admins sees the maintenance page instead of the app.
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        setting, _ = cls.objects.get_or_create(pk=cls.ONLY_ROW)
        return setting

    def save(self, *args, **kwargs):
        self.pk = self.ONLY_ROW
        super().save(*args, **kwargs)

    def __str__(self):
        return "Site settings"
