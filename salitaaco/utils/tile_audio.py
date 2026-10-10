from django.conf import settings
from django.templatetags.static import static
from django.utils.text import slugify

from salitaaco.defaults.vocabulary import CATEGORIES

# The shared voice's audio for the tile words, one MP3 per word, under static/.
TILE_AUDIO_FOLDER = "audio/text-to-speech"
VERB_ASPECTS = ["past", "present", "future"]


def tile_words():
    """
    Every word a tile can say, in board order: each tile's word, and for a
    verb all three of its forms (a verb tile shows one of them, never the root).
    """
    words = []
    for category in CATEGORIES:
        for item in category["items"]:
            if "verb" in item:
                words += [item["verb"][aspect] for aspect in VERB_ASPECTS]
            else:
                words.append(item["w"])
    return list(dict.fromkeys(words))


def tile_word_slug(word):
    """'tawagan si Nanay' -> 'tawagan-si-nanay', the name of the word's audio file."""
    return slugify(word)


def tile_audio_file_name(word):
    return f"{tile_word_slug(word)}.mp3"


def tile_audio_directory():
    return settings.BASE_DIR / "static" / TILE_AUDIO_FOLDER


def tile_audio_urls():
    """
    {word: url} for every tile word whose shared-voice audio has been generated.
    The URL changes when a file is generated again, so browsers fetch the new one.
    """
    directory = tile_audio_directory()
    urls = {}
    for word in tile_words():
        file_name = tile_audio_file_name(word)
        path = directory / file_name
        if path.exists():
            urls[word] = f"{static(f'{TILE_AUDIO_FOLDER}/{file_name}')}?v={int(path.stat().st_mtime)}"
    return urls
