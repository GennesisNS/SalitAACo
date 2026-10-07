# Django finds models through this package, so every model module is imported
# here. Application code imports each model from its own module instead.
from . import customization, profile, rating, word_usage  # noqa: F401
