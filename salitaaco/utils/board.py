from salitaaco.defaults.board import BOARD_ICONS, QUICK_WORDS
from salitaaco.defaults.vocabulary import CATEGORIES
from salitaaco.models.added_word import AddedWord
from salitaaco.models.board_status import BoardStatus
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


def hidden_board_names(child):
    """The published boards the child's guardian turned off."""
    hidden = {hidden_board.board for hidden_board in child.hidden_boards.all()}
    return hidden.intersection(board_names())


def boards(child=None):
    """
    The boards a board page offers. A child's is without the boards their
    guardian turned off; a guardian's or an admin's own board has them all.
    """
    published = all_boards()
    if child is None:
        return published
    hidden = {hidden_board.board for hidden_board in child.hidden_boards.all()}
    shown = [board for board in published if board["name"] not in hidden]
    # A child is never left without a board, whatever the rows say.
    return shown or published


def quick_words():
    """The Home screen's quick words as tiles, in the order of QUICK_WORDS. A word the vocabulary lacks is left out."""
    tiles = {item["w"]: item for category in CATEGORIES for item in category["items"]}
    return [tiles[word] for word in QUICK_WORDS if word in tiles]


# Features that add to what the board page receives put a function here: it is
# given the child whose board it is (None on a guardian's or an admin's own
# board) and returns a dict that is merged into the board's data. board.js
# treats everything added this way as optional, so a feature that registers
# here can be deleted without the board noticing.
board_data_sources = []


def extra_board_data(child):
    data = {}
    for source in board_data_sources:
        data.update(source(child))
    return data
