from django.db import models

from salitaaco.defaults.plans import (
    DEFAULT_FREE_BOARD_LIMIT,
    DEFAULT_FREE_WORD_LIMIT,
    DEFAULT_PLUS_BOARD_LIMIT,
    DEFAULT_PLUS_WORD_LIMIT,
)


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
    # Where guardians send the money for a paid plan: the GCash QR code they
    # scan, and the name and number of the account. Shown on Plano at Subscription.
    gcash_qr = models.ImageField(upload_to='payment-qr/', blank=True)
    gcash_qr_mime = models.CharField(max_length=50, blank=True)
    gcash_name = models.CharField(max_length=100, blank=True)
    gcash_number = models.CharField(max_length=20, blank=True)
    # How many tiles and boards of their own a guardian can add on each plan,
    # across all of their family's boards (utils/guardian_words.py).
    free_word_limit = models.PositiveSmallIntegerField(default=DEFAULT_FREE_WORD_LIMIT)
    plus_word_limit = models.PositiveSmallIntegerField(default=DEFAULT_PLUS_WORD_LIMIT)
    free_board_limit = models.PositiveSmallIntegerField(default=DEFAULT_FREE_BOARD_LIMIT)
    plus_board_limit = models.PositiveSmallIntegerField(default=DEFAULT_PLUS_BOARD_LIMIT)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        setting, _ = cls.objects.get_or_create(pk=cls.ONLY_ROW)
        return setting

    def save(self, *args, **kwargs):
        self.pk = self.ONLY_ROW
        super().save(*args, **kwargs)

    @property
    def has_gcash_qr(self):
        return bool(self.gcash_qr)

    def set_gcash_qr(self, file_name, content, mime):
        """Replace the QR code, removing the previous file from storage."""
        self.remove_gcash_qr(save=False)
        self.gcash_qr.save(file_name, content, save=False)
        self.gcash_qr_mime = mime
        self.save()

    def remove_gcash_qr(self, save=True):
        if self.gcash_qr:
            self.gcash_qr.delete(save=False)
        self.gcash_qr_mime = ''
        if save:
            self.save()

    def __str__(self):
        return "Site settings"
