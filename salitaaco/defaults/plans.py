# The plans a guardian can be on, and what a payment for one can become.
#
# The plans themselves are rows of the Plan model, which an admin edits on Mga
# Subscription. Migration 0017 made the first two, Free and SalitAACo Plus.

FREE = "free"
PLUS = "plus"

# The plan of every guardian who has not paid, or whose paid months are over.
# It is always free and always offered.
DEFAULT_PLAN = FREE

# How long one approved payment keeps a guardian on a paid plan. A payment
# approved while the guardian is still on the plan adds to the end of it.
PAID_MONTHS = 1

# How many family voices a guardian on a free plan can have. A paid plan has no
# limit. Voices made while on a paid plan stay when it ends; only adding more stops.
FREE_FAMILY_VOICE_LIMIT = 2

# How many tiles of their own a guardian on a paid plan can add, across all the
# boards, until an admin changes it on System Settings > General.
DEFAULT_GUARDIAN_WORD_LIMIT = 20

FREE_PERIOD = "habambuhay"
PAID_PERIOD = "kada buwan"

# What a payment can be. A guardian's upload starts as PENDING; an admin approves or rejects it.
PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"

PAYMENT_STATUSES = [
    (PENDING, "Naghihintay"),
    (APPROVED, "Aprubado"),
    (REJECTED, "Tinanggihan"),
]
