from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.customers.models import Customer

from .models import User


@transaction.atomic
def register_customer(*, full_name, email, phone, password):
    """Tạo tài khoản web và hồ sơ khách hàng trong cùng transaction."""
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        role=User.Role.CUSTOMER,
    )
    Customer.objects.create(
        user=user,
        full_name=full_name,
        email=user.email,
        phone=phone,
    )
    return user


@transaction.atomic
def create_staff_account(*, actor, full_name, email, phone, role, password):
    if actor.role != User.Role.MANAGER:
        raise PermissionDenied("Chỉ quản lý được tạo tài khoản nhân viên.")
    if role not in {User.Role.RECEPTIONIST, User.Role.ACCOUNTANT}:
        raise ValidationError("Vai trò nhân viên không hợp lệ.")
    return User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        role=role,
    )


@transaction.atomic
def toggle_staff_active(*, actor, employee):
    if actor.role != User.Role.MANAGER:
        raise PermissionDenied("Chỉ quản lý được khóa hoặc mở tài khoản.")
    if actor.pk == employee.pk:
        raise ValidationError("Quản lý không thể tự khóa tài khoản của mình.")
    if employee.role not in {User.Role.RECEPTIONIST, User.Role.ACCOUNTANT}:
        raise ValidationError("Chỉ được thay đổi trạng thái tài khoản nhân viên.")
    employee.is_active = not employee.is_active
    employee.save(update_fields=["is_active", "updated_at"])
    return employee
