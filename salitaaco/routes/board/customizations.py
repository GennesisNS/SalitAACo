from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from salitaaco.models.customization import Customization
from salitaaco.utils.perms_check import is_app_user, multi_user_test


def private_file_response(file, mime):
    """Serve an upload to its owner only; the browser may cache it for a day."""
    response = FileResponse(file.open('rb'), content_type=mime or "application/octet-stream")
    response["Cache-Control"] = "private, max-age=86400"
    return response


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_customization_image(request, customization_uuid):
    customization = get_object_or_404(Customization, uuid=customization_uuid, user=request.user)
    if not customization.has_image:
        raise Http404()
    return private_file_response(customization.image, customization.image_mime)


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
def view_customization_sound(request, customization_uuid):
    customization = get_object_or_404(Customization, uuid=customization_uuid, user=request.user)
    if not customization.has_sound:
        raise Http404()
    return private_file_response(customization.sound, customization.sound_mime)


@login_required(login_url='/login/')
@multi_user_test(is_app_user)
@require_POST
def reset_customization(request, customization_uuid):
    customization = get_object_or_404(Customization, uuid=customization_uuid, user=request.user)
    customization.reset()
    messages.success(request, "Naibalik na sa default ang tile.")
    return redirect('board')
