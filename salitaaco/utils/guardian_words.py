import shutil
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabsError
from salitaaco.models.customization import Customization
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.site_setting import SiteSetting
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils.board import word_tile
from salitaaco.utils.family_voice import elevenlabs_client, elevenlabs_is_set_up, family_voice_directory
from salitaaco.utils.plans import current_plan
from salitaaco.utils.tile_audio import tile_audio_file_name, tile_word_slug, tile_words

# The guardians' tiles in the shared voice, one folder per guardian under
# media/. They are not the app's vocabulary, so they are kept apart from its
# audio in static/, and like every upload they are served only by a
# login-protected view (play_guardian_word).
GUARDIAN_WORD_AUDIO_FOLDER = "guardian-tile-audio"


def on_free_plan(guardian):
    return current_plan(guardian).is_free


def word_limit(guardian):
    """How many tiles of their own the guardian's plan allows, across all of their family's boards."""
    setting = SiteSetting.load()
    return setting.free_word_limit if on_free_plan(guardian) else setting.plus_word_limit


def can_add_word(guardian):
    return guardian.words.count() < word_limit(guardian)


def limit_reached_message(noun, limit, on_free, plus_limit):
    """
    What a guardian is told when they cannot add another tile or board
    (`noun`): to get Plus when it allows more, otherwise to delete one first.
    """
    if on_free and plus_limit > limit:
        if limit == 0:
            return f"Para sa SalitAACo Plus ang sariling {noun}: hanggang {plus_limit}. Kunin ang Plus para makapagdagdag."
        return (f"Hanggang {limit} na sariling {noun} lang sa libreng plano. "
                f"Kunin ang SalitAACo Plus para makapagdagdag ng hanggang {plus_limit}.")
    return f"Naabot mo na ang {limit} na sariling {noun}. Magbura muna ng isa para makapagdagdag ng bago."


def shown_guardian_words(guardian):
    """
    The guardian's tiles that boards show: the oldest ones, up to their plan's
    limit. The others are kept, hidden, until the limit allows them again.
    """
    if guardian is None:
        return []
    return list(guardian.words.all()[:word_limit(guardian)])


def family_users(guardian):
    return [guardian.user_id, *guardian.children.values_list("user_id", flat=True)]


def delete_word_usage(guardian, text):
    """The counts of a word the guardian's family used, once the guardian's tile of it is gone."""
    users = family_users(guardian)
    WordUsage.objects.filter(user__in=users, word=text).delete()
    DailyUsage.objects.filter(user__in=users, kind=DailyUsage.WORD, name=text).delete()


def rename_guardian_word(word, text):
    """
    Give a guardian's tile another word. What the family keeps by the word
    goes with it: the counts of its taps (so the admin's lists, which leave
    the family's own tiles out by their words, never see the old one) and each
    user's own picture and recording of it. Should a user already have either
    for the new word (an admin's word of that name was deleted), theirs stays
    and the old tile's is let go. Its audio is made again apart, see
    revoice_renamed_word.
    """
    old = word.word
    if text == old:
        return
    users = family_users(word.guardian)
    for usage in WordUsage.objects.filter(user__in=users, word=old):
        taken = WordUsage.objects.filter(user_id=usage.user_id, word=text).first()
        if taken is None:
            usage.word = text
            usage.save()
        else:
            taken.use_count += usage.use_count
            taken.save()
            usage.delete()
    for usage in DailyUsage.objects.filter(user__in=users, kind=DailyUsage.WORD, name=old):
        taken = DailyUsage.objects.filter(user_id=usage.user_id, day=usage.day, kind=DailyUsage.WORD, name=text).first()
        if taken is None:
            usage.name = text
            usage.save()
        else:
            taken.use_count += usage.use_count
            taken.save()
            usage.delete()
    for customization in Customization.objects.filter(user__in=users, word=old):
        if Customization.objects.filter(user_id=customization.user_id, word=text).exists():
            customization.reset()
        else:
            customization.word = text
            customization.save()
    word.word = text
    word.save()


def guardian_word_audio_directory(guardian):
    return Path(settings.MEDIA_ROOT) / GUARDIAN_WORD_AUDIO_FOLDER / str(guardian.uuid)


def guardian_word_audio_path(word):
    """Where a guardian's tile in the shared voice is, made or not."""
    return guardian_word_audio_directory(word.guardian) / tile_audio_file_name(word.word)


def guardian_word_audio_urls(words):
    """{word: url} for the guardian's tiles already made in the shared voice."""
    urls = {}
    for word in words:
        path = guardian_word_audio_path(word)
        if path.exists():
            urls[word.word] = f"{reverse('play_guardian_word', args=[word.uuid])}?v={int(path.stat().st_mtime)}"
    return urls


def voice_guardian_word(word):
    """
    Voice a guardian's tile with ElevenLabs, as the vocabulary's tiles are: in
    the shared voice (ELEVENLABS_VOICE_ID), saved in the guardian's own folder,
    and in each of the guardian's family voices. Audio already made is not made
    again. Returns False when ElevenLabs refused any of it; until it is made,
    the tile speaks in the device's voice.
    """
    if not elevenlabs_is_set_up():
        return True

    # (the ElevenLabs voice, where its audio of the word goes)
    targets = []
    if settings.ELEVENLABS_VOICE_ID:
        targets.append((settings.ELEVENLABS_VOICE_ID, guardian_word_audio_path(word)))
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
    Remove the audio of a tile a guardian deleted: in the shared voice, from
    the guardian's folder, and in each of their family voices. A family voice's
    audio of a word the vocabulary has (an admin may have added it since)
    belongs to the vocabulary and stays.
    """
    (guardian_word_audio_directory(guardian) / tile_audio_file_name(text)).unlink(missing_ok=True)
    if tile_word_slug(text) in {tile_word_slug(word) for word in tile_words()}:
        return
    for voice in guardian.family_voices.all():
        (family_voice_directory(voice) / tile_audio_file_name(text)).unlink(missing_ok=True)


def revoice_renamed_word(word, old):
    """
    After a tile's word changed, remove the audio of the old word and voice
    the new one, as a new tile is. The same audio file name (only the letter
    case or the punctuation changed) is kept as it is. Returns False when
    ElevenLabs refused any of it.
    """
    if tile_audio_file_name(old) == tile_audio_file_name(word.word):
        return True
    delete_guardian_word_audio(word.guardian, old)
    return voice_guardian_word(word)


def delete_guardian_word(word):
    """Delete a guardian's tile, shown or not, with its picture, its audio and its counts."""
    guardian, text = word.guardian, word.word
    word.remove_icon_image(save=False)
    word.delete()
    delete_guardian_word_audio(guardian, text)
    delete_word_usage(guardian, text)


def delete_guardian_audio_folder(guardian):
    """Remove all of a guardian's tiles in the shared voice, when their account goes."""
    shutil.rmtree(guardian_word_audio_directory(guardian), ignore_errors=True)


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
            added.setdefault(word.board, []).append(word_tile(word, "guardian_word_image"))
    return [
        {**category, "items": category["items"] + added.get(category["name"], [])}
        for category in categories
    ]
