from django.contrib.auth.decorators import user_passes_test

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.defaults.user_roles import CHILD, GUARDIAN


def multi_user_test(*tests):
    def check(user):
        return any(test(user) for test in tests)
    return user_passes_test(check, login_url='/login/')


def is_administrator(user):
    return user.groups.filter(name=ADMINISTRATOR).exists()


def is_guardian(user):
    return user.groups.filter(name=GUARDIAN).exists()


def is_child(user):
    return user.groups.filter(name=CHILD).exists()


def is_app_user(user):
    """Every logged-in account may use the board and manage itself."""
    return user.is_authenticated
