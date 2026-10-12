from .administrator_roles import ADMINISTRATOR
from .user_roles import GUARDIAN

# The navigation of each layout. "route" is a URL name; the context processor resolves it.
# "fragment", when given, is added to the URL after a "#": the board is one page
# whose screens are told apart that way (see static/js/board.js).
# "roles" lists the groups that may see the item ("*" for every logged-in user).
# "child": True marks a page about one child: its URL takes the selected child,
# and a guardian without children does not see it. A category with
# "child_picker": True shows the list to pick that child from above its items.

# The sidebar of guardians and admins (templates/layouts/dashboard.html).
# "icon" names a drawing in templates/components/icon.html.
dashboard_items = [
    {
        "name": "Aking Pamilya",
        "items": [
            {
                "name": "Buod",
                "id": "overview",
                "route": "overview",
                "icon": "home",
                "roles": [GUARDIAN],
            },
            {
                "name": "Mga Bata",
                "id": "children",
                "route": "children",
                "icon": "users",
                "roles": [GUARDIAN],
            },
            {
                "name": "Boses ng Pamilya",
                "id": "family_voices",
                "route": "family_voices",
                "icon": "mic",
                "roles": [GUARDIAN],
            },
        ],
    },
    {
        "name": "Napiling Bata",
        "child_picker": True,
        "items": [
            {
                "name": "Mga Board",
                "id": "child_boards",
                "route": "child_boards",
                "icon": "grid",
                "roles": [GUARDIAN],
                "child": True,
            },
            # May be removed, with routes/favorites/.
            {
                "name": "Mga Paborito",
                "id": "favorites",
                "route": "favorites",
                "icon": "star",
                "roles": [GUARDIAN],
                "child": True,
            },
            {
                "name": "Boses",
                "id": "child_voice",
                "route": "child_voice",
                "icon": "volume",
                "roles": [GUARDIAN],
                "child": True,
            },
            {
                "name": "Paggamit",
                "id": "child_usage",
                "route": "child_usage",
                "icon": "chart",
                "roles": [GUARDIAN],
                "child": True,
            },
        ],
    },
    {
        "name": "Account",
        "items": [
            {
                "name": "Mga Tile",
                "id": "board",
                "route": "board",
                "icon": "message",
                "roles": ["*"],
            },
            {
                "name": "Tulong at Suporta",
                "id": "support",
                "route": "support",
                "icon": "help",
                "roles": [GUARDIAN],
            },
            {
                "name": "Settings",
                "id": "settings",
                "route": "settings",
                "icon": "sliders",
                "roles": ["*"],
            },
            {
                "name": "Account",
                "id": "profile",
                "route": "profile",
                "icon": "user",
                "roles": [GUARDIAN],
            },
        ],
    },
    {
        "name": "Admin",
        "items": [
            {
                "name": "Admin dashboard",
                "id": "analytics",
                "route": "analytics",
                "icon": "chart",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
]

# The navigation along the bottom of a child's pages (templates/layouts/child.html).
# "icon" is an emoji here: big and friendly, like the tiles.
child_items = [
    {
        "name": "Menu",
        "items": [
            {
                "name": "Home",
                "id": "home",
                "route": "board",
                "fragment": "home",
                "icon": "🏠",
                "roles": ["*"],
            },
            {
                "name": "Mga Board",
                "id": "boards",
                "route": "board",
                "fragment": "boards",
                "icon": "🧩",
                "roles": ["*"],
            },
            {
                "name": "Paborito",
                "id": "favorites",
                "route": "board",
                "fragment": "favorites",
                "icon": "⭐",
                "roles": ["*"],
            },
            {
                "name": "Profile",
                "id": "profile",
                "route": "profile",
                "icon": "🙂",
                "roles": ["*"],
            },
        ],
    },
]
