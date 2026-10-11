from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    path(
        "password/change/done/",
        views.PasswordChangeDoneView.as_view(),
        name="password-change-done",
    ),
    path("employees/", views.employee_list, name="employee-list"),
    path("employees/create/", views.employee_create, name="employee-create"),
    path(
        "employees/<int:pk>/toggle-active/",
        views.employee_toggle_active,
        name="employee-toggle-active",
    ),
]
