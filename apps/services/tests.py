from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType

from .models import Service
from .services import add_booking_service


User = get_user_model()


class BookingServiceTests(TestCase):
    def setUp(self):
        self.receptionist = User.objects.create_user(email="service-rec@example.com", password="x", full_name="Lễ tân", role=User.Role.RECEPTIONIST)
        self.manager = User.objects.create_user(email="service-manager@example.com", password="x", full_name="Quản lý", role=User.Role.MANAGER)
        customer = Customer.objects.create(full_name="Khách dịch vụ")
        room_type = RoomType.objects.create(name="Service Room", capacity=2, price_per_night=800000)
        room = Room.objects.create(room_number="S101", room_type=room_type, floor=1, status=Room.Status.OCCUPIED)
        self.booking = Booking.objects.create(customer=customer, room=room, check_in_date=date(2028, 1, 1), check_out_date=date(2028, 1, 3), guest_count=1, room_price_per_night=800000, status=Booking.Status.CHECKED_IN)
        self.service = Service.objects.create(name="Giặt ủi", unit_price=Decimal("50000"), unit="kg")

    def test_line_total_and_unit_price_are_snapshotted(self):
        item = add_booking_service(actor=self.receptionist, booking=self.booking, service=self.service, quantity=Decimal("2.5"), used_at=date(2028, 1, 2))
        self.assertEqual(item.unit_price, Decimal("50000"))
        self.assertEqual(item.line_total, Decimal("125000.0"))
        self.service.unit_price = 70000
        self.service.save(update_fields=["unit_price"])
        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal("50000"))

    def test_only_checked_in_booking_accepts_service(self):
        self.booking.status = Booking.Status.CONFIRMED
        self.booking.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            add_booking_service(actor=self.receptionist, booking=self.booking, service=self.service, quantity=1, used_at=date(2028, 1, 2))

    def test_manager_can_record_used_service(self):
        item = add_booking_service(actor=self.manager, booking=self.booking, service=self.service, quantity=1, used_at=date(2028, 1, 2))
        self.assertEqual(item.recorded_by, self.manager)
