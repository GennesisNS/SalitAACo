from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.board import all_boards
from salitaaco.utils.guardian_words import (
    add_guardian_words,
    delete_guardian_word_audio,
    delete_word_usage,
    on_free_plan,
    shown_guardian_words,
)


def board_limit(guardian):
    """How many boards of their own the guardian's plan allows."""
    setting = SiteSetting.load()
    return setting.free_board_limit if on_free_plan(guardian) else setting.plus_board_limit


def can_add_board(guardian):
    return guardian.boards.count() < board_limit(guardian)


def shown_guardian_boards(guardian):
    """
    The guardian's boards that the boards show: the oldest ones, up to their
    plan's limit. The others are kept, hidden, until the limit allows them again.
    """
    if guardian is None:
        return []
    return list(guardian.boards.all()[:board_limit(guardian)])


def family_boards(guardian):
    """
    Every board a guardian's family sees: the app's published boards, then the
    guardian's own shown boards, each with the guardian's shown tiles at its
    end. A board of the guardian's shows once it has a tile; until then there
    is nothing on it to tap.
    """
    categories = all_boards()
    if guardian is None:
        return categories

    own = [{"name": board.name, "icon": board.emoji, "items": []} for board in shown_guardian_boards(guardian)]
    own_names = {board["name"] for board in own}
    filled = add_guardian_words(categories + own, shown_guardian_words(guardian))
    return [board for board in filled if board["name"] not in own_names or board["items"]]


def child_boards(child):
    """
    The boards a child sees: their family's, without the ones their guardian
    turned off. A child is never left without a board, whatever the rows say.
    """
    family = family_boards(child.guardian)
    hidden = {hidden_board.board for hidden_board in child.hidden_boards.all()}
    shown = [board for board in family if board["name"] not in hidden]
    return shown or family


def board_guardian(owner, owner_child):
    """
    The guardian whose own boards and tiles a board shows: a child's guardian
    on the child's board, the guardian themself on their own. None for an
    admin's board or a child without a guardian.
    """
    if owner_child is not None:
        return owner_child.guardian
    return GuardianAccount.objects.filter(user=owner).first()


def boards_of(owner, owner_child):
    """The boards a board page shows: a child's own, or a guardian's or an admin's family's."""
    if owner_child is not None:
        return child_boards(owner_child)
    return family_boards(board_guardian(owner, owner_child))


def delete_guardian_board(board):
    """
    Delete a guardian's board with its tiles (and their audio), the switches
    that turned it off for the children, and the counts of its openings.
    """
    guardian = board.guardian
    for word in guardian.words.filter(board=board.name):
        text = word.word
        word.delete()
        delete_guardian_word_audio(guardian, text)
        delete_word_usage(guardian, text)
    HiddenBoard.objects.filter(child__guardian=guardian, board=board.name).delete()
    users = [guardian.user_id, *guardian.children.values_list("user_id", flat=True)]
    DailyUsage.objects.filter(user__in=users, kind=DailyUsage.BOARD, name=board.name).delete()
    board.delete()
