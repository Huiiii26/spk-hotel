from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """Bắt buộc đăng nhập, đang hoạt động và có một trong các role cho phép."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/accounts/login/?next={request.get_full_path()}")
            if not request.user.is_active:
                logout(request)
                messages.error(request, "Tài khoản của bạn đã bị khóa.")
                return redirect("accounts:login")
            if request.user.role not in allowed_roles:
                raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(AccessMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_active:
            logout(request)
            messages.error(request, "Tài khoản của bạn đã bị khóa.")
            return redirect("accounts:login")
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")
        return super().dispatch(request, *args, **kwargs)
