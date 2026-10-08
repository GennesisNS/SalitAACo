from ..utils.account import get_user_account


def current_account(request):
    """The logged-in user's account, for the name and picture in the sidebar."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"current_account": None}
    return {"current_account": get_user_account(user)}
