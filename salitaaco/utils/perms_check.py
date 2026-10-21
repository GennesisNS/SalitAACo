from django.contrib.auth.decorators import user_passes_test

from salitaaco.defaults.administrator_roles import ADMINISTRATOR
from salitaaco.defaults.user_roles import CHILD, GUARDIAN


def multi_user_test(*tests):
    def check(user):
        return any(test(user) for test in tests)
    return user_passes_test(check, login_url='/login/')


def user_roles(user):
    """
    The roles a user acts in: the names of their groups, except that an admin
    is only an admin. Admins are accounts of their own (create_admin, and
    migration 0019 took admin access away from accounts that were also a
    guardian's or a child's); this keeps any group left over from giving a
    guardian's pages to an admin.
    """
    groups = set(user.groups.values_list("name", flat=True))
    return {ADMINISTRATOR} if ADMINISTRATOR in groups else groups


def is_administrator(user):
    return user.groups.filter(name=ADMINISTRATOR).exists()


def is_guardian(user):
    return GUARDIAN in user_roles(user)


def is_child(user):
    return CHILD in user_roles(user)


def is_app_user(user):
    """Every logged-in account may use the board and manage itself."""
    return user.is_authenticated
