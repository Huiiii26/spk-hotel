from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Room, RoomType


User = get_user_model()


class RoomModelTests(TestCase):
    def test_room_type_rejects_invalid_capacity(self):
        room_type = RoomType(name="Sai", capacity=0, price_per_night=Decimal("500000"))
        with self.assertRaises(ValidationError):
            room_type.full_clean()

    def test_room_status_is_separate_from_future_availability(self):
        room_type = RoomType.objects.create(name="Standard", capacity=2, price_per_night=500000)
        room = Room.objects.create(
            room_number="101",
            room_type=room_type,
            floor=1,
            status=Room.Status.CLEANING,
        )
        self.assertEqual(room.status, Room.Status.CLEANING)
        self.assertTrue(room.is_active)


class PublicRoomTypeTests(TestCase):
    def setUp(self):
        self.active = RoomType.objects.create(
            name="Deluxe",
            capacity=2,
            price_per_night=Decimal("850000"),
            amenities=["Wi-Fi", "Bồn tắm"],
        )
        self.inactive = RoomType.objects.create(
            name="Ẩn",
            capacity=1,
            price_per_night=Decimal("300000"),
            is_active=False,
        )

    def test_public_list_only_displays_active_room_types(self):
        response = self.client.get(reverse("rooms:public-room-type-list"))
        self.assertContains(response, "Deluxe")
        self.assertNotContains(response, "Ẩn")

    def test_inactive_room_type_detail_returns_404(self):
        response = self.client.get(
            reverse("rooms:public-room-type-detail", args=[self.inactive.pk])
        )
        self.assertEqual(response.status_code, 404)


class RoomManagementPermissionTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            email="manager.rooms@example.com",
            password="SafePass2026!",
            full_name="Quản lý phòng",
            role=User.Role.MANAGER,
        )
        self.receptionist = User.objects.create_user(
            email="reception.rooms@example.com",
            password="SafePass2026!",
            full_name="Lễ tân",
            role=User.Role.RECEPTIONIST,
        )
        self.room_type = RoomType.objects.create(
            name="Standard",
            capacity=2,
            price_per_night=Decimal("500000"),
        )

    def test_receptionist_can_view_rooms_but_cannot_create_or_edit(self):
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse("rooms-staff:room-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("rooms-staff:room-create")).status_code, 403)

    def test_manager_can_create_room_type_with_normalized_amenities(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("rooms-staff:room-type-create"),
            {
                "name": "Suite",
                "description": "Phòng rộng",
                "capacity": 4,
                "price_per_night": 1500000,
                "amenities_text": "Wi-Fi, Bồn tắm, wi-fi",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("rooms-staff:room-type-list"))
        self.assertEqual(RoomType.objects.get(name="Suite").amenities, ["Wi-Fi", "Bồn tắm"])

    def test_manager_can_create_room(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("rooms-staff:room-create"),
            {
                "room_number": "301",
                "room_type": self.room_type.pk,
                "floor": 3,
                "status": Room.Status.AVAILABLE,
                "notes": "",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("rooms-staff:room-list"))
        self.assertTrue(Room.objects.filter(room_number="301").exists())
