from django.db.models import IntegerField, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.urls import reverse

from salitaaco.defaults.navigations import dashboard_items
from salitaaco.models.child_account import ChildAccount
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.account import request_account
from salitaaco.utils.board import board_names, boards

# The pages about one child have the child in their address. The sidebar links
# to them for the "selected child": the one whose page was opened last, kept in
# the session under this key, or the first child when none was.
SELECTED_CHILD_KEY = "selected_child"

# The page the sidebar's picker opens for a child when the page being shown is not about a child.
DEFAULT_CHILD_ROUTE = "child_boards"

# The pages about one child that the picker can open for another child: the
# sidebar's child pages, and the page that edits a child.
CHILD_PAGE_ROUTES = {"manage_child"} | {
    item["route"] for category in dashboard_items for item in category["items"] if item.get("child")
}


def guardian_child_or_404(request, child_uuid):
    """
    The child a guardian's page is about. Only the child's own guardian gets
    them; anyone else gets 404. Opening the page makes the child the selected one.
    """
    child = get_object_or_404(
        ChildAccount.objects.select_related("user", "family_voice", "guardian"),
        uuid=child_uuid,
        guardian__user=request.user,
    )
    request.session[SELECTED_CHILD_KEY] = str(child.uuid)
    return child


def children_with_numbers(children):
    """
    Children by name with what the tables of children show beside each one:
    their taps (`total_taps`), their voice, and how many of the boards are on
    for them (`shown_boards` of `total_boards`). `children` is a queryset.
    """
    return children.select_related("user", "family_voice").prefetch_related("hidden_boards").annotate(
        total_taps=Coalesce(Sum("user__word_usages__use_count"), 0, output_field=IntegerField()),
    ).order_by("display_name", "child_account_id")


def add_board_numbers(children):
    total = len(board_names())
    for child in children:
        child.shown_boards = len(boards(child))
        child.total_boards = total
    return children


def guardian_children(request):
    """The logged-in guardian's children by name, looked up once per request. Empty for the other roles."""
    if not hasattr(request, "_children"):
        account = request_account(request)
        request._children = (
            list(account.children.select_related("user").order_by("display_name", "child_account_id"))
            if isinstance(account, GuardianAccount) else []
        )
    return request._children


def selected_child(request):
    """The child the sidebar's child pages lead to, or None for a guardian without children."""
    children = guardian_children(request)
    chosen = request.session.get(SELECTED_CHILD_KEY)
    for child in children:
        if str(child.uuid) == chosen:
            return child
    return children[0] if children else None


def child_picker(request):
    """
    The sidebar's list of children: each with the address choosing it leads to,
    which is the page being shown for that child when it is a child's page.
    """
    match = getattr(request, "resolver_match", None)
    route = match.url_name if match is not None and match.url_name in CHILD_PAGE_ROUTES else DEFAULT_CHILD_ROUTE

    selected = selected_child(request)
    return [
        {
            "child": child,
            "url": reverse(route, args=[child.uuid]),
            "selected": child == selected,
        }
        for child in guardian_children(request)
    ]
