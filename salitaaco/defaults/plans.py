# The plans a guardian can be on, as the guardian, admin and public pages show them.
#
# FRONTEND ONLY FOR NOW: there is no plan model yet. When the backend of
# subscriptions is built, the plans move to the database (seeded with these
# two) so that an admin can edit them, and this file goes.
#
# The features are those of the business draft, without the language modes,
# which are not decided yet.

FREE = "free"
PLUS = "plus"

PLANS = [
    {
        "key": FREE,
        "name": "Free",
        "price": 0,
        "period": "habambuhay",
        "offered": True,
        "features": [
            "Mga pangunahing board ng simbolo",
            "Mga karaniwang sitwasyong Pilipino",
            "Boses na text-to-speech",
            "Pag-set up ng profile ng tagapag-alaga",
        ],
    },
    {
        "key": PLUS,
        "name": "SalitAACo Plus",
        "price": 149,
        "period": "kada buwan",
        "offered": True,
        "features": [
            "Lahat ng nasa Free",
            "Boses ng pamilya (family voice banking)",
            "Mada-download na ulat ng paggamit",
            "Karagdagang mga scenario pack",
        ],
    },
]

# With no subscriptions yet, every guardian is on this plan.
DEFAULT_PLAN = FREE

# What a payment can be. A guardian's upload starts as PENDING; an admin approves or rejects it.
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"

PAYMENT_STATUSES = [
    (PENDING, "Naghihintay"),
    (APPROVED, "Aprubado"),
    (REJECTED, "Tinanggihan"),
]
