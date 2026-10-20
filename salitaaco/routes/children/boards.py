from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from salitaaco.forms.children.child_boards import ChildBoardsForm
from salitaaco.models.hidden_board import HiddenBoard
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.children import guardian_child_or_404
from salitaaco.utils.guardian_boards import child_boards, family_boards
from salitaaco.utils.perms_check import is_guardian, multi_user_test

PREVIEW_TILES = 4


@active_nav("child_boards")
@login_required(login_url='/login/')
@multi_user_test(is_guardian)
def manage_child_boards(request, child_uuid):
    """
    Which boards a child sees: the app's, and the guardian's own (Sariling
    Board). The guardian turns each on and off for each child.
    """
    child = guardian_child_or_404(request, child_uuid)
    family = family_boards(child.guardian)
    names = [board["name"] for board in family]

    boards_form = ChildBoardsForm(initial={"boards": [board["name"] for board in child_boards(child)]}, names=names)

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
                    child.hidden_boards.all().delete()
                    HiddenBoard.objects.bulk_create([
                        HiddenBoard(child=child, board=name) for name in names if name not in shown
                    ])
                messages.success(request, f"Naka-save na ang mga board ni {child.display_name}.")
                return redirect('child_boards', child_uuid=child.uuid)

    own_names = set(child.guardian.boards.values_list("name", flat=True))
    # Each board with its switch, in the order of the form's choices.
    rows = [
        {
            "switch": switch,
            "board": board,
            "is_own": board["name"] in own_names,
            "word_count": len(board["items"]),
            "preview": [item["e"] for item in board["items"][:PREVIEW_TILES]],
        }
        for switch, board in zip(boards_form["boards"], family)
    ]

    context = {
        "child": child,
        "boards_form": boards_form,
        "rows": rows,
    }
    return render(request, 'dashboard/children/boards.html', context)
