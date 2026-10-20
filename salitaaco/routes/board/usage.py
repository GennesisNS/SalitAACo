from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from salitaaco.forms.board.board_name import BoardNameForm
from salitaaco.forms.board.tile_word import TileWordForm
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.daily_usage import DailyUsage
from salitaaco.models.word_usage import WordUsage
from salitaaco.utils.guardian_boards import boards_of
from salitaaco.utils.perms_check import is_app_user, multi_user_test
from salitaaco.utils.word_usage import DEFAULT_FREQUENT_LIMIT, frequent_words


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
@require_POST
def increment_word_usage(request):
    """Called by the board every time a tile is tapped."""
    tile_word_form = TileWordForm(request.POST)
    if not tile_word_form.is_valid():
        return JsonResponse({"ok": False, "error": "Walang word."}, status=400)

    word = tile_word_form.cleaned_data['word']
    WordUsage.record_use(request.user, word)
    DailyUsage.record(request.user, DailyUsage.WORD, word)
    return JsonResponse({"ok": True})


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
@require_POST
def record_board_open(request):
    """Called by the board every time one of its boards is opened."""
    owner_child = ChildAccount.objects.filter(user=request.user).select_related("guardian").first()
    names = [board["name"] for board in boards_of(request.user, owner_child)]
    board_name_form = BoardNameForm(request.POST, names=names)
    if not board_name_form.is_valid():
        return JsonResponse({"ok": False, "error": "Walang ganitong board."}, status=400)

    DailyUsage.record(request.user, DailyUsage.BOARD, board_name_form.cleaned_data['board'])
    return JsonResponse({"ok": True})


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
@require_GET
def list_frequent_words(request):
    """Called by the board to refresh the Paborito screen after taps."""
    try:
        limit = int(request.GET.get("limit", DEFAULT_FREQUENT_LIMIT))
    except ValueError:
        limit = DEFAULT_FREQUENT_LIMIT

    return JsonResponse({"ok": True, "items": frequent_words(request.user, limit)})
