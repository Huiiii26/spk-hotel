import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType

from .client import GeminiError, chat_completion
from .models import AILog, EmailDraft
from .services import advise_rooms, analyze_report, generate_email_draft


class FakeGeminiResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class GeminiClientTests(SimpleTestCase):
    @override_settings(
        GEMINI_API_KEY="test-key",
        GEMINI_BASE_URL="https://generativelanguage.googleapis.com",
        GEMINI_MODEL="gemini-2.5-flash",
        GEMINI_TIMEOUT_SECONDS=30,
    )
    @patch("apps.ai_integration.client.urlopen")
    def test_uses_generate_content_api_and_extracts_json_text(self, urlopen_mock):
        content = '{"suggestions": []}'
        urlopen_mock.return_value = FakeGeminiResponse(
            {
                "candidates": [
                    {
                        "content": {"parts": [{"text": content}]},
                    }
                ]
            }
        )

        self.assertEqual(chat_completion("Trả JSON"), content)
        request = urlopen_mock.call_args.args[0]
        body = json.loads(request.data.decode())
        self.assertEqual(
            request.full_url,
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        )
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(body["contents"][0]["parts"][0]["text"], "Trả JSON")
        self.assertEqual(request.headers["X-goog-api-key"], "test-key")

    @override_settings(GEMINI_API_KEY="")
    def test_missing_key_raises_not_configured(self):
        with self.assertRaises(GeminiError) as error:
            chat_completion("Trả JSON")
        self.assertEqual(error.exception.code, "NOT_CONFIGURED")


class AIDataMixin:
    def setUp(self):
        self.manager = User.objects.create_user(email="aimanager@example.com", password="pass", full_name="Manager", role=User.Role.MANAGER)
        self.receptionist = User.objects.create_user(email="aireception@example.com", password="pass", full_name="Reception", role=User.Role.RECEPTIONIST)
        self.accountant = User.objects.create_user(email="aiaccountant@example.com", password="pass", full_name="Accountant", role=User.Role.ACCOUNTANT)
        self.customer_user = User.objects.create_user(email="aicustomer@example.com", password="pass", full_name="Customer", role=User.Role.CUSTOMER)
        self.customer = Customer.objects.create(user=self.customer_user, full_name="Nguyễn Văn A", email="a@example.com", identity_document="CCCD-SECRET-123")
        room_type = RoomType.objects.create(name="AI Deluxe", capacity=2, price_per_night=900_000, amenities=["WiFi"])
        self.room = Room.objects.create(room_number="AI01", room_type=room_type, floor=1)
        self.booking = Booking.objects.create(customer=self.customer, room=self.room, created_by=self.receptionist, check_in_date=date.today() + timedelta(days=1), check_out_date=date.today() + timedelta(days=3), guest_count=1, room_price_per_night=900_000, status=Booking.Status.CONFIRMED)


class RoomAdvisorTests(AIDataMixin, TestCase):
    @patch("apps.ai_integration.services.chat_completion")
    def test_invalid_room_from_ai_is_removed_and_fallback_is_used(self, chat):
        chat.return_value = json.dumps({"suggestions": [{"room_id": 999, "room_number": "FAKE", "reason": "Sai"}]})
        suggestions, status = advise_rooms(user=self.customer_user, needs="Phòng yên tĩnh", rooms=[self.room])
        self.assertEqual(status, AILog.Status.FALLBACK)
        self.assertEqual([item["room_id"] for item in suggestions], [self.room.pk])
        self.assertNotIn(999, [item["room_id"] for item in suggestions])

    @patch("apps.ai_integration.services.chat_completion", side_effect=GeminiError("TIMEOUT"))
    def test_timeout_keeps_normal_room_results(self, _chat):
        suggestions, status = advise_rooms(user=self.customer_user, needs="", rooms=[self.room])
        self.assertEqual(status, AILog.Status.FALLBACK)
        self.assertEqual(suggestions[0]["room_number"], "AI01")
        self.assertEqual(AILog.objects.latest("created_at").error_code, "TIMEOUT")

    @patch("apps.ai_integration.services.chat_completion")
    def test_valid_ai_output_is_allow_listed(self, chat):
        chat.return_value = json.dumps({"suggestions": [{"room_id": self.room.pk, "room_number": "AI01", "reason": "Đúng ngân sách"}]})
        suggestions, status = advise_rooms(user=self.customer_user, needs="", rooms=[self.room])
        self.assertEqual(status, AILog.Status.SUCCESS)
        self.assertEqual(suggestions[0]["room_id"], self.room.pk)


class EmailAITests(AIDataMixin, TestCase):
    @patch("apps.ai_integration.services.chat_completion", side_effect=GeminiError("HTTP_429"))
    def test_email_fallback_creates_editable_draft(self, _chat):
        draft, status = generate_email_draft(actor=self.receptionist, booking=self.booking, email_type=EmailDraft.EmailType.CONFIRMATION)
        self.assertEqual(status, AILog.Status.FALLBACK)
        self.assertFalse(draft.generated_by_ai)
        self.assertIn(self.booking.booking_code, draft.subject)

    @patch("apps.ai_integration.services.chat_completion")
    def test_email_prompt_excludes_identity_and_payment_secrets(self, chat):
        chat.return_value = json.dumps({"subject": "Xác nhận", "body": "Nội dung"})
        generate_email_draft(actor=self.receptionist, booking=self.booking, email_type=EmailDraft.EmailType.CONFIRMATION)
        prompt = chat.call_args.args[0]
        self.assertNotIn("CCCD-SECRET-123", prompt)
        self.assertNotIn("password", prompt.lower())
        self.assertNotIn("api_key", prompt.lower())
        self.assertNotIn("session", prompt.lower())

    def test_accountant_cannot_generate_confirmation_email(self):
        self.client.force_login(self.accountant)
        response = self.client.post(reverse("ai-integration:email-generate", args=[self.booking.pk]), {"email_type": EmailDraft.EmailType.CONFIRMATION})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EmailDraft.objects.exists())

    def test_manager_can_open_email_generator(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("ai-integration:email-generate", args=[self.booking.pk]))
        self.assertEqual(response.status_code, 200)


class ReportAITests(AIDataMixin, TestCase):
    @patch("apps.ai_integration.services.chat_completion")
    def test_report_sends_only_aggregated_data_and_limits_promotions(self, chat):
        chat.return_value = json.dumps({"comment": "Ổn", "trends": ["Tăng"], "warnings": [], "promotions": ["A", "B", "C", "D"]})
        report = {"start_date": date.today(), "end_date": date.today(), "occupancy": {"rate": 50}, "revenue": Decimal("1000000"), "booking_count": 2, "cancellation_rate": 0, "top_room_type": {"room__room_type__name": "AI Deluxe"}, "top_service": None}
        result, status = analyze_report(user=self.manager, report=report)
        self.assertEqual(status, AILog.Status.SUCCESS)
        self.assertEqual(len(result["promotions"]), 3)
        prompt = chat.call_args.args[0]
        self.assertNotIn(self.customer.full_name, prompt)
        self.assertNotIn(self.customer.identity_document, prompt)

    @patch("apps.ai_integration.services.chat_completion", side_effect=GeminiError("TIMEOUT"))
    def test_report_timeout_returns_fallback_without_changing_numbers(self, _chat):
        report = {"start_date": date.today(), "end_date": date.today(), "occupancy": {"rate": 25}, "revenue": Decimal("500000"), "booking_count": 1, "cancellation_rate": 0, "top_room_type": None, "top_service": None}
        result, status = analyze_report(user=self.manager, report=report)
        self.assertEqual(status, AILog.Status.FALLBACK)
        self.assertIn("Số liệu gốc", result["comment"])
        self.assertEqual(report["revenue"], Decimal("500000"))

    def test_only_manager_and_accountant_can_open_ai_report(self):
        url = reverse("ai-integration:report")
        for user, expected in ((self.manager, 200), (self.accountant, 200), (self.receptionist, 403), (self.customer_user, 403)):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, expected)
            self.client.logout()
