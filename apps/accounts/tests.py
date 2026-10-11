from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer


User = get_user_model()


class RegistrationTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "full_name": "Nguyễn Văn Khách",
            "email": "customer@example.com",
            "phone": "0912345678",
            "password1": "SafePass2026!",
            "password2": "SafePass2026!",
        }
        data.update(overrides)
        return data

    def test_customer_can_register(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data())

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(email="customer@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.check_password("SafePass2026!"))
        self.assertTrue(Customer.objects.filter(user=user).exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            email="customer@example.com",
            password="SafePass2026!",
            full_name="Khách cũ",
        )
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data(email="CUSTOMER@example.com"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email này đã được sử dụng")
        self.assertEqual(User.objects.count(), 1)

    def test_public_registration_cannot_choose_manager_role(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data(role=User.Role.MANAGER),
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="customer@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com",
            password="SafePass2026!",
            full_name="Người dùng đăng nhập",
            role=User.Role.CUSTOMER,
        )
        Customer.objects.create(
            user=self.user,
            full_name=self.user.full_name,
            email=self.user.email,
        )

    def test_login_with_correct_email_and_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": "SafePass2026!"},
        )

        self.assertRedirects(response, reverse("customers:overview"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_locked_account_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active", "updated_at"])

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": "SafePass2026!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_can_be_changed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:password-change"),
            {
                "old_password": "SafePass2026!",
                "new_password1": "NewSafePass2027!",
                "new_password2": "NewSafePass2027!",
            },
        )

        self.assertRedirects(response, reverse("accounts:password-change-done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSafePass2027!"))


class EmployeePermissionTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="SafePass2026!",
            full_name="Quản lý",
            role=User.Role.MANAGER,
            is_staff=True,
        )
        self.receptionist = User.objects.create_user(
            email="receptionist@example.com",
            password="SafePass2026!",
            full_name="Lễ tân",
            role=User.Role.RECEPTIONIST,
        )

    def test_employee_cannot_access_employee_management(self):
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse("accounts:employee-list"))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_accountant(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("accounts:employee-create"),
            {
                "full_name": "Kế toán mới",
                "email": "accountant@example.com",
                "phone": "0987654321",
                "role": User.Role.ACCOUNTANT,
                "password1": "SafePass2026!",
                "password2": "SafePass2026!",
            },
        )

        self.assertRedirects(response, reverse("accounts:employee-list"))
        employee = User.objects.get(email="accountant@example.com")
        self.assertEqual(employee.role, User.Role.ACCOUNTANT)

    def test_manager_can_lock_and_unlock_employee(self):
        self.client.force_login(self.manager)
        url = reverse("accounts:employee-toggle-active", args=[self.receptionist.pk])

        self.client.post(url)
        self.receptionist.refresh_from_db()
        self.assertFalse(self.receptionist.is_active)

        self.client.post(url)
        self.receptionist.refresh_from_db()
        self.assertTrue(self.receptionist.is_active)

    def test_toggle_active_rejects_get(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("accounts:employee-toggle-active", args=[self.receptionist.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_customer_cannot_access_staff_dashboard(self):
        customer_user = User.objects.create_user(
            email="customer2@example.com",
            password="SafePass2026!",
            full_name="Khách hàng",
        )
        self.client.force_login(customer_user)
        response = self.client.get(reverse("core:staff-dashboard"))
        self.assertEqual(response.status_code, 403)

# Create your tests here.
