from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from salitaaco.forms.account.change_password import ChangePasswordForm
from salitaaco.forms.account.delete_account import DeleteAccountForm
from salitaaco.forms.account.profile_information import ProfileInformationForm
from salitaaco.forms.account.upload_avatar import UploadAvatarForm
from salitaaco.utils.account import delete_user_account
from salitaaco.utils.active_nav import active_nav
from salitaaco.utils.perms_check import is_app_user, multi_user_test
from salitaaco.utils.profile import get_user_profile
from salitaaco.utils.uploads import random_upload_name


@active_nav("account")
@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def manage_account(request):
    profile = get_user_profile(request.user)

    profile_form = ProfileInformationForm(initial={
        "display_name": profile.display_name,
        "age": profile.age,
    })
    avatar_form = UploadAvatarForm()
    password_form = ChangePasswordForm(user=request.user)
    delete_account_form = DeleteAccountForm(user=request.user)

    if request.method == "POST":
        if "profile_form" in request.POST:
            profile_form = ProfileInformationForm(request.POST)
            if profile_form.is_valid():
                profile.display_name = profile_form.cleaned_data['display_name']
                profile.age = profile_form.cleaned_data['age']
                profile.save()
                messages.success(request, "Naka-save na ang profile.")
                return redirect('account')

        if "avatar_form" in request.POST:
            avatar_form = UploadAvatarForm(request.POST, request.FILES)
            if avatar_form.is_valid():
                avatar = avatar_form.cleaned_data['avatar']
                profile.set_avatar(random_upload_name(avatar.content_type), avatar, avatar.content_type)
                messages.success(request, "Nai-save na ang larawan.")
                return redirect('account')

        if "password_form" in request.POST:
            password_form = ChangePasswordForm(request.POST, user=request.user)
            if password_form.is_valid():
                request.user.set_password(password_form.cleaned_data['new_password'])
                request.user.save()
                # Changing the password must not log the user out.
                update_session_auth_hash(request, request.user)
                messages.success(request, "Nabago na ang password.")
                return redirect('account')

        if "delete_account_form" in request.POST:
            delete_account_form = DeleteAccountForm(request.POST, user=request.user)
            if delete_account_form.is_valid():
                user = request.user
                logout(request)
                delete_user_account(user)
                messages.success(request, "Permanente nang nabura ang account.")
                return redirect('login')

    context = {
        "profile": profile,
        "profile_form": profile_form,
        "avatar_form": avatar_form,
        "password_form": password_form,
        "delete_account_form": delete_account_form,
        "show_delete_account_modal": bool(delete_account_form.errors),
    }
    return render(request, 'dashboard/account/account.html', context)


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_avatar(request):
    profile = get_user_profile(request.user)
    if not profile.has_avatar:
        raise Http404()
    response = FileResponse(profile.avatar.open('rb'), content_type=profile.avatar_mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
@require_POST
def remove_avatar(request):
    get_user_profile(request.user).remove_avatar()
    messages.success(request, "Naalis na ang larawan.")
    return redirect('account')
