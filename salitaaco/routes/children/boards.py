"""
A child's Mga Board: which boards the child sees, and the guardian's own boards
(custom boards), which the guardian adds, changes and deletes here.

The app's boards are SalitAACo's: a guardian only turns them on and off. A
guardian's own board is shared by all of their children, each of whom it can
be turned off for; its tiles are added on Sariling Tile. How many own boards a
guardian can have depends on their plan (utils/guardian_boards.py).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.children.child_boards import ChildBoardsForm
from salitaaco.forms.guardian_words.guardian_board import IMAGE, GuardianBoardForm
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.guardian_boards import (
    board_data,
    board_limit,
    delete_guardian_board,
    family_boards,
    rename_guardian_board,
    shown_guardian_boards,
)
from salitaaco.utils.guardian_words import limit_reached_message, on_free_plan
from salitaaco.utils.perms_check import is_app_user, is_guardian, multi_user_test
from salitaaco.utils.uploads import ICON_MAX_SIDE, random_upload_name, shrink_picture

PREVIEW_TILES = 4
NEW_BOARD = "new-board"


def edit_prefix(board):
    """The fields of each own board's form are named after it, so that every board's form can be on the page."""
    return f"board-{board.pk}"


def save_icon(board, form):
    """
    Give a board the picture its form chose: an uploaded one, made small
    enough to keep (utils/uploads.py), or an emoji in place of an uploaded one.
    """
    if form.cleaned_data["icon_kind"] == IMAGE:
        image = form.cleaned_data["icon_image"]
        if image:
            content, mime = shrink_picture(image, ICON_MAX_SIDE)
            board.set_icon_image(random_upload_name(mime), content, mime)
    else:
        board.remove_icon_image(save=False)
        board.emoji = form.cleaned_data["emoji"]
        board.save()


def icon_kind_of(board):
    return IMAGE if board.has_icon_image else "emoji"


@active_nav("child_boards")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def manage_child_boards(request, child_uuid):
    child = guardian_child_or_404(request, child_uuid)
    guardian = child.guardian
    own_boards = list(guardian.boards.all())

    # The boards with a switch: the app's, and the guardian's own that their plan's limit shows, tiles or not.
    family = family_boards(guardian, include_empty=True)
    names = [board["name"] for board in family]
    hidden = set(child.hidden_boards.values_list("board", flat=True))

    boards_form = ChildBoardsForm(initial={"boards": [name for name in names if name not in hidden]}, names=names)
    new_board_form = GuardianBoardForm(prefix=NEW_BOARD, guardian=guardian)
    edit_forms = {
        board.pk: GuardianBoardForm(
            prefix=edit_prefix(board), guardian=guardian, editing=board,
            initial={"name": board.name, "emoji": board.emoji, "icon_kind": icon_kind_of(board)},
        )
        for board in own_boards
    }
    open_modal = None

    limit = board_limit(guardian)
    on_free = on_free_plan(guardian)
    plus_limit = SiteSetting.load().plus_board_limit
    can_add = len(own_boards) < limit
    limit_message = limit_reached_message("board", limit, on_free, plus_limit)

    if request.method == "POST":
        if "restore_boards_form" in request.POST:
            child.hidden_boards.all().delete()
            messages.success(request, f"Naka-on na muli ang lahat ng board ni {child.display_name}.")
            return redirect('child_boards', child_uuid=child.uuid)

        if "boards_form" in request.POST:
            boards_form = ChildBoardsForm(request.POST, names=names)
            if boards_form.is_valid():
                shown = set(boards_form.cleaned_data['boards'])
                with transaction.atomic():
                    # The switches of boards not on the page (an own board over the limit) are kept as they are.
                    child.hidden_boards.filter(board__in=names).delete()
                    HiddenBoard.objects.bulk_create([
                        HiddenBoard(child=child, board=name) for name in names if name not in shown
                    ])
                messages.success(request, f"Naka-save na ang mga board ni {child.display_name}.")
                return redirect('child_boards', child_uuid=child.uuid)

        if "new_board_form" in request.POST:
            if not can_add:
                messages.error(request, limit_message)
                return redirect('child_boards', child_uuid=child.uuid)
            new_board_form = GuardianBoardForm(request.POST, request.FILES, prefix=NEW_BOARD, guardian=guardian)
            if new_board_form.is_valid():
                board = GuardianBoard.objects.create(guardian=guardian, name=new_board_form.cleaned_data["name"])
                save_icon(board, new_board_form)
                messages.success(request, f"Nagawa na ang board na “{board.name}”. Lagyan ito ng tile sa Sariling Tile.")
                return redirect('child_boards', child_uuid=child.uuid)
            open_modal = "new-board"

        if "edit_board_form" in request.POST:
            board = next((board for board in own_boards if str(board.uuid) == request.POST["edit_board_form"]), None)
            if board is None:
                raise Http404()
            form = GuardianBoardForm(request.POST, request.FILES, prefix=edit_prefix(board), guardian=guardian, editing=board)
            edit_forms[board.pk] = form
            if form.is_valid():
                with transaction.atomic():
                    rename_guardian_board(board, form.cleaned_data["name"])
                    save_icon(board, form)
                messages.success(request, f"Naka-save na ang board na “{board.name}”.")
                return redirect('child_boards', child_uuid=child.uuid)
            open_modal = f"edit-board-{board.uuid}"

    own_by_name = {board.name: board for board in own_boards}
    shown_own = {board.pk for board in shown_guardian_boards(guardian)}
    tile_counts = dict(guardian.words.values_list("board").annotate(count=Count("guardian_word_id")).order_by())

    def row(board, switch=None):
        own = own_by_name.get(board["name"])
        return {
            "switch": switch,
            "board": board,
            "own": own,
            "edit_form": edit_forms[own.pk] if own else None,
            # Its form was sent and was not valid: the window reopens to say why.
            "reopen": own is not None and open_modal == f"edit-board-{own.uuid}",
            # Every tile of an own board, shown or not, goes with it when it is deleted.
            "own_tile_count": tile_counts.get(own.name, 0) if own else 0,
            "word_count": len(board["items"]),
            "preview": [item["e"] for item in board["items"][:PREVIEW_TILES]],
        }

    # Each board with its switch, in the order of the form's choices; then the own boards over the limit, without.
    rows = [row(board, switch) for switch, board in zip(boards_form["boards"], family)]
    rows += [row(board_data(board)) for board in own_boards if board.pk not in shown_own]

    context = {
        "child": child,
        "boards_form": boards_form,
        "rows": rows,
        "new_board_form": new_board_form,
        "open_modal": open_modal,
        "own_count": len(own_boards),
        "hidden_count": len(own_boards) - len(shown_own),
        "limit": limit,
        "can_add": can_add,
        "limit_message": limit_message,
        "offer_plus": on_free and plus_limit > limit,
    }
    return render(request, 'dashboard/children/boards.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_own_board(request, child_uuid, board_uuid):
    """A guardian deletes one of their own boards, shown or not, with the tiles on it."""
    child = guardian_child_or_404(request, child_uuid)
    board = get_object_or_404(GuardianBoard.objects.select_related("guardian"), uuid=board_uuid, guardian=child.guardian)
    name = board.name
    delete_guardian_board(board)
    messages.success(request, f"Nabura na ang board na “{name}” at ang mga tile nito.")
    return redirect('child_boards', child_uuid=child.uuid)


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_guardian_board_icon(request, board_uuid):
    """A guardian's board's uploaded picture, for the guardian and for the guardian's children."""
    allowed = GuardianBoard.objects.filter(
        Q(guardian__user=request.user) | Q(guardian__children__user=request.user)
    ).distinct()
    board = get_object_or_404(allowed, uuid=board_uuid)
    if not board.has_icon_image:
        raise Http404()
    response = FileResponse(board.icon_image.open('rb'), content_type=board.icon_mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response
