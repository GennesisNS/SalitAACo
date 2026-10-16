import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.vocabulary.set_board_status import SetBoardStatusForm
from salitaaco.models.board_status import BoardStatus
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.board import every_board
from salitaaco.utils.perms_check import is_administrator, multi_user_test

logger = logging.getLogger(__name__)


@active_nav("admin_boards")
@login_required(login_url='/login/')
@multi_user_test(is_administrator)
def view_admin_boards(request):
    """Every board with its status. The boards are the app's own; an admin publishes or hides them."""
    opens = dict(
        DailyUsage.objects.filter(kind=DailyUsage.BOARD).values_list("name").annotate(total=Sum("use_count"))
    )
    changed = {status.board: status.updated_at for status in BoardStatus.objects.all()}

    boards = [
        {
            **board,
            "word_count": len(board["items"]),
            "opens": opens.get(board["name"], 0),
            "updated_at": changed.get(board["name"]),
        }
        for board in every_board()
    ]

    context = {
        "boards": boards,
        "published_count": sum(1 for board in boards if board["is_published"]),
    }
    return render(request, 'dashboard/vocabulary/boards.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_administrator)
@require_POST
def set_board_status(request):
    status_form = SetBoardStatusForm(request.POST)

    if status_form.is_valid():
        board = status_form.cleaned_data['board']
        published = status_form.cleaned_data['published']
        BoardStatus.objects.update_or_create(board=board, defaults={"is_published": published})
        logger.info("Admin %s %s the board %s", request.user.username, "published" if published else "hid", board)
        if published:
            messages.success(request, f"Naka-publish na ang board na “{board}”.")
        else:
            messages.success(request, f"Nakatago na sa lahat ang board na “{board}”.")
    else:
        errors = status_form.non_field_errors() or status_form.errors["board"]
        messages.error(request, errors[0])

    return redirect('admin_boards')
