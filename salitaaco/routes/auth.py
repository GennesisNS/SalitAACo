import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from salitaaco.forms.authentication import LoginForm, RegisterForm
from salitaaco.models.profile import Profile

logger = logging.getLogger(__name__)


def index_view(request):
    if request.user.is_authenticated:
        return redirect('board')
    return redirect('login')


def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.user.is_authenticated:
        # A logged-in user only lands here when a page turned them away.
        if next_url:
            messages.error(request, "Naka-log in ka pero hindi admin ang account na ito.")
        return redirect('board')

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
                return redirect('board')
            login_form.add_error(None, "Maling username o password.")

    context = {
        "login_form": login_form,
        "next": next_url,
    }
    return render(request, 'auth/login.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('board')

    register_form = RegisterForm()

    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=register_form.cleaned_data['username'],
                    password=register_form.cleaned_data['password'],
                )
                Profile.objects.create(
                    user=user,
                    display_name=register_form.cleaned_data['display_name'],
                )
            logger.info("New account registered: %s", user.username)
            login(request, user, backend='salitaaco.authentication.custom_authentication.UsernameBackend')
            return redirect('board')

    context = {
        "register_form": register_form,
    }
    return render(request, 'auth/register.html', context)


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
