from salitaaco.defaults.board import BOARD_ICONS, QUICK_WORDS
from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.models.added_word import AddedWord
from salitaaco.models.board_status import BoardStatus
from salitaaco.utils.tile_audio import VERB_ASPECTS
from salitaaco.utils.uploads import icon_image_url


def word_tile(word, image_route):
    """
    A word an admin or a guardian added (an AddedWord or a GuardianWord), as
    the boards describe a tile: its word, its emoji and, when its picture was
    uploaded, the address `image_route` serves it at.
    """
    tile = {"w": word.word, "e": word.emoji}
    if word.has_icon_image:
        tile["img"] = icon_image_url(image_route, word)
    return tile


def every_board():
    """
    Every board, published or not: each category of the default vocabulary,
    with the picture of its tile, followed by the words an admin added to it.
    `is_published` says whether anyone but an admin sees it.
    """
    added = {}
    for word in AddedWord.objects.order_by("created_at", "added_word_id"):
        added.setdefault(word.board, []).append(word_tile(word, "added_word_image"))
    unpublished = set(BoardStatus.objects.filter(is_published=False).values_list("board", flat=True))

    return [
        {
            "name": category["name"],
            "icon": BOARD_ICONS.get(category["name"]) or category["items"][0]["e"],
            # A new list each time: the default vocabulary itself is never added to.
            "items": category["items"] + added.get(category["name"], []),
            "is_published": category["name"] not in unpublished,
        }
        for category in CATEGORIES
    ]


def every_board_name():
    return [category["name"] for category in CATEGORIES]


def all_boards():
    """The published boards: the ones a board page can show."""
    return [
        {"name": board["name"], "icon": board["icon"], "items": board["items"]}
        for board in every_board() if board["is_published"]
    ]


def board_names():
    """The names of the published boards."""
    return [board["name"] for board in all_boards()]


def quick_words():
    """The Home screen's quick words as tiles, in the order of QUICK_WORDS. A word the vocabulary lacks is left out."""
    tiles = {item["w"]: item for category in CATEGORIES for item in category["items"]}
    return [tiles[word] for word in QUICK_WORDS if word in tiles]


def board_words(boards):
    """
    Every word a user can tap, or give a picture or a recording, on `boards`
    (as a board page has them): each tile's word, a verb in each of its forms,
    and the Home screen's quick words.
    """
    words = {item["w"] for item in quick_words()}
    for board in boards:
        for item in board["items"]:
            words.add(item["w"])
            if "verb" in item:
                words.update(item["verb"][aspect] for aspect in VERB_ASPECTS)
    return words
