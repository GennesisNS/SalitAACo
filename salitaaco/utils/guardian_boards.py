from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_word import GuardianWord
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.board import all_boards
from salitaaco.utils.guardian_words import (
    add_guardian_words,
    delete_guardian_word,
    family_users,
    on_free_plan,
    shown_guardian_words,
)
from salitaaco.utils.uploads import icon_image_url


def board_limit(guardian):
    """How many boards of their own the guardian's plan allows."""
    setting = SiteSetting.load()
    return setting.free_board_limit if on_free_plan(guardian) else setting.plus_board_limit


def shown_guardian_boards(guardian):
    """
    The guardian's boards that the boards show: the oldest ones, up to their
    plan's limit. The others are kept, hidden, until the limit allows them again.
    """
    if guardian is None:
        return []
    return list(guardian.boards.all()[:board_limit(guardian)])


def board_icon_url(board):
    """Where a guardian's board's uploaded picture is, or None when its picture is an emoji."""
    return icon_image_url("guardian_board_icon", board)


def board_data(board):
    """A guardian's board as the board pages describe boards, with its picture's address when it has one."""
    return {"name": board.name, "icon": board.emoji, "icon_url": board_icon_url(board), "items": []}


def family_boards(guardian, include_empty=False):
    """
    Every board a guardian's family sees: the app's published boards, then the
    guardian's own shown boards, each with the guardian's shown tiles at its
    end. A board of the guardian's shows once it has a tile, since until then
    there is nothing on it to tap; `include_empty` keeps the ones without, for
    the page where the guardian sets them up.
    """
    categories = all_boards()
    if guardian is None:
        return categories

    own = [board_data(board) for board in shown_guardian_boards(guardian)]
    own_names = {board["name"] for board in own}
    filled = add_guardian_words(categories + own, shown_guardian_words(guardian))
    if include_empty:
        return filled
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


def rename_guardian_board(board, name):
    """
    Give a guardian's board another name. Its tiles, the switches that turned
    it off for the children and the counts of its openings find it by name, so
    they take the new one too.
    """
    old = board.name
    if name == old:
        return
    guardian = board.guardian
    GuardianWord.objects.filter(guardian=guardian, board=old).update(board=name)
    HiddenBoard.objects.filter(child__guardian=guardian, board=old).update(board=name)
    DailyUsage.objects.filter(user__in=family_users(guardian), kind=DailyUsage.BOARD, name=old).update(name=name)
    board.name = name
    board.save()


def delete_guardian_board(board):
    """
    Delete a guardian's board with its picture, its tiles (and their pictures
    and audio), the switches that turned it off for the children, and the
    counts of its openings.
    """
    guardian = board.guardian
    for word in guardian.words.filter(board=board.name):
        delete_guardian_word(word)
    HiddenBoard.objects.filter(child__guardian=guardian, board=board.name).delete()
    DailyUsage.objects.filter(user__in=family_users(guardian), kind=DailyUsage.BOARD, name=board.name).delete()
    board.remove_icon_image(save=False)
    board.delete()
