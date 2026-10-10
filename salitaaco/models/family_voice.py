from django.db import models
import uuid


class FamilyVoice(models.Model):
    """
    A family member's voice (Nanay, Tatay, Lola…), cloned with ElevenLabs from
    a recording their guardian made with the person's consent. The tile words
    are generated in it, and a child whose guardian chose it for them hears it
    on every tile the family has not recorded by hand.

    The recording itself is not kept: it is sent to ElevenLabs once, to clone
    the voice, and only the voice's ID at ElevenLabs is stored here.
    """
    family_voice_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    guardian = models.ForeignKey('GuardianAccount', on_delete=models.CASCADE, related_name='family_voices')
    # Who the voice belongs to, as the family calls them: "Nanay", "Lola Rosa".
    name = models.CharField(max_length=100)
    elevenlabs_voice_id = models.CharField(max_length=100)
    # When the guardian accepted the consent terms, and which version of them.
    consent_at = models.DateTimeField()
    consent_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.guardian})"
