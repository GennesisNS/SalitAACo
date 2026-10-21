from django.urls import reverse

from ..defaults.navigations import child_items, dashboard_items
from ..models.child_account import ChildAccount
from ..utils.account import request_account
from ..utils.children import selected_child
from ..utils.perms_check import user_roles


def item_url(item, child):
    url = reverse(item["route"], args=[child.uuid] if item.get("child") else [])
    return f"{url}#{item['fragment']}" if item.get("fragment") else url


def navigation_items(request):
    """
    The navigation for the current user: a child's bottom navigation or the
    sidebar of guardians and admins. Only the items their roles may see (an
    admin's are only the admin's, see user_roles), with each route resolved to
    a URL and one item marked active.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"navigation_items": []}

    items = child_items if isinstance(request_account(request), ChildAccount) else dashboard_items
    groups = user_roles(user)
    child = selected_child(request)
    results = []

    for category in items:
        # filter items by role (allow items with "*" in roles for everyone)
        allowed_items = [
            {**item, "url": item_url(item, child), "active": False}
            for item in category.get("items", [])
            if ("*" in item.get("roles", []) or any(role in groups for role in item.get("roles", [])))
            # A page about one child needs a child to be about.
            and (child is not None or not item.get("child"))
        ]

        if allowed_items:  # only include category if it has allowed items
            results.append({
                **category,
                "items": allowed_items,
            })

    # A view names its navigation item with @active_nav; the first id the user can see wins.
    visible_items = {item["id"]: item for category in results for item in category["items"]}
    for nav_id in getattr(request, "active_nav_ids", ()):
        if nav_id in visible_items:
            visible_items[nav_id]["active"] = True
            break

    return {"navigation_items": results}
