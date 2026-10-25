from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking
from apps.billing.models import Payment
from apps.billing.services import create_or_update_invoice
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType
from apps.services.models import BookingService, Service
from apps.ai_integration.models import AILog, EmailDraft


User = get_user_model()
DEFAULT_DEMO_PASSWORD = "Demo@12345"
STAFF_DEMO_PASSWORD = "1"


class Command(BaseCommand):
    help = "Tạo hoặc cập nhật dữ liệu mẫu để trình diễn SPK Hotel."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._seed_users()
        customers = self._seed_customers(users)
        room_types = self._seed_room_types()
        rooms = self._seed_rooms(room_types)
        bookings = self._seed_bookings(users, customers, rooms)
        services = self._seed_services()
        self._seed_used_services(users, bookings, services)
        self._seed_invoices_and_payments(users, bookings)
        self._seed_ai_examples(users, bookings)

        lines = [
            "Đã tạo/cập nhật dữ liệu demo SPK Hotel.",
            "Quy mô: 4 loại phòng, 26 phòng, 11 khách hàng và 20 booking mẫu.",
            "Tài khoản demo:",
            "  Quản lý: quanli@hotel.com / 1",
            "  Lễ tân: letan@hotel.com / 1",
            "  Kế toán: ketoan@hotel.com / 1",
            "  Khách: customer1@spkhotel.vn / Demo@12345",
        ]
        try:
            for index, line in enumerate(lines):
                self.stdout.write(self.style.SUCCESS(line) if index == 0 else line)
        except UnicodeEncodeError:
            self.stdout.write("Da tao/cap nhat du lieu demo SPK Hotel.")

    def _upsert_user(
        self,
        *,
        email,
        full_name,
        phone,
        role,
        password=DEFAULT_DEMO_PASSWORD,
        previous_email=None,
    ):
        user = User.objects.filter(email=email).first()
        if user is None and previous_email:
            user = User.objects.filter(email=previous_email).first()
            if user is not None:
                user.email = email
        if user is None:
            user = User(email=email, full_name=full_name)
        user.full_name = full_name
        user.phone = phone
        user.role = role
        user.is_active = True
        user.is_staff = role == User.Role.MANAGER
        user.set_password(password)
        user.save()
        return user

    def _seed_users(self):
        definitions = {
            "manager": ("quanli@hotel.com", "Nguyễn Quốc Bảo", "0901000001", User.Role.MANAGER, STAFF_DEMO_PASSWORD, "manager@spkhotel.vn"),
            "receptionist": ("letan@hotel.com", "Trần Gia Hân", "0901000002", User.Role.RECEPTIONIST, STAFF_DEMO_PASSWORD, "receptionist@spkhotel.vn"),
            "accountant": ("ketoan@hotel.com", "Lê Minh Anh", "0901000003", User.Role.ACCOUNTANT, STAFF_DEMO_PASSWORD, "accountant@spkhotel.vn"),
            "customer1": ("customer1@spkhotel.vn", "Lê Thị Ngọc Mai", "0911000001", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
            "customer2": ("customer2@spkhotel.vn", "Nguyễn Văn An", "0911000002", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
            "customer3": ("customer3@spkhotel.vn", "Phạm Thu Trang", "0911000003", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
            "customer4": ("customer4@spkhotel.vn", "Vũ Hoàng Nam", "0911000004", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
            "customer5": ("customer5@spkhotel.vn", "Đặng Minh Châu", "0911000005", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
            "customer6": ("customer6@spkhotel.vn", "Bùi Anh Tú", "0911000006", User.Role.CUSTOMER, DEFAULT_DEMO_PASSWORD, None),
        }
        return {
            key: self._upsert_user(
                email=email,
                full_name=name,
                phone=phone,
                role=role,
                password=password,
                previous_email=previous_email,
            )
            for key, (email, name, phone, role, password, previous_email) in definitions.items()
        }

    def _seed_customers(self, users):
        customers = {}
        linked_definitions = {
            "customer1": ("Thái Nguyên", "Khách đặt qua website"),
            "customer2": ("Bắc Kạn", "Ưu tiên phòng yên tĩnh"),
            "customer3": ("Hà Nội", "Khách hàng thân thiết"),
            "customer4": ("Hải Phòng", "Ưu tiên phòng tầng cao"),
            "customer5": ("Quảng Ninh", "Thường đặt phòng công tác"),
            "customer6": ("Bắc Giang", "Khách gia đình"),
        }
        for key, (address, notes) in linked_definitions.items():
            user = users[key]
            customer, _ = Customer.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "address": address,
                    "notes": notes,
                },
            )
            customers[key] = customer

        customers["walkin1"], _ = Customer.objects.update_or_create(
            user=None,
            email="walkin1@demo.local",
            defaults={
                "full_name": "Hoàng Minh Đức",
                "phone": "0922000001",
                "address": "Tuyên Quang",
                "notes": "Khách do lễ tân nhập",
            },
        )
        customers["walkin2"], _ = Customer.objects.update_or_create(
            user=None,
            email="walkin2@demo.local",
            defaults={
                "full_name": "Đỗ Hải Yến",
                "phone": "0922000002",
                "address": "Cao Bằng",
                "notes": "Khách chưa có tài khoản website",
            },
        )
        walkin_definitions = {
            "walkin3": ("Ngô Quang Huy", "0922000003", "Lạng Sơn", "Khách đặt trực tiếp tại quầy"),
            "walkin4": ("Trịnh Hà My", "0922000004", "Hà Nam", "Khách đoàn công tác"),
            "walkin5": ("Phan Đức Long", "0922000005", "Ninh Bình", "Yêu cầu xuất hóa đơn"),
        }
        for key, (full_name, phone, address, notes) in walkin_definitions.items():
            customers[key], _ = Customer.objects.update_or_create(
                user=None,
                email=f"{key}@demo.local",
                defaults={
                    "full_name": full_name,
                    "phone": phone,
                    "address": address,
                    "notes": notes,
                },
            )
        return customers

    def _seed_room_types(self):
        definitions = {
            "standard": {
                "name": "Standard",
                "description": "Phòng tiêu chuẩn ấm cúng, phù hợp chuyến công tác hoặc nghỉ ngắn ngày.",
                "capacity": 2,
                "price_per_night": Decimal("650000"),
                "price_per_hour": Decimal("100000"),
                "amenities": ["WiFi", "Điều hòa", "TV"],
                "is_active": True,
            },
            "deluxe": {
                "name": "Deluxe",
                "description": "Phòng rộng rãi có ban công và tầm nhìn đẹp.",
                "capacity": 3,
                "price_per_night": Decimal("1200000"),
                "price_per_hour": Decimal("180000"),
                "amenities": ["WiFi", "Điều hòa", "TV", "Ban công", "Minibar"],
                "is_active": True,
            },
            "family": {
                "name": "Family Suite",
                "description": "Phòng gia đình có không gian sinh hoạt riêng và hai giường lớn.",
                "capacity": 5,
                "price_per_night": Decimal("2000000"),
                "price_per_hour": Decimal("300000"),
                "amenities": ["WiFi", "Điều hòa", "TV", "Bồn tắm", "Bếp nhỏ"],
                "is_active": True,
            },
            "executive": {
                "name": "Executive Suite",
                "description": "Phòng cao cấp dành cho khách công tác, có khu làm việc và phòng khách riêng.",
                "capacity": 4,
                "price_per_night": Decimal("2800000"),
                "price_per_hour": Decimal("420000"),
                "amenities": ["WiFi", "Điều hòa", "Smart TV", "Bồn tắm", "Minibar", "Bàn làm việc"],
                "is_active": True,
            },
        }
        result = {}
        for key, values in definitions.items():
            room_type, _ = RoomType.objects.update_or_create(name=values["name"], defaults=values)
            result[key] = room_type
        return result

    def _seed_rooms(self, room_types):
        definitions = [
            ("101", "standard", 1, Room.Status.AVAILABLE),
            ("102", "standard", 1, Room.Status.AVAILABLE),
            ("103", "standard", 1, Room.Status.AVAILABLE),
            ("104", "standard", 1, Room.Status.AVAILABLE),
            ("105", "standard", 1, Room.Status.AVAILABLE),
            ("106", "standard", 1, Room.Status.AVAILABLE),
            ("201", "deluxe", 2, Room.Status.AVAILABLE),
            ("202", "deluxe", 2, Room.Status.AVAILABLE),
            ("203", "deluxe", 2, Room.Status.CLEANING),
            ("204", "deluxe", 2, Room.Status.OCCUPIED),
            ("205", "deluxe", 2, Room.Status.AVAILABLE),
            ("206", "deluxe", 2, Room.Status.AVAILABLE),
            ("301", "family", 3, Room.Status.OCCUPIED),
            ("302", "family", 3, Room.Status.AVAILABLE),
            ("303", "family", 3, Room.Status.MAINTENANCE),
            ("304", "family", 3, Room.Status.AVAILABLE),
            ("305", "family", 3, Room.Status.AVAILABLE),
            ("306", "family", 3, Room.Status.AVAILABLE),
            ("401", "executive", 4, Room.Status.AVAILABLE),
            ("402", "executive", 4, Room.Status.AVAILABLE),
            ("403", "executive", 4, Room.Status.AVAILABLE),
            ("404", "executive", 4, Room.Status.CLEANING),
            ("405", "executive", 4, Room.Status.AVAILABLE),
            ("406", "executive", 4, Room.Status.AVAILABLE),
            ("501", "executive", 5, Room.Status.AVAILABLE),
            ("502", "executive", 5, Room.Status.AVAILABLE),
        ]
        result = {}
        for number, type_key, floor, status in definitions:
            room, _ = Room.objects.update_or_create(
                room_number=number,
                defaults={
                    "room_type": room_types[type_key],
                    "floor": floor,
                    "status": status,
                    "is_active": True,
                    "notes": "Dữ liệu mẫu SPK Hotel",
                },
            )
            result[number] = room
        return result

    def _seed_bookings(self, users, customers, rooms):
        today = timezone.localdate()
        definitions = [
            ("DEMO-PENDING", "customer1", "101", 2, 5, 2, Booking.Status.PENDING, users["customer1"]),
            ("DEMO-CONFIRMED", "walkin1", "201", 6, 9, 2, Booking.Status.CONFIRMED, users["receptionist"]),
            ("DEMO-CHECKEDIN", "customer2", "301", -1, 2, 3, Booking.Status.CHECKED_IN, users["receptionist"]),
            ("DEMO-CHECKEDOUT", "customer3", "102", -12, -9, 1, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CANCELLED", "walkin2", "202", 10, 12, 2, Booking.Status.CANCELLED, users["receptionist"]),
            ("DEMO-PENDING-02", "customer4", "105", 4, 6, 2, Booking.Status.PENDING, users["customer4"]),
            ("DEMO-PENDING-03", "customer6", "304", 8, 11, 4, Booking.Status.PENDING, users["customer6"]),
            ("DEMO-CONFIRMED-02", "customer5", "401", 12, 15, 2, Booking.Status.CONFIRMED, users["customer5"]),
            ("DEMO-CONFIRMED-03", "walkin3", "205", 3, 5, 2, Booking.Status.CONFIRMED, users["receptionist"]),
            ("DEMO-CHECKEDIN-02", "walkin4", "204", -1, 1, 2, Booking.Status.CHECKED_IN, users["receptionist"]),
            ("DEMO-CHECKEDOUT-02", "customer4", "103", -22, -20, 2, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-03", "customer5", "203", -35, -32, 1, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-04", "customer6", "302", -48, -44, 4, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-05", "walkin3", "401", -65, -62, 2, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-06", "walkin4", "204", -82, -80, 2, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-07", "walkin5", "402", -110, -106, 3, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-CHECKEDOUT-08", "customer1", "106", -140, -138, 2, Booking.Status.CHECKED_OUT, users["receptionist"]),
            ("DEMO-HOURLY", "customer2", "206", 1, 1, 2, Booking.Status.CONFIRMED, users["customer2"]),
            ("DEMO-CANCELLED-02", "customer5", "405", 18, 21, 2, Booking.Status.CANCELLED, users["customer5"]),
            ("DEMO-CANCELLED-03", "walkin5", "104", -5, -3, 1, Booking.Status.CANCELLED, users["receptionist"]),
        ]
        result = {}
        for code, customer_key, room_number, start, end, guests, status, creator in definitions:
            room = rooms[room_number]
            defaults = {
                "customer": customers[customer_key],
                "room": room,
                "created_by": creator,
                "check_in_date": timezone.make_aware(datetime.combine(today + timedelta(days=start), time(hour=14))),
                "check_out_date": timezone.make_aware(datetime.combine(today + timedelta(days=end), time(hour=12))),
                "guest_count": guests,
                "room_price_per_night": room.room_type.price_per_night,
                "room_price_per_hour": room.room_type.price_per_hour,
                "status": status,
                "notes": "Booking mẫu để trình diễn",
            }
            if code == "DEMO-HOURLY":
                defaults["check_in_date"] = timezone.make_aware(
                    datetime.combine(today + timedelta(days=start), time(hour=9))
                )
                defaults["check_out_date"] = timezone.make_aware(
                    datetime.combine(today + timedelta(days=end), time(hour=14))
                )
            if status == Booking.Status.CHECKED_IN:
                defaults["actual_check_in_at"] = timezone.now()
            if status == Booking.Status.CHECKED_OUT:
                defaults["actual_check_in_at"] = defaults["check_in_date"]
                defaults["actual_check_out_at"] = defaults["check_out_date"]
            if status == Booking.Status.CANCELLED:
                defaults["cancelled_at"] = timezone.now()
                defaults["cancellation_reason"] = "Khách thay đổi kế hoạch"
            booking, _ = Booking.objects.update_or_create(booking_code=code, defaults=defaults)
            result[code] = booking
        return result

    def _seed_services(self):
        definitions = {
            "breakfast": ("Ăn sáng", "Buffet sáng tại nhà hàng", Decimal("120000"), "suất"),
            "laundry": ("Giặt ủi", "Giặt và ủi quần áo", Decimal("50000"), "kg"),
            "airport": ("Đưa đón sân bay", "Xe riêng đưa hoặc đón sân bay", Decimal("450000"), "chuyến"),
            "minibar": ("Minibar", "Đồ uống và đồ ăn nhẹ trong phòng", Decimal("80000"), "phần"),
            "spa": ("Spa thư giãn", "Liệu trình thư giãn 60 phút", Decimal("650000"), "lượt"),
            "dinner": ("Bữa tối", "Set menu tối tại nhà hàng", Decimal("280000"), "suất"),
            "meeting": ("Phòng họp", "Phòng họp và thiết bị trình chiếu", Decimal("900000"), "buổi"),
            "late_checkout": ("Trả phòng muộn", "Gia hạn thời gian trả phòng", Decimal("350000"), "lần"),
        }
        result = {}
        for key, (name, description, price, unit) in definitions.items():
            service, _ = Service.objects.update_or_create(
                name=name,
                defaults={"description": description, "unit_price": price, "unit": unit, "is_active": True},
            )
            result[key] = service
        return result

    def _seed_ai_examples(self, users, bookings):
        AILog.objects.update_or_create(
            user=users["manager"],
            feature=AILog.Feature.REPORT,
            request_summary={"demo": True},
            defaults={
                "status": AILog.Status.FALLBACK,
                "response_summary": {"promotion_count": 0},
                "error_code": "DEMO",
                "duration_ms": 12,
            },
        )
        booking = bookings["DEMO-CONFIRMED"]
        EmailDraft.objects.update_or_create(
            booking=booking,
            email_type=EmailDraft.EmailType.CONFIRMATION,
            defaults={
                "recipient_email": booking.customer.email,
                "subject": f"SPK Hotel - Xác nhận {booking.booking_code}",
                "body": "Kính gửi quý khách, đây là bản nháp email xác nhận mẫu để trình diễn.",
                "status": EmailDraft.Status.DRAFT,
                "generated_by_ai": False,
                "created_by": users["receptionist"],
            },
        )

    def _seed_used_services(self, users, bookings, services):
        today = timezone.localdate()
        definitions = [
            (bookings["DEMO-CHECKEDIN"], services["breakfast"], Decimal("3"), today),
            (bookings["DEMO-CHECKEDOUT"], services["laundry"], Decimal("2"), today - timedelta(days=10)),
            (bookings["DEMO-CHECKEDIN-02"], services["dinner"], Decimal("2"), today),
            (bookings["DEMO-CHECKEDIN-02"], services["minibar"], Decimal("2"), today),
            (bookings["DEMO-CHECKEDOUT-02"], services["airport"], Decimal("1"), today - timedelta(days=21)),
            (bookings["DEMO-CHECKEDOUT-03"], services["spa"], Decimal("1"), today - timedelta(days=34)),
            (bookings["DEMO-CHECKEDOUT-04"], services["breakfast"], Decimal("8"), today - timedelta(days=46)),
            (bookings["DEMO-CHECKEDOUT-05"], services["meeting"], Decimal("1"), today - timedelta(days=64)),
            (bookings["DEMO-CHECKEDOUT-06"], services["laundry"], Decimal("3"), today - timedelta(days=81)),
            (bookings["DEMO-CHECKEDOUT-07"], services["late_checkout"], Decimal("1"), today - timedelta(days=107)),
            (bookings["DEMO-CHECKEDOUT-08"], services["minibar"], Decimal("3"), today - timedelta(days=139)),
        ]
        for booking, service, quantity, used_at in definitions:
            BookingService.objects.update_or_create(
                booking=booking,
                service=service,
                used_at=used_at,
                defaults={
                    "quantity": quantity,
                    "unit_price": service.unit_price,
                    "line_total": quantity * service.unit_price,
                    "recorded_by": users["receptionist"],
                },
            )

    def _seed_invoices_and_payments(self, users, bookings):
        unpaid = create_or_update_invoice(booking=bookings["DEMO-PENDING"])
        partial = create_or_update_invoice(booking=bookings["DEMO-CONFIRMED"])
        paid = create_or_update_invoice(booking=bookings["DEMO-CHECKEDOUT"])
        additional_paid_codes = [
            "DEMO-CHECKEDOUT-02",
            "DEMO-CHECKEDOUT-03",
            "DEMO-CHECKEDOUT-04",
            "DEMO-CHECKEDOUT-05",
            "DEMO-CHECKEDOUT-06",
            "DEMO-CHECKEDOUT-07",
            "DEMO-CHECKEDOUT-08",
        ]

        Payment.objects.update_or_create(
            invoice=partial,
            reference="DEMO-PARTIAL",
            defaults={
                "amount": min(Decimal("500000"), partial.total_amount),
                "method": Payment.Method.BANK_TRANSFER,
                "paid_at": timezone.now(),
                "recorded_by": users["accountant"],
                "notes": "Thanh toán một phần mẫu",
            },
        )
        for index, code in enumerate(additional_paid_codes, start=2):
            invoice = create_or_update_invoice(booking=bookings[code])
            Payment.objects.update_or_create(
                invoice=invoice,
                reference=f"DEMO-PAID-{index:02d}",
                defaults={
                    "amount": invoice.total_amount,
                    "method": [Payment.Method.CASH, Payment.Method.BANK_TRANSFER, Payment.Method.CARD][index % 3],
                    "paid_at": invoice.booking.actual_check_out_at or timezone.now(),
                    "recorded_by": users["accountant"],
                    "notes": "Thanh toán toàn bộ mẫu phục vụ báo cáo doanh thu",
                },
            )
            create_or_update_invoice(booking=invoice.booking)
        Payment.objects.update_or_create(
            invoice=paid,
            reference="DEMO-PAID",
            defaults={
                "amount": paid.total_amount,
                "method": Payment.Method.CARD,
                "paid_at": timezone.now(),
                "recorded_by": users["accountant"],
                "notes": "Thanh toán toàn bộ mẫu",
            },
        )
        create_or_update_invoice(booking=unpaid.booking)
        create_or_update_invoice(booking=partial.booking)
        create_or_update_invoice(booking=paid.booking)
