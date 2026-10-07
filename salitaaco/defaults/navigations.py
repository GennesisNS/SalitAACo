from .administrator_roles import ADMINISTRATOR

# The dashboard sidebar. "route" is a URL name; the context processor resolves it.
# "roles" lists the groups that may see the item ("*" for every logged-in user).

dashboard_items = [
    {
        "name": "SalitAACo",
        "items": [
            {
                "name": "Mga Tile",
                "id": "board",
                "route": "board",
                "icon": "🧩",
                "roles": ["*"],
            },
            {
                "name": "Profile",
                "id": "profile",
                "route": "profile",
                "icon": "👤",
                "roles": ["*"],
            },
            {
                "name": "Settings",
                "id": "settings",
                "route": "settings",
                "icon": "⚙️",
                "roles": ["*"],
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
                "icon": "📊",
                "roles": [ADMINISTRATOR],
            },
        ],
    },
]
