from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.accounts.models import User


@transaction.atomic
def save_customer_by_receptionist(*, actor, form):
    if actor.role not in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        raise PermissionDenied("Chỉ quản lý hoặc lễ tân được thay đổi thông tin khách hàng.")
    return form.save()


@transaction.atomic
def update_own_profile(*, actor, form):
    customer = form.instance
    if actor.role != User.Role.CUSTOMER or customer.user_id != actor.pk:
        raise PermissionDenied("Bạn chỉ được cập nhật hồ sơ của mình.")
    customer = form.save()
    actor.full_name = customer.full_name
    actor.email = customer.email
    actor.phone = customer.phone
    actor.save(update_fields=["full_name", "email", "phone", "updated_at"])
    return customer
