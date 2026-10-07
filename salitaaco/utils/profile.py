from salitaaco.models.profile import Profile


def get_user_profile(user):
    """
    The user's profile. Accounts made outside the app (createsuperuser, the
    Django admin) have none yet, so one is created with the username as the name.
    """
    profile, _ = Profile.objects.get_or_create(user=user, defaults={"display_name": user.username})
    return profile
