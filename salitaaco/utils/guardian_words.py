from django.conf import settings

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.family_voice import elevenlabs_client, elevenlabs_is_set_up, family_voice_directory
from salitaaco.utils.plans import current_plan
from salitaaco.utils.tile_audio import tile_audio_file_name, tile_audio_path, tile_word_slug, tile_words


def guardian_word_limit():
    """How many tiles of their own a guardian on a paid plan can have, across all the boards."""
    return SiteSetting.load().guardian_word_limit


def can_add_words(guardian):
    """Only a guardian on a paid plan adds tiles."""
    return not current_plan(guardian).is_free


def board_guardian(owner, owner_child):
    """
    The guardian whose own tiles a board shows: a child's guardian on the
    child's board, the guardian themself on their own. None for an admin's
    board or a child without a guardian.
    """
    if owner_child is not None:
        return owner_child.guardian
    return GuardianAccount.objects.filter(user=owner).first()


def shown_guardian_words(guardian):
    """The guardian's tiles that boards show: all of them on a paid plan, none otherwise."""
    if guardian is None or not can_add_words(guardian):
        return []
    return list(guardian.words.all())


def voice_guardian_word(word):
    """
    Voice a guardian's tile with ElevenLabs, as the vocabulary's tiles are: in
    the shared voice (ELEVENLABS_VOICE_ID), saved with their audio in static/,
    and in each of the guardian's family voices. Audio already made is not made
    again. Returns False when ElevenLabs refused any of it; until it is made,
    the tile speaks in the device's voice.
    """
    if not elevenlabs_is_set_up():
        return True

    # (the ElevenLabs voice, where its audio of the word goes)
    targets = []
    if settings.ELEVENLABS_VOICE_ID:
        targets.append((settings.ELEVENLABS_VOICE_ID, tile_audio_path(word.word)))
    for voice in word.guardian.family_voices.all():
        targets.append((voice.elevenlabs_voice_id, family_voice_directory(voice) / tile_audio_file_name(word.word)))

    client = elevenlabs_client()
    all_made = True
    for voice_id, path in targets:
        if path.exists():
            continue
        try:
            audio = client.text_to_speech(voice_id, word.word)
        except ElevenLabsError:
            # Already logged; the rest is still tried.
            all_made = False
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
    return all_made


def delete_guardian_word_audio(guardian, text):
    """
    Remove the audio of a tile a guardian deleted: the guardian's family
    voices' and, when no other guardian's tile says the word, the shared
    voice's. Audio of a word the vocabulary has (an admin may have added it
    since) belongs to the vocabulary and stays.
    """
    slug = tile_word_slug(text)
    if slug in {tile_word_slug(word) for word in tile_words()}:
        return
    for voice in guardian.family_voices.all():
        (family_voice_directory(voice) / tile_audio_file_name(text)).unlink(missing_ok=True)
    delete_shared_audio_if_unused(text)


def delete_shared_audio_if_unused(text):
    """Remove the shared voice's audio of a guardian's tile once no guardian's tile says the word."""
    slug = tile_word_slug(text)
    if slug in {tile_word_slug(word) for word in tile_words()}:
        return
    if not any(tile_word_slug(other) == slug for other in GuardianWord.objects.values_list("word", flat=True)):
        tile_audio_path(text).unlink(missing_ok=True)


def add_guardian_words(categories, words):
    """
    The boards with a guardian's tiles (`words`, from shown_guardian_words)
    after each board's own words. A tile the boards already have (an admin may
    add the same word later) is left out, so that no two tiles say the same thing.
    """
    if not words:
        return categories

    taken = {tile_word_slug(word) for word in tile_words()}
    added = {}
    for word in words:
        if tile_word_slug(word.word) not in taken:
            added.setdefault(word.board, []).append({"w": word.word, "e": word.emoji})
    return [
        {**category, "items": category["items"] + added.get(category["name"], [])}
        for category in categories
    ]
