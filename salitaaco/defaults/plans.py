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

# How many tiles and boards of their own a guardian can add, on the free plan
# and on a paid one, until an admin changes them on System Settings > Mga Plano.
# Each counts across all of the guardian's family's boards. Over a limit, the
# oldest ones up to it show and the rest are kept, hidden.
DEFAULT_FREE_WORD_LIMIT = 0
DEFAULT_PLUS_WORD_LIMIT = 20
DEFAULT_FREE_BOARD_LIMIT = 0
DEFAULT_PLUS_BOARD_LIMIT = 5

# How many child accounts a guardian can make on a plan, until an admin changes
# it on the plan's card on System Settings > Mga Plano. A plan an admin adds
# starts at the paid number. A guardian over their plan's limit (a paid plan
# ended, or an admin lowered it) keeps every child; only adding more stops.
DEFAULT_FREE_CHILD_LIMIT = 1
DEFAULT_PAID_CHILD_LIMIT = 3
MAX_CHILD_LIMIT = 50

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
