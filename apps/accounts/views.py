from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from .forms import CustomerRegistrationForm, StaffCreationForm
from .models import User
from .permissions import role_required
from .services import create_staff_account, register_customer, toggle_staff_active


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        if self.request.user.role == User.Role.CUSTOMER:
            return reverse("customers:overview")
        return reverse("core:staff-dashboard")


class LogoutView(auth_views.LogoutView):
    http_method_names = ["post", "options"]


class PasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password-change-done")
    success_message = "Đổi mật khẩu thành công."


class PasswordChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        register_customer(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            password=form.cleaned_data["password1"],
        )
        messages.success(request, "Đăng ký thành công. Bạn có thể đăng nhập.")
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


@role_required(User.Role.MANAGER)
def employee_list(request):
    employees = User.objects.filter(
        role__in=[User.Role.RECEPTIONIST, User.Role.ACCOUNTANT]
    ).order_by("role", "full_name")
    return render(request, "accounts/employee_list.html", {"employees": employees})


@role_required(User.Role.MANAGER)
def employee_create(request):
    form = StaffCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_staff_account(
            actor=request.user,
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            role=form.cleaned_data["role"],
            password=form.cleaned_data["password1"],
        )
        messages.success(request, "Đã tạo tài khoản nhân viên.")
        return redirect("accounts:employee-list")
    return render(request, "accounts/employee_form.html", {"form": form})


@require_POST
@role_required(User.Role.MANAGER)
def employee_toggle_active(request, pk):
    employee = get_object_or_404(User, pk=pk)
    try:
        toggle_staff_active(actor=request.user, employee=employee)
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        state = "mở khóa" if employee.is_active else "khóa"
        messages.success(request, f"Đã {state} tài khoản {employee.email}.")
    return redirect("accounts:employee-list")
