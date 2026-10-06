from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameBackend(ModelBackend):
    """
    Log in by username, ignoring letter case.

    The PHP application looked usernames up in a case-insensitive MySQL column,
    so "Miguel" and "miguel" are the same account on every database engine.
    """
    def authenticate(self, request, username: str | None = None, password: str | None = None, **kwargs):
        UserModel = get_user_model()
        if username is None or password is None:
            return None

        user = UserModel.objects.filter(username__iexact=username).first()
        if user is None:
            # Hash the password anyway so a missing account takes as long as a wrong password.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
