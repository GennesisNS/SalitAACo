import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from salitaaco.defaults.user_roles import GUARDIAN
from salitaaco.forms.authentication import LoginForm, RegisterForm
from salitaaco.models.guardian_account import GuardianAccount
from salitaaco.utils.account import add_to_group, get_user_account, home_route

logger = logging.getLogger(__name__)


def redirect_home(request):
    """To the first page of whoever is logged in: the board, the overview or the admin dashboard."""
    return redirect(home_route(get_user_account(request.user)))


def is_inactive_account(username, password):
    """
    Whether the login failed only because an admin made the account inactive.
    The password has to be right as well: someone guessing usernames learns nothing from this.
    """
    user = User.objects.filter(username__iexact=username).first()
    return user is not None and not user.is_active and user.check_password(password)


def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.user.is_authenticated:
        # A logged-in user only lands here when a page turned them away.
        if next_url:
            messages.error(request, "Naka-log in ka pero walang pahintulot ang account na ito sa pahinang iyon.")
        return redirect_home(request)

    login_form = LoginForm()

    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = authenticate(
                request,
                username=login_form.cleaned_data['username'],
                password=login_form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect_home(request)
            if is_inactive_account(login_form.cleaned_data['username'], login_form.cleaned_data['password']):
                login_form.add_error(None, "Hindi aktibo ang account na ito. Makipag-ugnayan sa admin.")
            else:
                login_form.add_error(None, "Maling username o password.")

    context = {
        "login_form": login_form,
        "next": next_url,
    }
    return render(request, 'auth/login.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect_home(request)

    register_form = RegisterForm()

    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            # Signing up makes a guardian account. Children's accounts are made
            # by their guardian, on the "Mga Bata" page.
            with transaction.atomic():
                user = User.objects.create_user(
                    username=register_form.cleaned_data['username'],
                    password=register_form.cleaned_data['password'],
                )
                GuardianAccount.objects.create(
                    user=user,
                    display_name=register_form.cleaned_data['display_name'],
                )
                add_to_group(user, GUARDIAN)
            logger.info("New guardian account registered: %s", user.username)
            login(request, user, backend='salitaaco.authentication.custom_authentication.UsernameBackend')
            return redirect('children')

    context = {
        "register_form": register_form,
    }
    return render(request, 'auth/register.html', context)


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
