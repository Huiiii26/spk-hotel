from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.accounts.models import User


def ensure_room_manager(actor):
    if actor.role != User.Role.MANAGER:
        raise PermissionDenied("Chỉ quản lý được thay đổi phòng và loại phòng.")


@transaction.atomic
def save_room_type(*, actor, form):
    ensure_room_manager(actor)
    return form.save()


@transaction.atomic
def save_room(*, actor, form):
    ensure_room_manager(actor)
    return form.save()
