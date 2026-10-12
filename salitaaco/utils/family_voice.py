import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabs, ElevenLabsError
from salitaaco.defaults.family_voice import PREVIEW_WORD, TERMS_VERSION
from salitaaco.models.family_voice import FamilyVoice
from salitaaco.utils.tile_audio import tile_audio_file_name, tile_word_slug, tile_words

logger = logging.getLogger(__name__)

# The tile words in each family voice, one folder per voice under media/.
# Like every upload they are private, served only by a login-protected view.
FAMILY_VOICE_FOLDER = "family-voices"


def elevenlabs_is_set_up():
    return bool(settings.ELEVENLABS_API_KEY)


def elevenlabs_client():
    return ElevenLabs(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)


def family_voice_directory(voice):
    return Path(settings.MEDIA_ROOT) / FAMILY_VOICE_FOLDER / str(voice.uuid)


def family_voice_progress(voice):
    """(words generated so far, all tile words)"""
    directory = family_voice_directory(voice)
    words = tile_words()
    done = sum(1 for word in words if (directory / tile_audio_file_name(word)).exists())
    return done, len(words)


def create_family_voice(guardian, name, sample):
    """
    Clone a family member's voice from their recording (an uploaded file) and
    save it for the guardian. Raises ElevenLabsError if ElevenLabs refuses; then
    nothing is saved. The recording is sent to ElevenLabs and not kept here.
    """
    sample.seek(0)
    elevenlabs_voice_id = elevenlabs_client().add_voice(
        # The name ElevenLabs shows for the voice. It only needs to be recognisable there.
        name=f"SalitAACo {name} ({guardian.uuid.hex[:8]})",
        sample_name=sample.name,
        sample=sample.read(),
        sample_mime=sample.content_type,
        description="A family member's voice for a child's SalitAACo board, cloned with their consent.",
    )
    voice = FamilyVoice.objects.create(
        guardian=guardian,
        name=name,
        elevenlabs_voice_id=elevenlabs_voice_id,
        consent_at=timezone.now(),
        consent_version=TERMS_VERSION,
    )
    logger.info("Created family voice %s for guardian %s", voice.uuid, guardian.user.username)

    # Children who do not hear a family voice yet hear this one.
    guardian.children.filter(family_voice__isnull=True).update(family_voice=voice)
    return voice


def generate_family_voice_words(voice, limit):
    """
    Generate up to `limit` tile words that the voice does not have yet.
    Returns the progress afterwards. Raises ElevenLabsError if ElevenLabs refuses;
    the words made before that are kept.
    """
    directory = family_voice_directory(voice)
    directory.mkdir(parents=True, exist_ok=True)

    missing = [word for word in tile_words() if not (directory / tile_audio_file_name(word)).exists()]
    if missing:
        client = elevenlabs_client()
        for word in missing[:limit]:
            (directory / tile_audio_file_name(word)).write_bytes(client.text_to_speech(voice.elevenlabs_voice_id, word))

    return family_voice_progress(voice)


def family_voice_preview_url(voice):
    """The voice saying the preview word, or None while that word is not generated yet."""
    if not (family_voice_directory(voice) / tile_audio_file_name(PREVIEW_WORD)).exists():
        return None
    return reverse("play_family_voice_word", args=[voice.uuid, tile_word_slug(PREVIEW_WORD)])


def family_voice_urls(voice):
    """{word: url} for the tile words already generated in the voice."""
    directory = family_voice_directory(voice)
    urls = {}
    for word in tile_words():
        path = directory / tile_audio_file_name(word)
        if path.exists():
            url = reverse("play_family_voice_word", args=[voice.uuid, tile_word_slug(word)])
            urls[word] = f"{url}?v={int(path.stat().st_mtime)}"
    return urls


def delete_family_voice(voice, strict=True):
    """
    Delete the voice at ElevenLabs, then its generated words and its row here.
    With strict, an ElevenLabs refusal stops everything (ElevenLabsError) so the
    voice is not left behind there; without, it is logged and the rest goes ahead.
    A voice ElevenLabs no longer has counts as deleted.
    """
    if elevenlabs_is_set_up():
        try:
            elevenlabs_client().delete_voice(voice.elevenlabs_voice_id)
        except ElevenLabsError as error:
            if error.status_code not in (400, 404):
                if strict:
                    raise
                logger.error("Could not delete ElevenLabs voice %s of family voice %s: %s",
                             voice.elevenlabs_voice_id, voice.uuid, error)
    else:
        logger.error("ELEVENLABS_API_KEY is not set: ElevenLabs voice %s was not deleted there",
                     voice.elevenlabs_voice_id)

    shutil.rmtree(family_voice_directory(voice), ignore_errors=True)
    logger.info("Deleted family voice %s (%s)", voice.uuid, voice.name)
    voice.delete()
