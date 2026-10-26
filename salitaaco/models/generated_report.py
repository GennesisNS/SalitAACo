from django.db import models
from django.utils import timezone
import uuid

from salitaaco.defaults.reports import FILE_TYPES, REPORT_CODES, REPORT_ID_PREFIX, REPORT_TYPES


class GeneratedReport(models.Model):
    """
    A report an admin made on Mga Ulat: what it is about, the days it covers,
    and the file it was made as (a CSV, or a page to print or save as PDF),
    kept as it was when it was made. Like every upload, the file is served
    only by a login-protected view, to admins.
    """
    generated_report_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to='reports/')
    # The admin who made it; kept as empty if their account goes.
    generated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-generated_report_id"]

    @property
    def report_id(self):
        """
        The ID the report shows and is known by, e.g. RPT-USR-20261026-0007:
        the code of its kind, the day it was made, and its number. It is
        known once the report is saved.
        """
        made = timezone.localtime(self.created_at)
        return f"{REPORT_ID_PREFIX}-{REPORT_CODES[self.report_type]}-{made:%Y%m%d}-{self.generated_report_id:04d}"

    def delete_file(self):
        if self.file:
            self.file.delete(save=False)

    def __str__(self):
        return f"{self.report_id} ({self.start_date} – {self.end_date})"
