from ..utils.profile import get_user_profile


def current_profile(request):
    """The logged-in user's profile, for the name and picture in the sidebar."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"current_profile": None}
    return {"current_profile": get_user_profile(user)}
