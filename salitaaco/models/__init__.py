# Django finds models through this package, so every model module is imported
# here. Application code imports each model from its own module instead.
from . import (  # noqa: F401
    admin_account,
    child_account,
    customization,
    daily_usage,
    family_voice,
    favorite_word,
    guardian_account,
    hidden_board,
    rating,
    support_message,
    word_usage,
)
