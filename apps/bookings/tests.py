from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType

from .forms import AvailabilitySearchForm
from .models import Booking
from .services import (
    cancel_booking,
    check_in_booking,
    check_out_booking,
    confirm_booking,
    create_booking,
    find_available_rooms,
    mark_room_available_after_cleaning,
)


User = get_user_model()


class BookingFixtureMixin:
    @classmethod
    def setUpTestData(cls):
        cls.customer_user = User.objects.create_user(
            email="booking-owner@example.com",
            password="SafePass2026!",
            full_name="Khách đặt phòng",
            role=User.Role.CUSTOMER,
        )
        cls.other_user = User.objects.create_user(
            email="booking-other@example.com",
            password="SafePass2026!",
            full_name="Khách khác",
            role=User.Role.CUSTOMER,
        )
        cls.receptionist = User.objects.create_user(
            email="booking-reception@example.com",
            password="SafePass2026!",
            full_name="Lễ tân",
            role=User.Role.RECEPTIONIST,
        )
        cls.manager = User.objects.create_user(
            email="booking-manager@example.com",
            password="SafePass2026!",
            full_name="Quản lý",
            role=User.Role.MANAGER,
        )
        cls.accountant = User.objects.create_user(
            email="booking-accountant@example.com",
            password="SafePass2026!",
            full_name="Kế toán",
            role=User.Role.ACCOUNTANT,
        )
        cls.customer = Customer.objects.create(
            user=cls.customer_user,
            full_name="Khách đặt phòng",
            email="booking-owner@example.com",
        )
        cls.other_customer = Customer.objects.create(
            user=cls.other_user,
            full_name="Khách khác",
            email="booking-other@example.com",
        )
        cls.room_type = RoomType.objects.create(
            name="Deluxe Booking",
            capacity=2,
            price_per_night=Decimal("1500000"),
            amenities=["WiFi", "Điều hòa", "Ban công"],
        )
        cls.room = Room.objects.create(
            room_number="B401",
            room_type=cls.room_type,
            floor=4,
        )
        cls.second_room = Room.objects.create(
            room_number="B402",
            room_type=cls.room_type,
            floor=4,
        )


class AvailabilityTests(BookingFixtureMixin, TestCase):
    def test_invalid_date_range_is_rejected(self):
        form = AvailabilitySearchForm(
            {"check_in_date": "2027-05-10", "check_out_date": "2027-05-10", "guest_count": 1}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("check_out_date", form.errors)

    def test_overlap_formula_excludes_booked_room(self):
        Booking.objects.create(
            customer=self.customer,
            room=self.room,
            created_by=self.customer_user,
            check_in_date=date(2027, 5, 10),
            check_out_date=date(2027, 5, 15),
            guest_count=2,
            room_price_per_night=self.room_type.price_per_night,
            status=Booking.Status.CONFIRMED,
        )
        rooms = find_available_rooms(
            check_in_date=date(2027, 5, 14),
            check_out_date=date(2027, 5, 18),
            guest_count=2,
        )
        self.assertNotIn(self.room, rooms)
        self.assertIn(self.second_room, rooms)

    def test_checkout_boundary_does_not_overlap_next_booking(self):
        Booking.objects.create(
            customer=self.customer,
            room=self.room,
            check_in_date=date(2027, 5, 10),
            check_out_date=date(2027, 5, 15),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
            status=Booking.Status.CONFIRMED,
        )
        rooms = find_available_rooms(
            check_in_date=date(2027, 5, 15),
            check_out_date=date(2027, 5, 17),
            guest_count=1,
        )
        self.assertIn(self.room, rooms)

    def test_cancelled_booking_does_not_block_room(self):
        Booking.objects.create(
            customer=self.customer,
            room=self.room,
            check_in_date=date(2027, 6, 1),
            check_out_date=date(2027, 6, 4),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
            status=Booking.Status.CANCELLED,
        )
        rooms = find_available_rooms(
            check_in_date=date(2027, 6, 2),
            check_out_date=date(2027, 6, 3),
            guest_count=1,
        )
        self.assertIn(self.room, rooms)

    def test_checked_out_booking_still_blocks_its_historical_date_range(self):
        Booking.objects.create(
            customer=self.customer,
            room=self.room,
            check_in_date=date(2027, 6, 10),
            check_out_date=date(2027, 6, 12),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
            status=Booking.Status.CHECKED_OUT,
        )
        rooms = find_available_rooms(
            check_in_date=date(2027, 6, 11),
            check_out_date=date(2027, 6, 12),
            guest_count=1,
        )
        self.assertNotIn(self.room, rooms)

    def test_capacity_budget_amenities_and_maintenance_filters(self):
        self.second_room.status = Room.Status.MAINTENANCE
        self.second_room.save(update_fields=["status"])
        rooms = find_available_rooms(
            check_in_date=date(2027, 7, 1),
            check_out_date=date(2027, 7, 3),
            guest_count=2,
            max_budget=Decimal("1600000"),
            amenities=["wifi", "BAN CÔNG"],
        )
        self.assertEqual(rooms, [self.room])


class BookingCreationTests(BookingFixtureMixin, TestCase):
    def test_customer_booking_is_pending_and_snapshots_price(self):
        booking = create_booking(
            actor=self.customer_user,
            customer=self.customer,
            room=self.room,
            check_in_date=date(2027, 8, 1),
            check_out_date=date(2027, 8, 3),
            guest_count=2,
        )
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.room_price_per_night, Decimal("1500000"))
        self.room_type.price_per_night = Decimal("2000000")
        self.room_type.save(update_fields=["price_per_night"])
        booking.refresh_from_db()
        self.assertEqual(booking.room_price_per_night, Decimal("1500000"))

    def test_receptionist_booking_is_confirmed(self):
        booking = create_booking(
            actor=self.receptionist,
            customer=self.customer,
            room=self.room,
            check_in_date=date(2027, 8, 5),
            check_out_date=date(2027, 8, 7),
            guest_count=1,
        )
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_backend_rechecks_overlap_before_create(self):
        data = {
            "actor": self.customer_user,
            "customer": self.customer,
            "room": self.room,
            "check_in_date": date(2027, 9, 1),
            "check_out_date": date(2027, 9, 4),
            "guest_count": 1,
        }
        create_booking(**data)
        with self.assertRaises(ValidationError):
            create_booking(**data)
        self.assertEqual(Booking.objects.count(), 1)

    def test_service_requests_room_row_lock(self):
        with patch(
            "apps.bookings.services.Room.objects.select_for_update",
            wraps=Room.objects.select_for_update,
        ) as row_lock:
            create_booking(
                actor=self.customer_user,
                customer=self.customer,
                room=self.room,
                check_in_date=date(2027, 10, 1),
                check_out_date=date(2027, 10, 2),
                guest_count=1,
            )
        row_lock.assert_called_once_with()

    def test_customer_cannot_create_booking_for_someone_else(self):
        with self.assertRaises(PermissionDenied):
            create_booking(
                actor=self.customer_user,
                customer=self.other_customer,
                room=self.room,
                check_in_date=date(2027, 11, 1),
                check_out_date=date(2027, 11, 2),
                guest_count=1,
            )


class BookingStateTransitionTests(BookingFixtureMixin, TestCase):
    def make_booking(self, status, room=None):
        return Booking.objects.create(
            customer=self.customer,
            room=room or self.room,
            created_by=self.customer_user,
            check_in_date=date(2028, 5, 1),
            check_out_date=date(2028, 5, 3),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
            status=status,
        )

    def test_receptionist_can_confirm_pending_booking(self):
        booking = self.make_booking(Booking.Status.PENDING)
        confirmed = confirm_booking(actor=self.receptionist, booking=booking)
        self.assertEqual(confirmed.status, Booking.Status.CONFIRMED)

    def test_confirm_from_wrong_status_is_rejected(self):
        booking = self.make_booking(Booking.Status.CONFIRMED)
        with self.assertRaises(ValidationError):
            confirm_booking(actor=self.receptionist, booking=booking)

    def test_check_in_updates_booking_time_and_room_status(self):
        booking = self.make_booking(Booking.Status.CONFIRMED)
        checked_in = check_in_booking(actor=self.receptionist, booking=booking)
        self.room.refresh_from_db()
        self.assertEqual(checked_in.status, Booking.Status.CHECKED_IN)
        self.assertIsNotNone(checked_in.actual_check_in_at)
        self.assertEqual(self.room.status, Room.Status.OCCUPIED)

    def test_check_in_pending_or_cancelled_booking_is_rejected(self):
        pending = self.make_booking(Booking.Status.PENDING)
        with self.assertRaises(ValidationError):
            check_in_booking(actor=self.receptionist, booking=pending)
        pending.status = Booking.Status.CANCELLED
        pending.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            check_in_booking(actor=self.receptionist, booking=pending)

    def test_check_out_updates_booking_and_moves_room_to_cleaning(self):
        self.room.status = Room.Status.OCCUPIED
        self.room.save(update_fields=["status"])
        booking = self.make_booking(Booking.Status.CHECKED_IN)
        checked_out = check_out_booking(actor=self.receptionist, booking=booking)
        self.room.refresh_from_db()
        self.assertEqual(checked_out.status, Booking.Status.CHECKED_OUT)
        self.assertIsNotNone(checked_out.actual_check_out_at)
        self.assertEqual(self.room.status, Room.Status.CLEANING)

    def test_check_out_from_wrong_status_is_rejected(self):
        booking = self.make_booking(Booking.Status.CONFIRMED)
        with self.assertRaises(ValidationError):
            check_out_booking(actor=self.receptionist, booking=booking)

    def test_customer_can_cancel_own_booking_before_check_in(self):
        booking = self.make_booking(Booking.Status.PENDING)
        cancelled = cancel_booking(
            actor=self.customer_user,
            booking=booking,
            reason="Thay đổi lịch trình",
        )
        self.assertEqual(cancelled.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(cancelled.cancelled_at)
        self.assertEqual(cancelled.cancellation_reason, "Thay đổi lịch trình")

    def test_customer_cannot_cancel_another_booking(self):
        booking = self.make_booking(Booking.Status.PENDING)
        with self.assertRaises(PermissionDenied):
            cancel_booking(actor=self.other_user, booking=booking)

    def test_checked_in_booking_cannot_be_cancelled(self):
        booking = self.make_booking(Booking.Status.CHECKED_IN)
        with self.assertRaises(ValidationError):
            cancel_booking(actor=self.receptionist, booking=booking)

    def test_manager_can_confirm_check_in_and_check_out(self):
        booking = self.make_booking(Booking.Status.PENDING)
        booking = confirm_booking(actor=self.manager, booking=booking)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        booking = check_in_booking(actor=self.manager, booking=booking)
        self.assertEqual(booking.status, Booking.Status.CHECKED_IN)
        booking = check_out_booking(actor=self.manager, booking=booking)
        self.assertEqual(booking.status, Booking.Status.CHECKED_OUT)

    def test_receptionist_marks_cleaning_room_available(self):
        self.room.status = Room.Status.CLEANING
        self.room.save(update_fields=["status"])
        room = mark_room_available_after_cleaning(actor=self.receptionist, room=self.room)
        self.assertEqual(room.status, Room.Status.AVAILABLE)

    def test_non_cleaning_room_cannot_be_marked_available(self):
        with self.assertRaises(ValidationError):
            mark_room_available_after_cleaning(actor=self.receptionist, room=self.room)


class BookingViewPermissionTests(BookingFixtureMixin, TestCase):
    def setUp(self):
        self.booking = Booking.objects.create(
            customer=self.other_customer,
            room=self.room,
            created_by=self.other_user,
            check_in_date=date(2027, 12, 1),
            check_out_date=date(2027, 12, 3),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
        )

    def test_customer_cannot_view_another_customers_booking(self):
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse("customer-bookings:detail", args=[self.booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_customer_can_create_and_view_own_booking(self):
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("customer-bookings:create"),
            {
                "room": self.second_room.pk,
                "check_in_date": "2028-02-01",
                "check_out_date": "2028-02-03",
                "guest_count": 2,
                "notes": "Gần thang máy",
            },
        )
        own_booking = Booking.objects.get(customer=self.customer)
        self.assertRedirects(response, reverse("customer-bookings:detail", args=[own_booking.pk]))
        self.assertEqual(own_booking.status, Booking.Status.PENDING)
        self.assertEqual(
            self.client.get(reverse("customer-bookings:detail", args=[own_booking.pk])).status_code,
            200,
        )

    def test_public_can_search_available_rooms(self):
        response = self.client.get(
            reverse("bookings:availability-search"),
            {
                "check_in_date": "2028-03-01",
                "check_out_date": "2028-03-03",
                "guest_count": 2,
                "max_budget": "1600000",
                "amenities": "WiFi, Ban công",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.room_number)

    def test_receptionist_can_create_confirmed_booking_for_customer(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            reverse("bookings-staff:create"),
            {
                "customer": self.customer.pk,
                "room": self.second_room.pk,
                "check_in_date": "2028-04-01",
                "check_out_date": "2028-04-02",
                "guest_count": 1,
                "notes": "Khách gọi điện",
            },
        )
        created = Booking.objects.get(customer=self.customer)
        self.assertRedirects(response, reverse("bookings-staff:detail", args=[created.pk]))
        self.assertEqual(created.status, Booking.Status.CONFIRMED)

    def test_accountant_cannot_create_or_list_booking(self):
        self.client.force_login(self.accountant)
        self.assertEqual(self.client.get(reverse("bookings-staff:list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("bookings-staff:create")).status_code, 403)

    def test_manager_can_list_and_create_booking(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("bookings-staff:list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("bookings-staff:create")).status_code, 200)

    def test_receptionist_can_run_full_confirm_checkin_checkout_flow(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(reverse("bookings-staff:confirm", args=[self.booking.pk]))
        self.assertRedirects(response, reverse("bookings-staff:detail", args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

        self.client.post(reverse("bookings-staff:check-in", args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.room.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CHECKED_IN)
        self.assertEqual(self.room.status, Room.Status.OCCUPIED)

        self.client.post(reverse("bookings-staff:check-out", args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.room.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CHECKED_OUT)
        self.assertEqual(self.room.status, Room.Status.CLEANING)

        self.client.post(
            reverse("bookings-staff:room-mark-available", args=[self.room.pk]),
            {"next": reverse("rooms-staff:room-list")},
        )
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.AVAILABLE)

    def test_transition_endpoints_only_accept_post_and_allow_manager(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(
            self.client.get(reverse("bookings-staff:confirm", args=[self.booking.pk])).status_code,
            405,
        )
        self.client.force_login(self.manager)
        self.assertEqual(
            self.client.post(reverse("bookings-staff:confirm", args=[self.booking.pk])).status_code,
            302,
        )

    def test_customer_cancel_endpoint_checks_ownership(self):
        self.client.force_login(self.customer_user)
        self.assertEqual(
            self.client.post(reverse("customer-bookings:cancel", args=[self.booking.pk])).status_code,
            404,
        )
        own_booking = Booking.objects.create(
            customer=self.customer,
            room=self.second_room,
            created_by=self.customer_user,
            check_in_date=date(2028, 6, 1),
            check_out_date=date(2028, 6, 3),
            guest_count=1,
            room_price_per_night=self.room_type.price_per_night,
        )
        self.client.post(
            reverse("customer-bookings:cancel", args=[own_booking.pk]),
            {"reason": "Không thể đi"},
        )
        own_booking.refresh_from_db()
        self.assertEqual(own_booking.status, Booking.Status.CANCELLED)

    def test_room_calendar_permissions(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("bookings-staff:calendar")).status_code, 200)
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(reverse("bookings-staff:calendar")).status_code, 200)
        self.client.force_login(self.accountant)
        self.assertEqual(self.client.get(reverse("bookings-staff:calendar")).status_code, 403)


@skipUnless(connection.vendor == "postgresql", "Kiểm thử đồng thời cần PostgreSQL và row-level lock.")
class ConcurrentBookingTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            email="concurrent@example.com",
            password="SafePass2026!",
            full_name="Khách đồng thời",
            role=User.Role.CUSTOMER,
        )
        self.customer = Customer.objects.create(user=self.user, full_name="Khách đồng thời")
        room_type = RoomType.objects.create(name="Concurrency", capacity=2, price_per_night=900000)
        self.room = Room.objects.create(room_number="C101", room_type=room_type, floor=1)

    def _book(self):
        close_old_connections()
        try:
            create_booking(
                actor=User.objects.get(pk=self.user.pk),
                customer=Customer.objects.get(pk=self.customer.pk),
                room=Room.objects.get(pk=self.room.pk),
                check_in_date=date(2028, 1, 1),
                check_out_date=date(2028, 1, 3),
                guest_count=1,
            )
            return "created"
        except ValidationError:
            return "rejected"
        finally:
            close_old_connections()

    def test_two_simultaneous_requests_only_create_one_booking(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self._book(), range(2)))
        self.assertCountEqual(results, ["created", "rejected"])
        self.assertEqual(Booking.objects.count(), 1)
