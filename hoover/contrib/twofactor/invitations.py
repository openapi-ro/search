from django.db import transaction
from datetime import timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.utils.timezone import now
from django_otp import login as otp_login
from . import models

@transaction.atomic
def invite(username, duration, create=False):
    if create:
        user = get_user_model().objects.create(username=username)
    else:
        user = get_user_model().objects.get_by_natural_key(username)

    models.Invitation.objects.filter(user=user).delete()
    invitation = models.Invitation.objects.create(
        user=user,
        expires=now() + timedelta(minutes=duration),
    )

    url = "{}/invitation/{}".format(
        settings.HOOVER_BASE_URL,
        invitation.code,
    )
    return url

def get_or_404(code):
    return get_object_or_404(
        models.Invitation.objects.select_for_update(),
        code=code,
        expires__gt=now(),
    )

@transaction.atomic
def accept(request, invitation, device, password):
    user = invitation.user
    username = user.get_username()
    user.set_password(password)
    user.save()
    device.confirmed = True
    device.save()
    invitation.delete()
    user2 = authenticate(username=username, password=password)
    assert user2
    login(request, user2)
    otp_login(request, device)
