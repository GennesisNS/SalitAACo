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
            {
                "name": "Sariling Board",
                "id": "guardian_boards",
                "route": "guardian_boards",
                "icon": "grid",
                "roles": [GUARDIAN],
            },
            {
                "name": "Sariling Tile",
                "id": "guardian_words",
                "route": "guardian_words",
                "icon": "type",
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
    # ----- The admin's pages -----
    {
        "name": "Buod",
        "items": [
            {
                "name": "Dashboard",
                "id": "analytics",
                "route": "analytics",
                "icon": "home",
                "roles": [ADMINISTRATOR],
            },
            {
                "name": "Analytics at Ulat",
                "id": "reports",
                "route": "reports",
                "icon": "chart",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
    {
        "name": "Pamamahala",
        "items": [
            {
                "name": "Mga User",
                "id": "users",
                "route": "users",
                "icon": "users",
                "roles": [ADMINISTRATOR],
            },
            {
                "name": "Mga Board",
                "id": "admin_boards",
                "route": "admin_boards",
                "icon": "grid",
                "roles": [ADMINISTRATOR],
            },
            {
                "name": "Mga Salita at Simbolo",
                "id": "words",
                "route": "words",
                "icon": "type",
                "roles": [ADMINISTRATOR],
            },
            # May be removed, with routes/institutions/.
            {
                "name": "Mga Paaralan at Institusyon",
                "id": "institutions",
                "route": "institutions",
                "icon": "building",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
    {
        "name": "Negosyo",
        "items": [
            {
                "name": "Kita",
                "id": "revenue",
                "route": "revenue",
                "icon": "receipt",
                "roles": [ADMINISTRATOR],
            },
            {
                "name": "Mga Subscription",
                "id": "subscriptions",
                "route": "subscriptions",
                "icon": "card",
                "roles": [ADMINISTRATOR],
            },
            # May be removed, with routes/feedback/.
            {
                "name": "Feedback at mga Isyu",
                "id": "feedback",
                "route": "feedback",
                "icon": "message",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
    {
        "name": "System Settings",
        "items": [
            {
                "name": "General",
                "id": "system_general",
                "route": "system_general",
                "icon": "sliders",
                "roles": [ADMINISTRATOR],
            },
            {
                "name": "Access control",
                "id": "system_access",
                "route": "system_access",
                "icon": "shield",
                "roles": [ADMINISTRATOR],
            },
            # May be removed, with routes/privacy/.
            {
                "name": "Privacy",
                "id": "system_privacy",
                "route": "system_privacy",
                "icon": "lock",
                "roles": [ADMINISTRATOR],
            },
            # May be removed, with routes/technical_status/.
            {
                "name": "Technical status",
                "id": "system_status",
                "route": "system_status",
                "icon": "activity",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
    # ----- Everyone's own: their board, how the app looks for them, their account -----
    {
        "name": "Account",
        "items": [
            {
                "name": "Mga Tile",
                "id": "board",
                "route": "board",
                "icon": "puzzle",
                "roles": ["*"],
            },
            {
                "name": "Plano at Subscription",
                "id": "plan",
                "route": "plan",
                "icon": "card",
                "roles": [GUARDIAN],
            },
            {
                "name": "Tulong at Suporta",
                "id": "support",
                "route": "support",
                "icon": "help",
                "roles": [GUARDIAN],
            },
            {
                "name": "Hitsura at Tile",
                "id": "settings",
                "route": "settings",
                "icon": "eye",
                "roles": ["*"],
            },
            {
                "name": "Account",
                "id": "profile",
                "route": "profile",
                "icon": "user",
                "roles": [GUARDIAN, ADMINISTRATOR],
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
