from django.db import models
import uuid


class Institution(models.Model):
    """
    A school or centre that uses the app under an arrangement made with the
    people who run it. This is the admin's record of that arrangement; it is
    not linked to any account. Belongs to the "Mga Paaralan at Institusyon"
    page (routes/institutions/), which may be removed: nothing else reads this model.
    """
    institution_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_details = models.CharField(max_length=150, blank=True)
    # How many children the arrangement covers.
    seats = models.PositiveIntegerField(default=0)
    # What was agreed: institutional plans are negotiated, not priced on the site.
    plan_notes = models.CharField(max_length=200, blank=True)
    renewal_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
