from django.db import models
import uuid


class SupportMessage(models.Model):
    """
    What a guardian wrote to the people who run the app, on the Tulong at
    Suporta page. It goes when the guardian's account does; when the child it
    was about is deleted, the message stays without them.
    """
    support_message_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='support_messages')
    # The child the problem is about, when the guardian named one.
    child = models.ForeignKey(
        'ChildAccount',
        on_delete=models.SET_NULL,
        related_name='support_messages',
        blank=True,
        null=True,
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # When an admin marked it as dealt with; empty while it is still open.
    resolved_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_resolved(self):
        return self.resolved_at is not None

    def __str__(self):
        return f"{self.guardian}: {self.message[:40]}"
