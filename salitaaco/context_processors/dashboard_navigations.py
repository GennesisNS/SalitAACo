from django.urls import reverse

from ..defaults.navigations import dashboard_items


def navigation_items(request):
    """
    The sidebar for the current user: only the items their groups may see,
    with each route resolved to a URL and one item marked active.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"navigation_items": []}

    groups = list(user.groups.values_list("name", flat=True))
    results = []

    for category in dashboard_items:
        # filter items by role (allow items with "*" in roles for everyone)
        allowed_items = [
            {**item, "url": reverse(item["route"]), "active": False}
            for item in category.get("items", [])
            if "*" in item.get("roles", []) or any(role in groups for role in item.get("roles", []))
        ]

        if allowed_items:  # only include category if it has allowed items
            results.append({
                **category,
                "items": allowed_items,
            })

    # A view names its sidebar item with @active_nav; the first id the user can see wins.
    visible_items = {item["id"]: item for category in results for item in category["items"]}
    for nav_id in getattr(request, "active_nav_ids", ()):
        if nav_id in visible_items:
            visible_items[nav_id]["active"] = True
            break

    return {"navigation_items": results}
