from salitaaco.defaults.board import BOARD_ICONS, QUICK_WORDS
from salitaaco.defaults.vocabulary import CATEGORIES


def all_boards():
    """Every board: each category of the vocabulary, with the picture of its tile."""
    return [
        {
            "name": category["name"],
            "icon": BOARD_ICONS.get(category["name"]) or category["items"][0]["e"],
            "items": category["items"],
        }
        for category in CATEGORIES
    ]


def board_names():
    return [category["name"] for category in CATEGORIES]


def hidden_board_names(child):
    """The boards the child's guardian turned off, as the names of boards that still exist."""
    hidden = {hidden_board.board for hidden_board in child.hidden_boards.all()}
    return hidden.intersection(board_names())


def boards(child=None):
    """
    The boards a board page offers. A child's is without the boards their
    guardian turned off; a guardian's or an admin's own board has them all.
    """
    if child is None:
        return all_boards()
    hidden = hidden_board_names(child)
    shown = [board for board in all_boards() if board["name"] not in hidden]
    # A child is never left without a board, whatever the rows say.
    return shown or all_boards()


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
