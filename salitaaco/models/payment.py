from django.db import models
import uuid

from salitaaco.defaults.plans import APPROVED, PAYMENT_STATUSES, PENDING, REJECTED


class Payment(models.Model):
    """
    A guardian's payment for a plan: the picture of the GCash payment they
    uploaded, which an admin approves or rejects on the Kita page. An approved
    payment keeps the guardian on the plan from `starts_at` to `ends_at`, so a
    guardian's plan is found from their payments; there is no other record of it.
    """
    payment_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='payments')
    # Plans are never deleted, so a payment always has its plan.
    plan = models.ForeignKey('Plan', on_delete=models.PROTECT, related_name='payments')
    # The plan's price when the guardian paid; a later change of price leaves it as it was.
    amount = models.PositiveIntegerField()
    proof = models.ImageField(upload_to='payment-proofs/')
    proof_mime = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUSES, default=PENDING)
    # Why the admin rejected it, which the guardian sees.
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Who approved or rejected it, and when. The admin is kept as empty if their user goes.
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    # The time on the plan this payment bought; empty until it is approved.
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at", "-payment_id"]

    @property
    def is_pending(self):
        return self.status == PENDING

    @property
    def is_approved(self):
        return self.status == APPROVED

    @property
    def is_rejected(self):
        return self.status == REJECTED

    def __str__(self):
        return f"{self.guardian}: ₱{self.amount} ({self.status})"
