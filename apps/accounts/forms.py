from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


BOOTSTRAP_INPUT = {"class": "form-control"}


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={**BOOTSTRAP_INPUT, "autocomplete": "email"}),
    )
    full_name = forms.CharField(
        label="Họ và tên",
        max_length=150,
        widget=forms.TextInput(attrs=BOOTSTRAP_INPUT),
    )
    phone = forms.CharField(
        label="Số điện thoại",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs=BOOTSTRAP_INPUT),
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password2"].label = "Nhập lại mật khẩu"
        self.fields["password1"].widget.attrs.update(BOOTSTRAP_INPUT)
        self.fields["password2"].widget.attrs.update(BOOTSTRAP_INPUT)

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"]).lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email


class StaffCreationForm(CustomerRegistrationForm):
    role = forms.ChoiceField(
        label="Vai trò nhân viên",
        choices=(
            (User.Role.RECEPTIONIST, User.Role.RECEPTIONIST.label),
            (User.Role.ACCOUNTANT, User.Role.ACCOUNTANT.label),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(CustomerRegistrationForm.Meta):
        fields = ("full_name", "email", "phone", "role", "password1", "password2")


class AdminUserCreationForm(UserCreationForm):
    """Form dành riêng cho trang Django Admin."""

    class Meta:
        model = User
        fields = ("email", "full_name", "phone", "role")
