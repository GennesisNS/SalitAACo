"""
The "Sariling Board" page: boards a guardian makes for their family, after the
app's boards. The guardian fills them with their own tiles on Sariling Tile,
and a board shows, once it has one, on the guardian's own board and on every
one of their children's, where it is turned on and off as any other board.
How many a guardian can have depends on their plan, as an admin sets it on
System Settings > General; over it, the oldest up to it show and the rest are
kept, hidden.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.guardian_words.guardian_board import GuardianBoardForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.models.guardian_board import GuardianBoard
from salitaaco.models.site_setting import SiteSetting
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.guardian_boards import board_limit, delete_guardian_board, shown_guardian_boards
from salitaaco.utils.guardian_words import limit_reached_message, on_free_plan
from salitaaco.utils.perms_check import is_guardian, multi_user_test


@active_nav("guardian_boards")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def view_guardian_boards(request):
    guardian = get_object_or_404(GuardianAccount, user=request.user)
    boards = list(guardian.boards.all())
    limit = board_limit(guardian)
    on_free = on_free_plan(guardian)
    plus_limit = SiteSetting.load().plus_board_limit
    can_add = len(boards) < limit
    limit_message = limit_reached_message("board", limit, on_free, plus_limit)

    board_form = GuardianBoardForm(guardian=guardian)

    if request.method == "POST":
        if not can_add:
            messages.error(request, limit_message)
            return redirect('guardian_boards')

        board_form = GuardianBoardForm(request.POST, guardian=guardian)
        if board_form.is_valid():
            board = GuardianBoard.objects.create(
                guardian=guardian,
                name=board_form.cleaned_data['name'],
                emoji=board_form.cleaned_data['emoji'],
            )
            messages.success(request, f"Nagawa na ang board na “{board.name}”. Lagyan ito ng tile sa Sariling Tile.")
            return redirect('guardian_boards')

    shown = {board.pk for board in shown_guardian_boards(guardian)}
    tile_counts = dict(guardian.words.values_list("board").annotate(count=Count("guardian_word_id")).order_by())
    rows = [
        {"board": board, "shown": board.pk in shown, "tile_count": tile_counts.get(board.name, 0)}
        for board in boards
    ]

    context = {
        "boards": rows,
        "board_count": len(boards),
        "hidden_count": sum(1 for row in rows if not row["shown"]),
        "limit": limit,
        "can_add": can_add,
        "limit_message": limit_message,
        "offer_plus": on_free and plus_limit > limit,
        "board_form": board_form,
    }
    return render(request, 'dashboard/guardian_boards/guardian_boards.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_guardian)
@require_POST
def remove_guardian_board(request, board_uuid):
    """A guardian deletes one of their boards, shown or not, with the tiles on it."""
    board = get_object_or_404(GuardianBoard.objects.select_related("guardian"), uuid=board_uuid, guardian__user=request.user)
    name = board.name
    delete_guardian_board(board)
    messages.success(request, f"Nabura na ang board na “{name}” at ang mga tile nito.")
    return redirect('guardian_boards')
