from django.urls import reverse

from ..models.child_account import ChildAccount
from ..utils.account import home_route, request_account
from ..utils.children import child_picker, selected_child

CHILD_LAYOUT = "layouts/child.html"
DASHBOARD_LAYOUT = "layouts/dashboard.html"


def current_account(request):
    """
    The logged-in user's account, for the name and picture in the layout, and
    what the layout depends on: a child's pages are drawn in the child layout,
    a guardian's and an admin's in the dashboard layout, whose first page is
    where "back to the dashboard" leads. A guardian also gets their children,
    for the sidebar.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"current_account": None}

    account = request_account(request)
    is_child = isinstance(account, ChildAccount)

    return {
        "current_account": account,
        "is_child": is_child,
        "layout_template": CHILD_LAYOUT if is_child else DASHBOARD_LAYOUT,
        "home_url": reverse(home_route(account)),
        # A guardian's sidebar: the child its child pages lead to, and the list to pick another from.
        "selected_child": selected_child(request),
        "child_picker": child_picker(request),
    }
