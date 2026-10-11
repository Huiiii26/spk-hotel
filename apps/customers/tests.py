from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Customer


User = get_user_model()


class CustomerPermissionTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            email="manager.customer@example.com",
            password="SafePass2026!",
            full_name="Quản lý",
            role=User.Role.MANAGER,
        )
        self.receptionist = User.objects.create_user(
            email="reception.customer@example.com",
            password="SafePass2026!",
            full_name="Lễ tân",
            role=User.Role.RECEPTIONIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant.customer@example.com",
            password="SafePass2026!",
            full_name="Kế toán",
            role=User.Role.ACCOUNTANT,
        )
        self.customer_user = User.objects.create_user(
            email="owner@example.com",
            password="SafePass2026!",
            full_name="Khách cũ",
            role=User.Role.CUSTOMER,
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            full_name="Khách cũ",
            email="owner@example.com",
        )

    def test_receptionist_can_create_walk_in_customer(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            reverse("customers-staff:customer-create"),
            {
                "full_name": "Khách trực tiếp",
                "email": "walkin@example.com",
                "phone": "0901234567",
                "address": "Thái Nguyên",
                "date_of_birth": "2000-01-02",
                "identity_document": "012345678901",
                "notes": "Khách chưa có tài khoản",
            },
        )
        self.assertRedirects(response, reverse("customers-staff:customer-list"))
        walk_in = Customer.objects.get(email="walkin@example.com")
        self.assertIsNone(walk_in.user)

    def test_manager_can_view_and_create_customer(self):
        self.client.force_login(self.manager)
        self.assertEqual(
            self.client.get(reverse("customers-staff:customer-list")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("customers-staff:customer-create")).status_code,
            200,
        )

    def test_accountant_cannot_view_customer_list(self):
        self.client.force_login(self.accountant)
        response = self.client.get(reverse("customers-staff:customer-list"))
        self.assertEqual(response.status_code, 403)

    def test_customer_can_update_own_profile_and_user_fields_are_synced(self):
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("customers:profile"),
            {
                "full_name": "Khách mới",
                "email": "new-owner@example.com",
                "phone": "0911222333",
                "address": "Bắc Kạn",
                "date_of_birth": "2001-03-04",
                "identity_document": "B1234567",
                "notes": "Đã cập nhật",
            },
        )
        self.assertRedirects(response, reverse("customers:profile"))
        self.customer.refresh_from_db()
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer.full_name, "Khách mới")
        self.assertEqual(self.customer_user.full_name, "Khách mới")
        self.assertEqual(self.customer_user.email, "new-owner@example.com")
