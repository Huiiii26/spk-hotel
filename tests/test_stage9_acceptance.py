from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse


class RoleNavigationAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.users = {
            user.role: user
            for user in get_user_model().objects.filter(
                email__in=[
                    "quanli@hotel.com",
                    "letan@hotel.com",
                    "ketoan@hotel.com",
                    "customer1@spkhotel.vn",
                ]
            )
        }

    def assert_pages_available(self, role, names):
        self.client.force_login(self.users[role])
        for name in names:
            with self.subTest(role=role, url=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.client.logout()

    def test_manager_navigation(self):
        self.assert_pages_available("MANAGER", [
            "core:staff-dashboard", "accounts:employee-list", "rooms-staff:room-type-list",
            "rooms-staff:room-list", "customers-staff:customer-list", "bookings-staff:list",
            "services-staff:list", "billing-staff:list", "reports-staff:dashboard",
            "ai-integration:report", "ai-integration:logs",
        ])

    def test_receptionist_navigation(self):
        self.assert_pages_available("RECEPTIONIST", [
            "core:staff-dashboard", "rooms-staff:room-list", "customers-staff:customer-list",
            "bookings-staff:list", "bookings-staff:calendar", "billing-staff:list",
            "ai-integration:room-advisor",
        ])

    def test_accountant_navigation(self):
        self.assert_pages_available("ACCOUNTANT", [
            "core:staff-dashboard", "billing-staff:list", "reports-staff:dashboard",
            "ai-integration:report",
        ])

    def test_customer_navigation(self):
        self.assert_pages_available("CUSTOMER", [
            "customers:overview", "customers:profile", "bookings:availability-search",
            "ai-integration:room-advisor", "customer-bookings:list", "customer-billing:list",
        ])

    def test_backend_denies_cross_role_pages(self):
        customer = self.users["CUSTOMER"]
        self.client.force_login(customer)
        self.assertEqual(self.client.get(reverse("accounts:employee-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("reports-staff:dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("billing-staff:list")).status_code, 403)


class ErrorPageAcceptanceTests(TestCase):
    @override_settings(DEBUG=False)
    def test_404_is_friendly_and_hides_debug_details(self):
        response = self.client.get("/duong-dan-khong-ton-tai/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Không tìm thấy trang", status_code=404)
        self.assertNotContains(response, "Traceback", status_code=404)
