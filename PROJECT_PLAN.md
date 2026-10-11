# PROJECT PLAN — Hệ thống quản lý khách sạn có tích hợp AI

## 1. Trạng thái và nguyên tắc thực hiện

- Trạng thái hiện tại: **Hoàn thành cả 9 giai đoạn ngày 05/09/2026; sẵn sàng chạy demo và tiếp tục chỉnh sửa theo góp ý**.
- Tài liệu đã đối chiếu:
  - `NHÓM 05_DuongQuocHuy_2026,08mm,19(2).docx`.
  - `de_tai_04 (1)(1).md`.
  - Yêu cầu chi tiết mới nhất do người dùng cung cấp trong cuộc trò chuyện.
- Thứ tự ưu tiên khi có khác biệt: **yêu cầu mới nhất của người dùng → tài liệu đề tài Markdown → tài liệu Word cũ**.
- Công nghệ hiện tại: Python 3.12+, Django 5, Django Templates, Django ORM, Django Authentication, Bootstrap 5, JavaScript cơ bản, Chart.js, Gemini API với Gemini 2.5 Flash, PostgreSQL; SQLite dùng cho development.
- Không dùng React, Vue, Node.js, FastAPI hoặc cơ chế token REST cho giao diện chính.
- Giai đoạn 1 đã được người dùng xác nhận ngày 05/09/2026.

## 2. Kết quả kiểm tra thư mục dự án

Thư mục hiện tại chưa có dự án Django hoặc mã nguồn ứng dụng. Chỉ có hai tài liệu đầu vào trong thư mục `upload/`. Vì vậy dự án sẽ được khởi tạo mới, không có mã cũ cần bảo toàn hoặc migration cũ cần tương thích.

## 3. Tóm tắt phạm vi

Hệ thống phục vụ khách sạn vừa và nhỏ, bao phủ vòng đời từ tìm phòng, đặt phòng, xác nhận, check-in, sử dụng dịch vụ, check-out, lập hóa đơn đến thanh toán và thống kê.

Hệ thống có bốn role:

- `MANAGER`: quản lý nhân viên, phòng, loại phòng, dịch vụ, toàn bộ booking, hóa đơn, thống kê và AI.
- `RECEPTIONIST`: quản lý khách hàng, booking, lịch phòng, check-in/check-out, dịch vụ sử dụng, khởi tạo hóa đơn và AI hỗ trợ lễ tân.
- `ACCOUNTANT`: hóa đơn, thanh toán, công nợ, doanh thu và AI báo cáo/email nhắc nợ.
- `CUSTOMER`: tự đăng ký, tìm phòng, tư vấn AI, tự đặt phòng và chỉ xem/hủy dữ liệu thuộc sở hữu của mình.

AI có ba nhóm chức năng:

1. Tư vấn tối đa 3 phòng từ danh sách phòng trống đã được Django lọc.
2. Sinh bản nháp email xác nhận, hủy phòng hoặc nhắc thanh toán.
3. Nhận xét số liệu báo cáo đã được Django tổng hợp và đưa tối đa 3 gợi ý khuyến mại.

AI không quyết định phòng trống, không tự tạo booking, không tính doanh thu và không nhận dữ liệu nhạy cảm.

### 3.1. Yêu cầu kỹ thuật của đề tài

Đề bài cho phép lựa chọn:

- Backend: FastAPI, Flask hoặc Django.
- Frontend: React, Vue hoặc HTML template.
- CSDL: SQLite, MySQL hoặc PostgreSQL.
- AI Engine: OpenAI, Gemini, Claude, Hugging Face hoặc Ollama.

Phương án đã chốt cho sản phẩm là **Django + HTML template + PostgreSQL/SQLite + Gemini API** theo yêu cầu mới nhất. Dự án bắt buộc có prompt template cho tư vấn phòng và sinh email, kiểm tra trùng lịch tại backend, cùng test case cho đặt phòng, trả phòng, tính hóa đơn và AI sinh email.

## 4. Các điểm mâu thuẫn hoặc chưa đồng bộ

### 4.1. Mâu thuẫn giữa tài liệu cũ và yêu cầu mới

| STT | Nội dung | Tài liệu cũ | Chuẩn áp dụng khi triển khai |
|---:|---|---|---|
| 1 | Vai trò | Chủ yếu 3 role quản trị viên, lễ tân, kế toán; khách hàng chưa được đưa xuyên suốt vào FR/UC | Dùng 4 role: `MANAGER`, `RECEPTIONIST`, `ACCOUNTANT`, `CUSTOMER` |
| 2 | Đăng nhập | REST API, token | Django Authentication, session/cookie, đăng nhập bằng email |
| 3 | Giao diện | Frontend gọi RESTful API; cho phép React/Vue | Django Templates + Bootstrap 5 + JS cơ bản |
| 4 | Backend | Cho phép FastAPI/Flask/Django | Chỉ Django 5 bằng Python |
| 5 | CSDL | SQLite/MySQL/PostgreSQL đều có thể chọn | PostgreSQL là chính; SQLite chỉ development |
| 6 | AI Engine | Có thể chọn nhiều nhà cung cấp | Gemini API |
| 7 | Trạng thái booking | Tài liệu cũ dùng 4 trạng thái: đã đặt, đang lưu trú, đã trả, đã hủy | Dùng 5 trạng thái: `PENDING`, `CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`, `CANCELLED` |
| 8 | Người tạo booking | ERD cũ bắt buộc lễ tân tạo | Booking tự đặt bởi khách phải được hỗ trợ; `created_by` có thể là khách hoặc nhân viên |
| 9 | Quyền check-out | UC cũ ghi lễ tân và kế toán | Chỉ lễ tân thực hiện check-in/check-out; kế toán không được làm |
| 10 | Trạng thái phòng sau check-out | Có chỗ ghi “Trống (chờ dọn)” | Phải là `CLEANING`; chỉ sau khi dọn xong mới chuyển `AVAILABLE` |
| 11 | Giá lịch sử | Hóa đơn cũ lấy đơn giá hiện tại theo loại phòng | Booking lưu `room_price_per_night`; dịch vụ sử dụng lưu `unit_price` tại thời điểm phát sinh |
| 12 | Hóa đơn | ERD cũ thiếu phụ thu, giảm giá, đã trả, còn thiếu | Bổ sung đầy đủ công thức và trạng thái thanh toán |
| 13 | Khách hàng | ERD cũ không liên kết tài khoản, thiếu địa chỉ/ngày sinh/CCCD | `Customer.user` là OneToOne nullable; bổ sung trường theo yêu cầu |
| 14 | AI output | Tài liệu cũ cho phép text/Markdown/raw chung | Tư vấn phòng bắt buộc JSON và phải kiểm tra lại ID; không lưu/log bí mật |
| 15 | Email | Tài liệu cũ có thể hiểu là gửi email | Phiên bản demo chỉ tạo/lưu bản nháp và mô phỏng gửi |

### 4.2. Các quyết định nghiệp vụ đề xuất

Các quyết định dưới đây sẽ được coi là mặc định nếu người dùng xác nhận kế hoạch:

1. Booking do khách tự tạo có trạng thái `PENDING`; booking do lễ tân tạo có thể lưu `CONFIRMED` sau khi lễ tân xác nhận thông tin.
2. Khách chỉ được hủy booking của mình khi trạng thái là `PENDING` hoặc `CONFIRMED`. Chưa áp dụng phí hủy hoặc mốc giờ hủy vì đề bài chưa quy định.
3. Số đêm và tiền phòng chốt theo ngày dự kiến của booking: `check_out_date - check_in_date`. Trường hợp ở quá ngày được đưa vào `surcharge`, tránh âm thầm thay đổi dữ liệu booking lịch sử.
4. Không cho tổng thanh toán vượt số còn thiếu; hoàn tiền/refund nằm ngoài phạm vi phiên bản đầu.
5. Invoice có thể được lễ tân khởi tạo trước; khi check-out hệ thống tạo hoặc cập nhật và chốt lại số tiền.
6. `Room.status` biểu diễn trạng thái vận hành hiện tại. Tìm phòng tương lai chủ yếu dựa vào lịch booking; chỉ loại phòng `MAINTENANCE` và các phòng/loại phòng không hoạt động. Với thao tác check-in hiện tại, phòng phải sẵn sàng vận hành.
7. SQLite chỉ dành cho phát triển cơ bản. Kiểm thử khóa đồng thời và môi trường chạy chính thức phải dùng PostgreSQL vì `select_for_update()` không cung cấp khóa hàng tương đương trên SQLite.
8. Dữ liệu tiện ích của loại phòng dùng `JSONField` dạng danh sách chuỗi để tương thích Django/PostgreSQL/SQLite; chuẩn hóa chữ thường khi tìm kiếm tại service layer.
9. Booking, Invoice, Payment không có chức năng xóa cứng. Các danh mục dùng cờ `is_active`; dữ liệu lịch sử dùng `PROTECT` hoặc `RESTRICT` ở khóa ngoại phù hợp.

## 5. Kiến trúc Django đề xuất

```text
Browser
  -> Django URL
  -> Form / Permission Decorator hoặc Mixin
  -> Django View mỏng
  -> Domain Service
  -> Django ORM
  -> PostgreSQL / SQLite
```

```text
Django View
  -> AI Service
  -> Sanitizer / Prompt Builder
  -> Gemini Client
  -> JSON Validator / Allow-list Validator
  -> AILog
  -> Template hoặc fallback dữ liệu thường
```

Nguyên tắc phân lớp:

- `models.py`: cấu trúc dữ liệu, lựa chọn trạng thái, ràng buộc đơn giản và index.
- `forms.py`: kiểm tra dữ liệu nhập và loại bỏ các trường không được phép như `role` khi khách đăng ký.
- `views.py`: xác thực, kiểm tra quyền, nhận form, gọi service, trả template/redirect.
- `services.py`: nghiệp vụ đặt phòng, chuyển trạng thái, lập hóa đơn, thanh toán, thống kê, gọi AI.
- `selectors.py` (đề xuất bổ sung): truy vấn đọc phức tạp, tối ưu `select_related/prefetch_related`.
- `permissions.py`: decorator/mixin kiểm tra role và quyền sở hữu.
- `tests/`: test model, service, view, permission và AI mock.

## 6. Cấu trúc thư mục dự kiến

```text
hotel_management/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── customers/
│   ├── rooms/
│   ├── bookings/
│   ├── services/
│   ├── billing/
│   ├── reports/
│   ├── ai_integration/
│   └── core/
├── templates/
│   ├── public/
│   ├── accounts/
│   ├── customer/
│   ├── staff/
│   ├── partials/
│   └── base.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── media/
├── tests/
├── manage.py
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_PLAN.md
```

Mỗi app có `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `services.py` khi có nghiệp vụ phức tạp và thư mục `tests/`.

## 7. Thiết kế Database

Tất cả model nghiệp vụ có `created_at` và `updated_at` trừ khi Django đã cung cấp trường tương đương phù hợp. Tiền dùng `DecimalField`, không dùng float.

### 7.1. User — `accounts.User`

- Kế thừa `AbstractBaseUser`, `PermissionsMixin`.
- Trường: `email` unique, `full_name`, `phone`, `role`, `is_active`, `is_staff`, `date_joined`, `created_at`, `updated_at`.
- `USERNAME_FIELD = "email"`.
- `role`: MANAGER, RECEPTIONIST, ACCOUNTANT, CUSTOMER.
- Custom manager: `create_user`, `create_superuser`.
- Form đăng ký công khai không nhận trường role; service luôn gán CUSTOMER.
- Index: `email`, `(role, is_active)`.

### 7.2. Customer — `customers.Customer`

- `user`: OneToOne đến User, `null=True`, `blank=True`, `on_delete=SET_NULL`.
- `full_name`, `email`, `phone`, `address`, `date_of_birth`, `identity_document`, `notes`.
- Cho phép hồ sơ walk-in chưa có tài khoản.
- Lịch sử lưu trú không lưu thành chuỗi riêng; truy vấn từ Booking đã `CHECKED_OUT`.
- Dữ liệu `identity_document` không bao giờ được đưa vào payload AI hoặc log AI.
- Index: `phone`, `email`, `identity_document` (nếu tìm kiếm nghiệp vụ yêu cầu).

### 7.3. RoomType — `rooms.RoomType`

- `name`, `description`, `capacity`, `price_per_night`, `amenities` JSON, `image`, `is_active`.
- Check constraint: `capacity > 0`, `price_per_night >= 0`.
- Index: `is_active`, `(capacity, is_active)`.

### 7.4. Room — `rooms.Room`

- `room_number` unique, `room_type` FK, `floor`, `status`, `notes`, `is_active`.
- `status`: AVAILABLE, OCCUPIED, CLEANING, MAINTENANCE.
- Index: `room_number`, `(status, is_active)`, `(room_type, status)`.
- Không dùng status làm nguồn duy nhất để tìm phòng trống trong tương lai.

### 7.5. Booking — `bookings.Booking`

- `booking_code` unique, `customer` FK, `room` FK.
- `created_by` FK User nullable để lưu người thực hiện; khách tự đặt vẫn lưu chính tài khoản khách.
- `check_in_date`, `check_out_date`, `guest_count`.
- `room_price_per_night` là giá snapshot.
- `status`: PENDING, CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED.
- `actual_check_in_at`, `actual_check_out_at`, `cancelled_at`, `cancellation_reason`, `notes`.
- Check constraint: `check_out_date > check_in_date`, `guest_count > 0`, `room_price_per_night >= 0`.
- Index: `(room, check_in_date, check_out_date)`, `(status, check_in_date)`, `(customer, status)`, `booking_code`.
- PostgreSQL: service khóa bản ghi Room bằng `select_for_update()` trong `transaction.atomic()` trước khi kiểm tra giao lịch và tạo booking.
- Có thể bổ sung PostgreSQL `ExclusionConstraint` có điều kiện cho các trạng thái giữ phòng nếu migration tương thích được xác nhận; service check vẫn giữ để có thông báo thân thiện.

### 7.6. Service — `services.Service`

- `name`, `description`, `unit_price`, `unit`, `is_active`.
- Check constraint: `unit_price >= 0`.
- Index: `(is_active, name)`.

### 7.7. BookingService — `services.BookingService`

- `booking` FK, `service` FK, `quantity`, `unit_price`, `used_at`, `recorded_by` FK User.
- `line_total` được tính nhất quán từ `quantity * unit_price`; service nghiệp vụ không tin giá gửi từ browser.
- Check constraint: `quantity > 0`, `unit_price >= 0`, `line_total >= 0`.
- Index: `(booking, used_at)`, `service`.

### 7.8. Invoice — `billing.Invoice`

- OneToOne `booking`.
- `room_amount`, `service_amount`, `surcharge`, `discount`, `total_amount`, `paid_amount`, `balance_due`, `status`, `finalized_at`.
- `status`: UNPAID, PARTIALLY_PAID, PAID.
- Công thức được tính trong billing service; mọi giá trị tiền không âm và giảm giá không làm tổng tiền âm.
- Index: `(status, created_at)`, `finalized_at`.

### 7.9. Payment — `billing.Payment`

- `invoice` FK, `amount`, `method`, `paid_at`, `recorded_by`, `reference`, `notes`.
- `method`: CASH, BANK_TRANSFER, CARD.
- Check constraint: `amount > 0`.
- Không lưu số thẻ/tài khoản ngân hàng.
- Index: `(invoice, paid_at)`, `(method, paid_at)`.

### 7.10. AILog — `ai_integration.AILog`

- `user` FK nullable, `request_type`, `booking` FK nullable.
- `sanitized_request` JSON, `validated_response` JSON/text, `status`, `latency_ms`, `error_code`, timestamps.
- `status`: SUCCESS, FALLBACK, INVALID_RESPONSE, TIMEOUT, ERROR.
- Không lưu API key, session ID, mật khẩu, CCCD/hộ chiếu, thẻ hoặc tài khoản ngân hàng.
- Index: `(request_type, status, created_at)`, `(user, created_at)`.

### 7.11. EmailDraft — `ai_integration.EmailDraft`

- `booking` FK nullable, `invoice` FK nullable, `draft_type`, `recipient_name`, `recipient_email`, `subject`, `body`, `source`, `status`, `created_by`, `reviewed_by`, `reviewed_at`, `simulated_sent_at`.
- `source`: AI hoặc STATIC_FALLBACK.
- `status`: DRAFT, APPROVED, SIMULATED_SENT.
- Nội dung AI chỉ là bản nháp; nhân viên phải duyệt.
- Index: `(status, created_at)`, `(booking, draft_type)`.

## 8. Quy tắc nghiệp vụ trọng tâm

### 8.1. Tìm phòng trống

Điều kiện giao lịch:

```python
existing_check_in < requested_check_out
and existing_check_out > requested_check_in
```

Query loại các booking `CANCELLED` và chỉ coi `PENDING`, `CONFIRMED`, `CHECKED_IN` là giữ phòng. Phòng phải đủ sức chứa, đang hoạt động, loại phòng đang hoạt động, không `MAINTENANCE`, không giao lịch và phù hợp loại phòng/ngân sách/tiện ích.

### 8.2. Chống đặt trùng khi đồng thời

Service tạo booking:

1. Mở `transaction.atomic()`.
2. Khóa bản ghi Room bằng `select_for_update()`.
3. Đọc lại Room/RoomType và kiểm tra hoạt động, sức chứa.
4. Chạy lại query giao lịch ngay trong transaction.
5. Nếu trùng, ném lỗi nghiệp vụ có thông báo tiếng Việt.
6. Nếu hợp lệ, snapshot giá và tạo Booking.

Test đồng thời dùng `TransactionTestCase` và PostgreSQL. SQLite không được dùng để kết luận tính đúng của row lock.

### 8.3. Chuyển trạng thái booking

| Trạng thái hiện tại | Chuyển hợp lệ |
|---|---|
| PENDING | CONFIRMED, CANCELLED |
| CONFIRMED | CHECKED_IN, CANCELLED |
| CHECKED_IN | CHECKED_OUT |
| CHECKED_OUT | Không có |
| CANCELLED | Không có |

Mọi chuyển trạng thái đi qua service; view không tự sửa trực tiếp `status`.

### 8.4. Hóa đơn và thanh toán

```text
nights = check_out_date - check_in_date
room_amount = nights × room_price_per_night
service_amount = tổng BookingService.line_total
total_amount = max(0, room_amount + service_amount + surcharge - discount)
paid_amount = tổng Payment.amount
balance_due = total_amount - paid_amount
```

Trạng thái hóa đơn được suy ra từ số tiền, không nhận trực tiếp từ form.

## 9. Bảng phân quyền

Ký hiệu: `✓` được phép; `Own` chỉ dữ liệu của chính khách; `—` không được phép.

| Chức năng | MANAGER | RECEPTIONIST | ACCOUNTANT | CUSTOMER |
|---|:---:|:---:|:---:|:---:|
| Dashboard nội bộ | ✓ | ✓ | ✓ | — |
| Quản lý nhân viên | ✓ | — | — | — |
| Khóa/mở tài khoản | ✓ | — | — | — |
| Xem khách hàng | ✓ | ✓ | — | — |
| Sửa hồ sơ khách hàng | ✓ | ✓ | — | Own |
| Quản lý loại phòng | ✓ | — | — | — |
| Quản lý phòng | ✓ | — | — | — |
| Xem phòng/loại phòng | ✓ | ✓ | ✓ | ✓ |
| Tìm phòng trống | ✓ | ✓ | — | ✓ |
| Tạo booking | ✓ | ✓ | — | Own |
| Xem booking | Tất cả | Tất cả | Chỉ đọc khi cần đối soát | Own |
| Xác nhận booking | ✓ | ✓ | — | — |
| Check-in/check-out | ✓ | ✓ | — | — |
| Hủy booking | ✓ | ✓ | — | Own, trước check-in |
| Quản lý danh mục dịch vụ | ✓ | — | — | — |
| Ghi nhận dịch vụ sử dụng | ✓ | ✓ | — | — |
| Khởi tạo hóa đơn | ✓ | ✓ | — | — |
| Xem hóa đơn | Tất cả | Tất cả | Tất cả | Own |
| Ghi nhận thanh toán | ✓ | — | ✓ | Own, giả lập toàn bộ |
| Thống kê doanh thu | ✓ | — | ✓ | — |
| Thống kê công suất | ✓ | — | — | — |
| AI tư vấn phòng | ✓ | ✓ | — | ✓ |
| AI sinh email xác nhận/hủy | ✓ | ✓ | — | — |
| AI email nhắc thanh toán | ✓ | — | ✓ | — |
| AI nhận xét báo cáo/khuyến mại | ✓ | — | ✓ | — |
| Xem lịch sử AI | ✓ | — | — | — |

Ghi chú cập nhật: theo xác nhận mới nhất, Manager có thể thao tác thay Receptionist và Accountant. Customer chỉ được thanh toán giả lập hóa đơn của chính mình; backend vẫn kiểm tra role, ownership và POST/CSRF.

## 10. Danh sách URL và chức năng

Các URL dùng tên rõ ràng, có namespace theo app. Các thao tác thay đổi dữ liệu dùng POST, có CSRF; không dùng GET để hủy, check-in, check-out hoặc thanh toán.

### 10.1. Công khai và tài khoản

| URL | Method | Chức năng |
|---|---|---|
| `/` | GET | Trang chủ |
| `/rooms/types/` | GET | Danh sách loại phòng |
| `/rooms/types/<int:pk>/` | GET | Chi tiết loại phòng/phòng liên quan |
| `/rooms/search/` | GET/POST | Tìm phòng trống |
| `/accounts/register/` | GET/POST | Đăng ký khách hàng |
| `/accounts/login/` | GET/POST | Đăng nhập email/mật khẩu |
| `/accounts/logout/` | POST | Đăng xuất |
| `/accounts/password/change/` | GET/POST | Đổi mật khẩu |

### 10.2. Khu vực khách hàng

| URL | Method | Chức năng |
|---|---|---|
| `/customer/` | GET | Tổng quan tài khoản |
| `/customer/profile/` | GET/POST | Cập nhật hồ sơ |
| `/customer/ai-room-advisor/` | GET/POST | AI tư vấn phòng có fallback |
| `/customer/bookings/` | GET | Booking của tôi |
| `/customer/bookings/create/<int:room_id>/` | GET/POST | Tự đặt phòng |
| `/customer/bookings/<uuid:code>/` | GET | Chi tiết booking của tôi |
| `/customer/bookings/<uuid:code>/cancel/` | POST | Hủy booking của tôi nếu hợp lệ |
| `/customer/invoices/` | GET | Hóa đơn của tôi |
| `/customer/invoices/<int:pk>/` | GET | Chi tiết hóa đơn thuộc sở hữu |
| `/customer/stay-history/` | GET | Lịch sử booking đã check-out |

### 10.3. Khu vực nhân viên và quản lý

| URL | Method | Quyền chính | Chức năng |
|---|---|---|---|
| `/staff/dashboard/` | GET | Staff roles | Dashboard theo role |
| `/staff/bookings/` | GET | Manager/Receptionist | Danh sách booking |
| `/staff/bookings/create/` | GET/POST | Receptionist | Tạo booking cho khách |
| `/staff/bookings/<int:pk>/confirm/` | POST | Manager/Receptionist | Xác nhận booking |
| `/staff/bookings/<int:pk>/check-in/` | POST | Manager/Receptionist | Check-in |
| `/staff/bookings/<int:pk>/check-out/` | POST | Manager/Receptionist | Check-out, tạo/cập nhật invoice |
| `/staff/bookings/<int:pk>/cancel/` | POST | Manager/Receptionist | Hủy booking hợp lệ |
| `/staff/calendar/` | GET | Receptionist/Manager | Lịch phòng |
| `/staff/customers/` | GET | Receptionist/Manager | Danh sách khách hàng |
| `/staff/customers/create/` | GET/POST | Manager/Receptionist | Tạo khách walk-in |
| `/staff/customers/<int:pk>/edit/` | GET/POST | Manager/Receptionist | Sửa thông tin khách |
| `/staff/room-types/` | GET | Manager | Quản lý loại phòng |
| `/staff/room-types/create/` | GET/POST | Manager | Tạo loại phòng |
| `/staff/rooms/` | GET | Manager | Quản lý phòng |
| `/staff/rooms/<int:pk>/status/` | POST | Manager/Receptionist có giới hạn | Cập nhật trạng thái vận hành; lễ tân chỉ CLEANING→AVAILABLE |
| `/staff/services/` | GET | Manager | Quản lý danh mục dịch vụ |
| `/staff/bookings/<int:pk>/services/add/` | GET/POST | Manager/Receptionist | Ghi nhận dịch vụ sử dụng |
| `/staff/invoices/` | GET | Manager/Receptionist/Accountant | Danh sách hóa đơn theo quyền |
| `/staff/invoices/<int:pk>/` | GET | Manager/Receptionist/Accountant | Chi tiết hóa đơn |
| `/staff/invoices/<int:pk>/payments/add/` | GET/POST | Manager/Accountant | Ghi nhận thanh toán |
| `/customer/invoices/<int:pk>/pay/` | POST | Customer (Own) | Thanh toán giả lập toàn bộ công nợ |
| `/staff/reports/` | GET | Manager/Accountant | Thống kê, lọc ngày, Chart.js |
| `/staff/ai/reports/` | GET/POST | Manager/Accountant | AI nhận xét báo cáo |
| `/staff/ai/email/<int:booking_id>/` | GET/POST | Manager/Receptionist/Accountant theo loại | Sinh/sửa/duyệt email draft |
| `/staff/ai/logs/` | GET | Manager | Lịch sử gọi AI |
| `/staff/employees/` | GET | Manager | Danh sách nhân viên |
| `/staff/employees/create/` | GET/POST | Manager | Tạo lễ tân/kế toán |
| `/staff/employees/<int:pk>/toggle-active/` | POST | Manager | Khóa/mở tài khoản |

Endpoint JSON nội bộ chỉ tạo khi cần cho Chart.js hoặc cập nhật lịch phòng, vẫn sử dụng session, CSRF và quyền Django; không xây một REST API/token riêng.

## 11. Kế hoạch thực hiện theo 9 giai đoạn

### Giai đoạn 1 — Khởi tạo Django và Database

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Tạo project, 9 apps, settings tách môi trường, `.env.example`, `.gitignore`, requirements.
- Khai báo Custom User Model ngay trước migration đầu tiên.
- Cấu hình SQLite development và PostgreSQL qua biến môi trường.
- Tạo base template, Bootstrap và trang health/home tối thiểu.
- Tiêu chí hoàn tất: migrate sạch, `manage.py check` không lỗi, test smoke pass.

### Giai đoạn 2 — Tài khoản và phân quyền

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- User manager, đăng ký CUSTOMER, đăng nhập email, đăng xuất POST, đổi mật khẩu.
- Tạo Customer profile tự động cho khách đăng ký.
- Decorator/mixin theo role và kiểm tra tài khoản bị khóa.
- Manager tạo/khóa/mở RECEPTIONIST và ACCOUNTANT.
- Test đăng ký, email trùng, login đúng/sai, khóa tài khoản, chống tự nâng role và chống truy cập sai quyền.

### Giai đoạn 3 — Phòng, loại phòng và khách hàng

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Model/form/view/template cho RoomType, Room, Customer.
- Upload ảnh vào media; trạng thái vận hành và cờ hoạt động.
- CRUD theo quyền, public room listing/detail, menu theo role.
- Test constraint, quyền truy cập và hồ sơ walk-in.

### Giai đoạn 4 — Tìm phòng và booking

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Availability selector/service theo công thức overlap.
- Bộ lọc ngày, khách, loại phòng, ngân sách, tiện ích.
- Booking service dùng transaction + lock; snapshot giá.
- Customer self-booking và receptionist booking.
- Test ngày sai, overlap, cancelled không chặn, ownership và request đồng thời trên PostgreSQL.

### Giai đoạn 5 — Check-in, check-out và hủy phòng

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- State machine booking tập trung trong service.
- Xác nhận, check-in, check-out, hủy và ghi thời gian thực tế.
- Cập nhật OCCUPIED/CLEANING/AVAILABLE đúng quy trình.
- Test mọi chuyển trạng thái hợp lệ/không hợp lệ và quyền theo role.

### Giai đoạn 6 — Dịch vụ, hóa đơn và thanh toán

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Danh mục Service; BookingService snapshot đơn giá.
- Invoice calculation service, phụ thu/giảm giá.
- Nhiều Payment, cập nhật paid/balance/status trong transaction.
- Test tiền phòng, dịch vụ, thanh toán một phần/toàn bộ, chống trả thừa và ownership hóa đơn.

### Giai đoạn 7 — Dashboard và thống kê

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Query KPI từ database, lọc khoảng ngày.
- Dashboard theo role và Chart.js.
- Doanh thu theo ngày/tháng, booking theo thời gian, công suất, doanh thu theo loại phòng.
- Kiểm tra định nghĩa công suất và dữ liệu biên trước khi chốt test.

### Giai đoạn 8 — Tích hợp Gemini AI

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Gemini client có timeout, exception mapping và cấu hình `.env`.
- Sanitizer, prompt builder, JSON parser/validator, allow-list room ID.
- Room advisor fallback; email static fallback; AI report từ số liệu tổng hợp.
- AILog và EmailDraft, không log dữ liệu nhạy cảm.
- Mock toàn bộ API trong test; không tiêu tốn API thật khi chạy test.

### Giai đoạn 9 — Kiểm thử và hoàn thiện giao diện

- Trạng thái: **Hoàn thành ngày 05/09/2026**.
- Hoàn thiện toàn bộ test bắt buộc và kiểm tra coverage phần service/permission.
- Responsive Bootstrap, sidebar/header/breadcrumb, messages, loading, empty state, modal xác nhận.
- Format tiền Việt Nam và ngày `dd/MM/yyyy`.
- Management command `seed_demo`, README, hướng dẫn PostgreSQL/SQLite và kịch bản demo.
- Kiểm tra bảo mật, lỗi thân thiện, static/media và dữ liệu demo.

## 12. Quy trình nghiệm thu sau mỗi giai đoạn

Mỗi giai đoạn chỉ được đánh dấu hoàn tất khi đã cung cấp:

1. Danh sách file tạo/sửa.
2. Giải thích ngắn chức năng và quyết định quan trọng.
3. Kết quả `python manage.py makemigrations --check` hoặc migration mới tương ứng.
4. Kết quả `python manage.py migrate`.
5. Kết quả `python manage.py check`.
6. Kết quả test liên quan (`pytest` hoặc `python manage.py test`).
7. Lệnh chạy dự án.
8. Các bước kiểm tra thủ công trên giao diện.
9. Cập nhật trạng thái/checklist trong file này.

Không chuyển sang giai đoạn tiếp theo khi test trọng yếu của giai đoạn hiện tại chưa đạt, trừ khi người dùng yêu cầu rõ và lỗi được ghi nhận.

## 13. Danh sách test bắt buộc

- [ ] Khách hàng đăng ký thành công.
- [ ] Từ chối email trùng.
- [ ] Đăng nhập đúng và sai.
- [ ] Tài khoản bị khóa không đăng nhập/truy cập được.
- [ ] Khách không thể tự chọn role quản lý.
- [ ] Nhân viên không truy cập chức năng quản lý nhân viên.
- [ ] Khách không xem booking người khác.
- [ ] Khách không xem hóa đơn người khác.
- [ ] Ngày đặt phòng không hợp lệ.
- [ ] Hai booking bị trùng lịch bị từ chối.
- [ ] Booking CANCELLED không chặn phòng.
- [ ] Hai yêu cầu đồng thời không đặt được cùng một phòng.
- [ ] Check-in sai trạng thái bị từ chối.
- [ ] Check-out sai trạng thái bị từ chối.
- [ ] Tính đúng tiền phòng.
- [ ] Tính đúng tiền dịch vụ.
- [ ] Thanh toán một phần.
- [ ] Thanh toán toàn bộ.
- [ ] AI trả room ID không hợp lệ bị loại.
- [ ] AI timeout chuyển FALLBACK.
- [ ] Fallback không chặn tìm/đặt phòng.
- [ ] Payload AI không có CCCD/hộ chiếu hoặc dữ liệu thanh toán.

## 14. Dữ liệu demo `seed_demo`

Command phải idempotent ở mức hợp lý, có thể chạy lại mà không nhân bản dữ liệu theo khóa tự nhiên.

- 1 MANAGER, 1 RECEPTIONIST, 1 ACCOUNTANT.
- 3 tài khoản CUSTOMER.
- 5 Customer profile, gồm khách có và không có tài khoản.
- 3 RoomType, 10 Room, 4 Service.
- Booking ở PENDING, CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED.
- Invoice ở UNPAID, PARTIALLY_PAID, PAID.
- Payment và AILog mẫu; EmailDraft mẫu nếu phù hợp.
- Mật khẩu demo chỉ ghi trong README dành cho môi trường demo, không dùng cho production.

## 15. Biến môi trường dự kiến

```dotenv
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
GEMINI_API_KEY=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Production chuyển `DATABASE_URL` sang PostgreSQL, `DEBUG=False`, thiết lập `ALLOWED_HOSTS`, secure cookies và proxy/HTTPS đúng môi trường.

## 16. Definition of Done toàn dự án

- Toàn bộ backend/nghiệp vụ/xác thực/phân quyền/truy vấn/AI viết bằng Python và Django.
- Không có React, Vue, Node.js, FastAPI.
- Custom User Model tồn tại từ migration đầu tiên.
- Backend kiểm tra role và ownership ở mọi URL nhạy cảm.
- Không có booking giao nhau trong điều kiện triển khai PostgreSQL chuẩn.
- Công thức hóa đơn và nhiều lần thanh toán chính xác.
- AI chỉ nhận dữ liệu đã lọc, có validate output và fallback.
- Các test bắt buộc chạy đạt.
- `seed_demo`, README, `.env.example`, giao diện tiếng Việt responsive hoàn tất.
- `python manage.py check --deploy` được xem xét cho cấu hình production.

## 17. Xác nhận cần thiết trước khi viết code

Nếu người dùng xác nhận kế hoạch mà không yêu cầu sửa, Giai đoạn 1 sẽ bắt đầu với các quyết định mặc định tại mục 4.2. Những điểm có thể đổi trước khi code gồm:

- Quản lý chỉ xem hay được thao tác thay lễ tân/kế toán.
- Booking do lễ tân tạo mặc định `CONFIRMED` hay vẫn `PENDING`.
- Có cần chính sách hủy theo số giờ/ngày và phí hủy hay không.
- Có dùng PostgreSQL `ExclusionConstraint` ngoài cơ chế `select_for_update()` hay không.

**Trạng thái phê duyệt:** Đã xác nhận Giai đoạn 3; chờ xác nhận Giai đoạn 4.

## 18. Nhật ký Giai đoạn 1

### 18.1. File đã tạo hoặc sửa

- `manage.py`, `config/urls.py`, `config/asgi.py`, `config/wsgi.py`.
- `config/settings/base.py`, `development.py`, `production.py`.
- 9 app trong `apps/`: accounts, customers, rooms, bookings, services, billing, reports, ai_integration, core.
- Custom User Model, UserManager và cấu hình Django Admin trong `apps/accounts/`.
- URL/view trang chủ, health check, đăng nhập và đăng xuất POST.
- `templates/base.html`, `templates/core/home.html`, `templates/accounts/login.html`.
- `static/css/app.css`, `static/js/app.js`.
- `requirements.txt`, `pytest.ini`, `.env.example`, `.gitignore`, `README.md`.
- Migration `apps/accounts/migrations/0001_initial.py`.
- 3 smoke test trong `apps/core/tests.py`.

### 18.2. Chức năng đã hoàn thành

- Django 5.2 chạy trên Python 3.12.
- Settings tách development/production, đọc bí mật từ `.env`.
- SQLite mặc định cho development và hỗ trợ PostgreSQL qua `DATABASE_URL`.
- Custom User Model dùng email, có đủ 4 role ngay từ migration đầu tiên.
- Trang chủ Bootstrap, trang đăng nhập, đăng xuất bằng POST và health endpoint.

### 18.3. Kết quả kiểm tra

```text
python manage.py makemigrations --check --dry-run
No changes detected

python manage.py migrate
No migrations to apply

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 3 tests — OK

python -m pytest
3 passed

GET /          -> HTTP 200
GET /health/   -> HTTP 200, {"status": "ok", "service": "hotel-management"}
```

### 18.4. Kiểm tra thủ công

1. Tạo môi trường ảo và cài `requirements.txt`.
2. Sao chép `.env.example` thành `.env`.
3. Chạy `python manage.py migrate`.
4. Chạy `python manage.py runserver`.
5. Mở `http://127.0.0.1:8000/` và kiểm tra trang chủ.
6. Mở `/accounts/login/` và kiểm tra form email/mật khẩu.
7. Mở `/health/` và kiểm tra JSON trạng thái.

## 19. Nhật ký Giai đoạn 2

### 19.1. File đã tạo hoặc sửa

- `apps/accounts/forms.py`: form đăng ký khách và tạo nhân viên; form công khai không có trường role.
- `apps/accounts/permissions.py`: decorator/mixin kiểm tra đăng nhập, trạng thái hoạt động và role.
- `apps/accounts/services.py`: service đăng ký khách, tạo nhân viên, khóa/mở tài khoản trong transaction.
- `apps/accounts/views.py`, `urls.py`, `admin.py`, `tests.py`.
- `apps/customers/models.py`, `admin.py`, `views.py`, `urls.py`.
- `apps/customers/migrations/0001_initial.py`.
- `apps/core/views.py`, `urls.py` và `config/urls.py`.
- Template đăng ký, đăng nhập, đổi mật khẩu, danh sách/form nhân viên, dashboard staff, tổng quan khách và trang lỗi 403.
- `templates/base.html`, `README.md` và `PROJECT_PLAN.md`.

### 19.2. Chức năng đã hoàn thành

- Khách tự đăng ký; backend luôn gán `CUSTOMER` dù request gửi thêm role khác.
- Email được chuẩn hóa chữ thường và kiểm tra trùng không phân biệt hoa/thường.
- Mật khẩu được Django băm; đăng nhập bằng email; tài khoản bị khóa không đăng nhập được.
- Đổi mật khẩu giữ an toàn phiên đăng nhập.
- Customer profile được tạo cùng User trong `transaction.atomic()`.
- Chỉ Manager được tạo tài khoản `RECEPTIONIST` hoặc `ACCOUNTANT`.
- Chỉ Manager được khóa/mở tài khoản nhân viên; không cho tự khóa chính mình.
- Dashboard và menu thay đổi theo role; backend trả 403 khi role không hợp lệ.
- Đăng xuất và khóa/mở tài khoản chỉ nhận POST.

### 19.3. Kết quả kiểm tra

```text
python manage.py makemigrations customers
Created apps/customers/migrations/0001_initial.py

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py migrate
Applied customers.0001_initial — OK

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 15 tests — OK

python -m pytest
15 passed
```

### 19.4. Kiểm tra thủ công

1. Chạy server và mở `/accounts/register/` để đăng ký khách.
2. Kiểm tra đăng nhập email tại `/accounts/login/` và chuyển đến `/customer/`.
3. Tạo superuser bằng `python manage.py createsuperuser` để có tài khoản Manager.
4. Đăng nhập Manager, mở `/accounts/employees/`, tạo lễ tân và kế toán.
5. Thử khóa một nhân viên rồi đăng nhập tài khoản đó; hệ thống phải từ chối.
6. Đăng nhập lễ tân và truy cập `/accounts/employees/`; hệ thống phải trả trang 403.
7. Mở `/accounts/password/change/` và kiểm tra đổi mật khẩu.

## 20. Nhật ký Giai đoạn 3

### 20.1. Yêu cầu giao diện bổ sung

- Chỉ lấy phong cách trình bày từ ảnh mẫu người dùng cung cấp; chức năng vẫn theo đặc tả dự án.
- Dashboard dùng tông kem/cam, sidebar trái, thẻ KPI bo góc, bảng dữ liệu và thẻ người dùng góc phải.
- Menu sinh theo role và responsive: sidebar chuyển thành menu trượt trên màn hình nhỏ.

### 20.2. File đã tạo hoặc sửa

- `apps/rooms/models.py`, `forms.py`, `services.py`, `views.py`, `urls.py`, `staff_urls.py`, `admin.py`, `tests.py`.
- `apps/rooms/migrations/0001_initial.py`.
- `apps/customers/forms.py`, `services.py`, `views.py`, `urls.py`, `staff_urls.py`, `tests.py`.
- `apps/core/views.py`, `templatetags/hotel_format.py`.
- `templates/dashboard_base.html`, dashboard, phòng, loại phòng, khách hàng và hồ sơ cá nhân.
- `static/css/app.css`, `static/js/app.js`, `config/urls.py`, `requirements.txt`, `README.md`.

### 20.3. Chức năng đã hoàn thành

- RoomType: tên, mô tả, sức chứa, giá/đêm, tiện ích JSON, ảnh và trạng thái hoạt động.
- Room: số phòng, loại phòng, tầng, trạng thái AVAILABLE/OCCUPIED/CLEANING/MAINTENANCE, ghi chú và trạng thái hoạt động.
- Manager tạo/sửa/xem phòng và loại phòng; role khác bị backend từ chối.
- Trang công khai chỉ hiển thị loại phòng đang hoạt động.
- Manager và Receptionist xem danh sách/chi tiết khách; chỉ Receptionist tạo/sửa khách.
- Customer cập nhật hồ sơ của chính mình; User và Customer được đồng bộ email, họ tên, số điện thoại trong transaction.
- Hồ sơ khách walk-in cho phép `user=NULL`.
- Format tiền Việt Nam và ngày Việt Nam được áp dụng tại template.
- Dashboard lấy số lượng/trạng thái phòng thật từ database; booking/doanh thu vẫn để 0 đến đúng giai đoạn nghiệp vụ.

### 20.4. Kết quả kiểm tra

```text
python manage.py makemigrations rooms
Created apps/rooms/migrations/0001_initial.py

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py migrate
No migrations to apply

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 26 tests — OK

python -m pytest
26 passed
```

Trình duyệt kiểm tra từ xa không truy cập được địa chỉ localhost. Template đã được render qua các integration test; CSS có breakpoint cho desktop, tablet và mobile. Cần kiểm tra trực quan cuối cùng trên trình duyệt máy người dùng theo mục 20.5.

### 20.5. Kiểm tra thủ công

1. Chạy `python manage.py runserver` và đăng nhập bằng Manager.
2. Mở `/staff/dashboard/`; kiểm tra sidebar, KPI và bảng tình trạng phòng.
3. Mở `/staff/room-types/`, tạo loại phòng kèm ảnh và tiện ích.
4. Mở `/staff/rooms/`, tạo phòng và thử bốn trạng thái vận hành.
5. Đăng nhập Receptionist, mở `/staff/customers/`, tạo khách walk-in và sửa hồ sơ.
6. Đăng nhập Manager và xác nhận chỉ xem khách, không có nút thêm/sửa.
7. Đăng nhập Customer, mở `/customer/profile/` và cập nhật hồ sơ.
8. Thu nhỏ cửa sổ dưới 900 px; kiểm tra nút menu mở sidebar trượt, bảng cuộn ngang và thẻ KPI xếp cột.

### 20.6. Điều chỉnh nhận diện giao diện

- Đổi tên thương hiệu trên giao diện từ `SHM Hotel`/`Hotel AI` thành `SPK Hotel`.
- Đổi chữ viết tắt trong logo sidebar từ `SHM` thành `SPK`.
- Xóa nhãn `Đồ án Python · Django 5` trên trang chủ.
- Xóa toàn bộ khối giới thiệu `Giai đoạn 1` khỏi trang chủ.
- Không thay đổi chức năng, nghiệp vụ, phân quyền hoặc cấu trúc cơ sở dữ liệu.
- Đã chạy lại `python manage.py check`, Django TestCase và Pytest: 26 test đều đạt.

## 21. Nhật ký Giai đoạn 4

### 21.1. File đã tạo hoặc sửa

- `apps/bookings/models.py`, `forms.py`, `services.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`.
- `apps/bookings/customer_urls.py`, `apps/bookings/staff_urls.py`.
- `apps/bookings/migrations/0001_initial.py`.
- `apps/core/views.py`, `apps/customers/views.py`, `apps/core/templatetags/hotel_format.py`.
- `templates/bookings/availability_search.html`, `booking_form.html`, `booking_detail.html`.
- `templates/bookings/customer_booking_list.html`, `staff_booking_list.html`.
- `templates/base.html`, `templates/dashboard_base.html`, `templates/core/staff_dashboard.html`, `templates/customers/overview.html`.
- `static/css/app.css`, `config/urls.py`, `README.md`.

### 21.2. Chức năng đã hoàn thành

- Model Booking có mã duy nhất, khách hàng, phòng, người tạo, ngày ở, số khách, giá snapshot, trạng thái và các mốc thời gian nghiệp vụ.
- Constraint database bảo đảm ngày trả lớn hơn ngày nhận, số khách dương và giá snapshot không âm.
- Tìm phòng theo ngày, số khách, loại phòng, ngân sách mỗi đêm và danh sách tiện ích.
- Chỉ trả phòng/loại phòng đang hoạt động, đủ sức chứa, không bảo trì và không có booking giao lịch.
- Công thức giao lịch: `existing_check_in < requested_check_out` và `existing_check_out > requested_check_in`.
- Chỉ Booking `CANCELLED` không chặn lịch; các trạng thái còn lại được tính khi kiểm tra giao lịch.
- Khách tự đặt phòng cho chính mình với trạng thái `PENDING`; lễ tân tạo cho khách với trạng thái `CONFIRMED`.
- Backend không nhận giá từ browser; giá hiện tại của loại phòng được snapshot ngay khi tạo booking.
- `create_booking()` chạy trong `transaction.atomic()`, khóa Room bằng `select_for_update()` rồi kiểm tra trùng lần cuối.
- Khách chỉ truy vấn được booking của chính mình; Manager và Receptionist xem toàn bộ, chỉ Receptionist được tạo booking cho khách.
- Dashboard nhân viên hiển thị số booking hoạt động, chờ xác nhận và danh sách booking gần đây từ database.

### 21.3. Kết quả migration và kiểm thử

```text
python manage.py makemigrations bookings
Created apps/bookings/migrations/0001_initial.py

python manage.py migrate
Applying bookings.0001_initial... OK

python manage.py check
System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py test
Ran 45 tests — OK (skipped=1)

python -m pytest
44 passed, 1 skipped
```

Test đồng thời bị skip khi dùng SQLite vì SQLite không có row-level lock. Test này tự động chạy khi cấu hình test bằng PostgreSQL và xác nhận hai yêu cầu đồng thời chỉ tạo được một booking.

### 21.4. Lệnh chạy

```powershell
cd hotel_management
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Mở `http://127.0.0.1:8000/bookings/search/` để bắt đầu tìm phòng.

### 21.5. Kiểm tra thủ công

1. Đăng nhập Manager, tạo ít nhất một loại phòng và hai phòng hoạt động.
2. Mở `/bookings/search/`, nhập ngày trả lớn hơn ngày nhận, số khách và tiện ích; xác nhận chỉ hiện phòng phù hợp.
3. Đăng nhập Customer, tìm phòng, nhấn **Chọn phòng** và tạo booking; trạng thái phải là **Chờ xác nhận**.
4. Tìm lại đúng phòng với khoảng ngày giao nhau; phòng vừa đặt không được xuất hiện.
5. Tìm với ngày nhận đúng bằng ngày trả của booking cũ; phòng được phép xuất hiện vì hai khoảng không giao nhau.
6. Đăng nhập Receptionist, mở `/staff/bookings/create/`, chọn khách và tạo booking; trạng thái phải là **Đã xác nhận**.
7. Đăng nhập Manager, mở `/staff/bookings/`; xem được danh sách nhưng truy cập `/staff/bookings/create/` phải bị từ chối.
8. Đăng nhập Customer khác và thử mở URL chi tiết booking không thuộc mình; hệ thống phải trả 404.
9. Đổi giá loại phòng sau khi booking đã tạo; giá hiển thị trong booking cũ phải giữ nguyên.

### 21.6. Bổ sung dữ liệu mẫu theo yêu cầu trình diễn

- Thêm management command `python manage.py seed_demo` tại `apps/core/management/commands/seed_demo.py`.
- Lệnh hiện tạo/cập nhật 1 Manager, 1 Receptionist, 1 Accountant, 3 tài khoản Customer, 5 hồ sơ khách, 3 loại phòng, 10 phòng và 5 booking mẫu.
- Booking mẫu bao phủ `PENDING`, `CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`, `CANCELLED`.
- Dữ liệu dùng `get_or_create()`/`update_or_create()` nên có thể chạy lại mà không nhân bản bản ghi mẫu.
- Tài khoản nhân viên demo: `quanli@hotel.com`, `letan@hotel.com`, `ketoan@hotel.com`; cùng dùng mật khẩu `1`. Khách hàng dùng `Demo@12345`.
- Dịch vụ, hóa đơn, thanh toán và AI log sẽ được nối thêm vào command khi các model tương ứng được triển khai.
- Thêm test xác nhận command tạo đúng dữ liệu cốt lõi, chạy lặp không trùng và tài khoản demo đăng nhập được.

## 22. Nhật ký Giai đoạn 5

### 22.1. File đã tạo hoặc sửa

- `apps/bookings/services.py`: state machine và các service xác nhận, check-in, check-out, hủy booking.
- `apps/bookings/forms.py`: form lý do hủy và bộ lọc lịch phòng.
- `apps/bookings/views.py`, `staff_urls.py`, `customer_urls.py`: endpoint thao tác và lịch phòng.
- `apps/rooms/views.py`: cho lễ tân xem tình trạng phòng để hoàn tất dọn phòng.
- `templates/bookings/booking_detail.html`: nút nghiệp vụ, thời gian thực tế và modal xác nhận.
- `templates/bookings/room_calendar.html`: lịch booking theo từng phòng.
- `templates/rooms/room_list.html`, `templates/dashboard_base.html`: thao tác dọn xong và menu theo role.
- `static/js/app.js`, `static/css/app.css`: modal động, action bar và giao diện lịch responsive.
- `apps/bookings/tests.py`, `apps/rooms/tests.py`, `README.md`, `PROJECT_PLAN.md`.

### 22.2. Quy tắc nghiệp vụ đã hoàn thành

- State machine tập trung: `PENDING → CONFIRMED/CANCELLED`, `CONFIRMED → CHECKED_IN/CANCELLED`, `CHECKED_IN → CHECKED_OUT`.
- `CHECKED_OUT` và `CANCELLED` là trạng thái cuối, không thể chuyển tiếp.
- Chỉ Receptionist được xác nhận, check-in, check-out và hoàn tất dọn phòng.
- Customer chỉ được hủy booking thuộc tài khoản của mình khi còn `PENDING` hoặc `CONFIRMED`.
- Manager chỉ xem booking/lịch phòng, không được thực hiện nghiệp vụ của lễ tân.
- Check-in lưu `actual_check_in_at` và đổi Room từ `AVAILABLE` sang `OCCUPIED`.
- Check-out lưu `actual_check_out_at` và đổi Room từ `OCCUPIED` sang `CLEANING`.
- Hoàn tất dọn phòng chỉ chấp nhận Room đang `CLEANING`, sau đó chuyển sang `AVAILABLE`.
- Các endpoint thay đổi dữ liệu chỉ nhận POST và đều kiểm tra role ở backend.
- Service dùng `transaction.atomic()` và `select_for_update()` cho Booking/Room.
- Lịch phòng lọc tối đa 62 ngày, truy vấn theo công thức giao lịch và không hiển thị booking đã hủy.
- Check-out chưa tạo Invoice trong giai đoạn này vì Invoice/BookingService thuộc Giai đoạn 6; trạng thái và phòng đã sẵn sàng để nối billing service.

### 22.3. Kết quả migration và kiểm thử

```text
python manage.py migrate
No migrations to apply

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 61 tests — OK (skipped=1)

python -m pytest
60 passed, 1 skipped
```

Test bị skip là kiểm thử hai yêu cầu đồng thời đặt một phòng, chỉ chạy khi database test là PostgreSQL vì SQLite không hỗ trợ row-level lock.

### 22.4. Lệnh chạy

```powershell
cd hotel_management
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### 22.5. Kiểm tra thủ công

1. Đăng nhập `letan@hotel.com` với mật khẩu `1`.
2. Mở `/staff/bookings/`, chọn booking `DEMO-PENDING` và nhấn **Xác nhận booking**.
3. Với booking đã xác nhận, nhấn **Check-in**; booking phải thành **Đã nhận phòng**, phòng thành **Đang sử dụng**.
4. Nhấn **Check-out**; booking phải thành **Đã trả phòng**, phòng thành **Đang dọn**.
5. Mở `/staff/rooms/`, nhấn **Đã dọn xong**; phòng phải chuyển thành **Trống**.
6. Chọn một booking `PENDING` hoặc `CONFIRMED`, thử hủy và nhập lý do; booking phải thành **Đã hủy**.
7. Đăng nhập `customer1@spkhotel.vn`, mở **Booking của tôi** và thử hủy booking của chính mình.
8. Đổi URL sang booking của khách khác; hệ thống phải trả 404.
9. Đăng nhập Manager, xác nhận xem được `/staff/calendar/` nhưng không có quyền POST xác nhận/check-in/check-out.
10. Đăng nhập Accountant, truy cập `/staff/calendar/`; hệ thống phải trả 403.

### 22.6. Điều chỉnh tài khoản lễ tân demo

- Đổi email lễ tân mẫu từ `receptionist@spkhotel.vn` thành `letan@hotel.com`.
- Các tài khoản Manager, Receptionist và Accountant mẫu dùng mật khẩu `1`; tài khoản Customer giữ mật khẩu `Demo@12345`.
- `seed_demo` tự chuyển tài khoản mẫu cũ sang email mới khi chạy lại, không tạo thêm lễ tân trùng.
- Đã xác nhận `authenticate(email="letan@hotel.com", password="1")` thành công và role là `RECEPTIONIST`.
- Mật khẩu một ký tự chỉ dùng cho demo local, không phù hợp môi trường thật.

## 23. Nhật ký Giai đoạn 6

### 23.1. File đã tạo hoặc sửa

- `apps/services/models.py`, `forms.py`, `services.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`.
- `apps/services/migrations/0001_initial.py`.
- `apps/billing/models.py`, `forms.py`, `services.py`, `views.py`, `urls.py`, `customer_urls.py`, `admin.py`, `tests.py`.
- `apps/billing/migrations/0001_initial.py`.
- `apps/bookings/services.py`, `views.py`, `templates/bookings/booking_detail.html`.
- `apps/customers/views.py`, `templates/customers/overview.html`.
- `apps/core/views.py`, `apps/core/management/commands/seed_demo.py`, `apps/core/tests.py`.
- Template danh mục/ghi dịch vụ, danh sách/chi tiết hóa đơn, điều chỉnh và thanh toán.
- `templates/dashboard_base.html`, `templates/core/staff_dashboard.html`, `config/urls.py`, `README.md`.

### 23.2. Chức năng và công thức

- Service gồm tên, mô tả, đơn giá, đơn vị tính, trạng thái hoạt động và index phù hợp.
- BookingService lưu số lượng, đơn giá snapshot, ngày dùng, thành tiền và lễ tân ghi nhận.
- Chỉ booking `CHECKED_IN` được ghi dịch vụ; `line_total = quantity × unit_price` được tính tại service backend.
- Invoice liên kết OneToOne Booking; Payment liên kết nhiều-một với Invoice và không xóa cứng dữ liệu đã phát sinh.
- `room_amount = number_of_nights × room_price_per_night`.
- `service_amount = SUM(BookingService.line_total)`.
- `total_amount = room_amount + service_amount + surcharge - discount`.
- `balance_due = total_amount - paid_amount`; `paid_amount` luôn tổng hợp từ Payment.
- Check-out gọi billing service trong cùng transaction; nếu tạo hóa đơn lỗi thì toàn bộ check-out được rollback.
- Accountant có thể ghi nhiều Payment và không được trả vượt công nợ; Receptionist không được ghi thanh toán.
- Receptionist được nhập phụ thu/giảm giá; Accountant chỉ theo dõi công nợ và ghi thanh toán.
- Customer chỉ xem Invoice có Booking liên kết tài khoản của chính mình; truy cập hóa đơn khác trả 404.
- Không có chức năng xóa BookingService, Invoice hoặc Payment trên giao diện.

### 23.3. Dữ liệu demo

- `seed_demo` tạo 4 dịch vụ: Ăn sáng, Giặt ủi, Đưa đón sân bay, Minibar.
- Có dịch vụ sử dụng cho booking đang/đã lưu trú.
- Có 3 hóa đơn mẫu bao phủ chưa thanh toán, thanh toán một phần và đã thanh toán.
- Có 2 Payment mẫu với hình thức chuyển khoản và thẻ.
- Command tiếp tục idempotent khi chạy nhiều lần.

### 23.4. Migration và kiểm thử

```text
python manage.py makemigrations services billing
Created services.0001_initial and billing.0001_initial

python manage.py migrate
Applied billing.0001_initial and services.0001_initial — OK

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 75 tests — OK (skipped=1)

python -m pytest
74 passed, 1 skipped
```

### 23.5. Lệnh chạy

```powershell
cd hotel_management
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### 23.6. Kiểm tra thủ công

1. Đăng nhập Manager, mở `/staff/services/` và tạo/sửa một dịch vụ.
2. Đăng nhập `letan@hotel.com` / `1`, mở booking `DEMO-CHECKEDIN` và ghi dịch vụ sử dụng.
3. Check-out booking đó; xác nhận trạng thái thành `CHECKED_OUT`, phòng thành `CLEANING` và hóa đơn được tạo.
4. Mở hóa đơn, kiểm tra tiền phòng, tiền dịch vụ và tổng tiền theo công thức.
5. Lễ tân thử nhập phụ thu/giảm giá; giảm giá quá tổng tiền phải bị từ chối.
6. Đăng nhập `ketoan@hotel.com` / `1`, mở `/staff/invoices/` và ghi thanh toán một phần.
7. Ghi lần thanh toán còn lại; hóa đơn phải chuyển từ `PARTIALLY_PAID` sang `PAID`.
8. Thử nhập số tiền lớn hơn công nợ; backend phải từ chối và không tạo Payment.
9. Đăng nhập `customer1@spkhotel.vn` / `Demo@12345`, mở `/customer/invoices/` và xem hóa đơn của mình.
10. Thử đổi ID sang hóa đơn của khách khác; hệ thống phải trả 404.

## 24. Nhật ký Giai đoạn 7

### 24.1. File đã tạo hoặc sửa

- `apps/reports/forms.py`: form lọc ngày và kiểu nhóm ngày/tháng, giới hạn tối đa 366 ngày.
- `apps/reports/services.py`: toàn bộ truy vấn ORM, tính KPI, công suất và dữ liệu biểu đồ.
- `apps/reports/views.py`, `urls.py`, `tests.py`: trang báo cáo, phân quyền và kiểm thử.
- `templates/reports/report_dashboard.html`: giao diện báo cáo và bốn biểu đồ Chart.js.
- `apps/core/views.py`, `templates/core/staff_dashboard.html`: dashboard lấy dữ liệu thật từ database.
- `templates/dashboard_base.html`, `static/css/app.css`, `config/urls.py`, `README.md`, `PROJECT_PLAN.md`.

### 24.2. Định nghĩa số liệu đã chốt

- Doanh thu là **doanh thu thực thu**, bằng tổng `Payment.amount` có `paid_at` trong khoảng lọc.
- Công suất = số đêm phòng đã sử dụng / tổng số đêm phòng có thể bán × 100%.
- Mẫu số dùng số phòng đang hoạt động × số ngày trong khoảng lọc (tính cả ngày đầu và cuối).
- Tử số lấy phần giao nhau giữa lịch ở và khoảng lọc của booking `CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`.
- Booking `PENDING` và `CANCELLED` không tăng công suất phòng.
- Booking mới và tỷ lệ hủy được tính theo `created_at` trong kỳ.
- Loại phòng bán chạy dựa trên booking không hủy có lịch ở giao với kỳ.
- Dịch vụ bán chạy dựa trên tổng số lượng `BookingService` theo `used_at`.
- Doanh thu theo loại phòng gắn từng Payment với loại phòng của booking tương ứng.
- Tất cả số liệu do Django ORM và service Python tính; AI không tham gia phép tính.

### 24.3. Chức năng giao diện và phân quyền

- URL báo cáo: `/staff/reports/`.
- Manager và Accountant được xem; Receptionist và Customer bị backend trả 403.
- Bộ lọc hỗ trợ khoảng ngày và nhóm biểu đồ theo ngày hoặc tháng.
- Chart.js hiển thị doanh thu, booking, công suất và doanh thu theo loại phòng.
- Dữ liệu chart được đưa vào HTML bằng `json_script` để tránh chèn JavaScript không an toàn.
- Dashboard chung hiển thị doanh thu tháng, công suất theo đêm phòng, công nợ, loại phòng và dịch vụ nổi bật.

### 24.4. Migration và kiểm thử

```text
python manage.py migrate
No migrations to apply

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 82 tests — OK (skipped=1)

python -m pytest
81 passed, 1 skipped
```

Test bị skip là kiểm thử đồng thời chỉ có ý nghĩa trên PostgreSQL vì SQLite không hỗ trợ row-level lock tương đương.

### 24.5. Lệnh chạy

```powershell
cd hotel_management
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### 24.6. Kiểm tra thủ công

1. Đăng nhập `quanli@hotel.com` / `1`, mở `/staff/dashboard/` và kiểm tra KPI lấy dữ liệu thật.
2. Nhấn **Báo cáo**, chọn khoảng ngày có dữ liệu demo rồi xem bốn biểu đồ.
3. Đổi **Nhóm biểu đồ theo** từ ngày sang tháng và xác nhận nhãn biểu đồ thay đổi.
4. Nhập đến ngày nhỏ hơn từ ngày; backend phải báo lỗi tiếng Việt.
5. Nhập khoảng vượt 366 ngày; backend phải từ chối.
6. Đăng nhập `ketoan@hotel.com` / `1`; kế toán phải xem được báo cáo.
7. Đăng nhập `letan@hotel.com` / `1`; lễ tân không thấy menu Báo cáo và truy cập trực tiếp URL phải nhận 403.
8. Ghi thêm một Payment trong kỳ rồi tải lại; doanh thu và biểu đồ theo loại phòng phải tăng đúng số tiền.

## 25. Nhật ký Giai đoạn 8

### 25.1. File đã tạo hoặc sửa

- `apps/ai_integration/models.py`, migration `0001_initial.py`: `AILog`, `EmailDraft`.
- `apps/ai_integration/client.py`: gọi Gemini `generateContent` bằng API key trong `.env`, timeout và mã lỗi thân thiện.
- `apps/ai_integration/prompts.py`: prompt template tư vấn phòng, sinh email và nhận xét báo cáo.
- `apps/ai_integration/services.py`: validate JSON, allow-list phòng, fallback, email draft và log AI.
- `apps/ai_integration/forms.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`.
- Bốn template AI: tư vấn phòng, sinh/duyệt email, nhận xét báo cáo và lịch sử AI.
- `templates/dashboard_base.html`, `templates/bookings/booking_detail.html`, `templates/billing/invoice_detail.html`.
- `apps/core/management/commands/seed_demo.py`, `apps/core/tests.py`, `config/urls.py`, `README.md`, `PROJECT_PLAN.md`.

### 25.2. Nghiệp vụ AI đã hoàn thành

- Customer và Receptionist dùng AI tư vấn phòng tại `/ai/room-advisor/`.
- Django truy vấn phòng trống trước; Gemini chỉ nhận danh sách allow-list đã lọc.
- Kết quả AI tối đa 3 phòng, bắt buộc khớp cả ID và số phòng; kết quả giả bị loại.
- Khi API lỗi, timeout, hết số dư hoặc chưa nhập key, hệ thống trả gợi ý thường và ghi `FALLBACK`.
- AI không tự tạo booking; người dùng vẫn phải chọn phòng và qua booking service kiểm tra lịch lần cuối.
- Receptionist sinh email xác nhận/hủy; Accountant chỉ sinh email nhắc thanh toán.
- Email chỉ là bản nháp có thể sửa, duyệt hoặc mô phỏng gửi; chưa gửi email thật.
- Email fallback tĩnh được dùng khi Gemini không hoạt động.
- Manager và Accountant dùng AI nhận xét báo cáo tại `/ai/reports/`.
- Django tổng hợp doanh thu, công suất, booking, tỷ lệ hủy, loại phòng và dịch vụ trước khi gọi AI.
- AI trả nhận xét, xu hướng, cảnh báo và tối đa 3 gợi ý khuyến mãi; số liệu gốc luôn hiển thị cạnh nhận xét.
- Manager xem tối đa 100 log gần nhất tại `/ai/logs/`.

### 25.3. An toàn dữ liệu

- Không đưa mật khẩu, API key, session ID, CCCD/hộ chiếu, số thẻ hay tài khoản ngân hàng vào payload AI.
- Prompt email chỉ có tên khách, mã booking, loại phòng, ngày ở, tổng tiền, số còn thiếu và liên hệ khách sạn.
- Prompt báo cáo chỉ có số liệu tổng hợp, không chứa dữ liệu định danh khách hàng.
- AILog chỉ lưu tóm tắt an toàn, trạng thái, mã lỗi và thời gian xử lý; không lưu API key hoặc prompt đầy đủ.
- Dữ liệu JSON dùng `json_script` hoặc validate backend trước khi hiển thị.

### 25.4. Migration và kiểm thử

```text
python manage.py migrate
Applied ai_integration.0001_initial — OK

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py test
Ran 91 tests — OK (skipped=1)

python -m pytest
90 passed, 1 skipped
```

### 25.5. Cấu hình và chạy

Trong `.env`:

```dotenv
GEMINI_API_KEY=nhap_api_key_cua_ban
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Nếu để trống key hoặc tài khoản hết số dư, website vẫn chạy bằng fallback.

```powershell
cd hotel_management
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### 25.6. Kiểm tra thủ công

1. Nhập Gemini API key vào `.env`, khởi động lại server.
2. Đăng nhập Customer, mở **AI tư vấn phòng**, nhập ngày và nhu cầu rồi kiểm tra tối đa 3 phòng.
3. Xóa key và thử lại; giao diện phải báo fallback nhưng vẫn hiện phòng hợp lệ.
4. Đăng nhập `letan@hotel.com` / `1`, mở chi tiết booking và nhấn **Sinh email**.
5. Kiểm tra bản nháp có thể chỉnh sửa, duyệt và mô phỏng gửi.
6. Đăng nhập kế toán, mở hóa đơn còn thiếu và sinh email nhắc thanh toán; thử chọn email xác nhận phải bị từ chối.
7. Đăng nhập Manager, mở **AI phân tích**, chọn khoảng ngày và kiểm tra số liệu gốc cùng gợi ý khuyến mãi.
8. Mở **Lịch sử AI** để xem trạng thái `SUCCESS` hoặc `FALLBACK`, mã lỗi và thời gian xử lý.

## 26. Nhật ký Giai đoạn 9

### 26.1. File đã tạo hoặc sửa

- `tests/test_stage9_acceptance.py`: kiểm thử luồng điều hướng theo bốn role, chặn truy cập chéo và trang lỗi 404.
- `templates/base.html`: navbar responsive cho màn hình nhỏ.
- `templates/core/staff_dashboard.html`: không hiển thị liên kết booking ngoài quyền của kế toán.
- `templates/404.html`, `templates/500.html`, `apps/core/views.py`, `config/urls.py`: trang lỗi thân thiện.
- `static/js/app.js`: loading và khóa nút khi gửi form POST.
- `config/settings/production.py`, `.env.example`: tăng cường HTTPS, cookie, HSTS và clickjacking protection.
- `INSTALL_WINDOWS.md`: hướng dẫn cài/chạy, cấu hình SQLite/PostgreSQL/Gemini và sửa lỗi đăng nhập demo.
- `DEMO_CHECKLIST.md`: kịch bản trình diễn cho Manager, Receptionist, Accountant và Customer.
- `README.md`, `PROJECT_PLAN.md`.

### 26.2. Rà soát hoàn thiện

- Giao diện tiếp tục dùng Django Templates, Bootstrap 5, CSS và JavaScript cơ bản; không dùng React/Vue/Node/FastAPI.
- Navbar công khai thu gọn trên mobile; dashboard sidebar đã responsive từ các giai đoạn trước.
- Menu và liên kết chỉ hiển thị theo role, đồng thời mọi view quan trọng vẫn kiểm tra role/ownership ở backend.
- Form POST hiển thị spinner `Đang xử lý...` và khóa nút để hạn chế bấm lặp.
- 403, 404 và 500 không hiển thị lỗi kỹ thuật chi tiết cho người dùng.
- `.env`, SQLite local, media, cache, coverage và virtual environment đều bị loại khỏi Git/gói bàn giao.
- Cấu hình production bắt buộc `DJANGO_SECRET_KEY`, tắt DEBUG, secure cookie, HTTPS redirect và HSTS.
- `python manage.py check --deploy --settings=config.settings.production` đạt không cảnh báo với biến môi trường production hợp lệ.

### 26.3. Migration và kiểm thử cuối

```text
python manage.py migrate
No migrations to apply

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py check --deploy --settings=config.settings.production
System check identified no issues (0 silenced)

python manage.py test
Ran 97 tests — OK (skipped=1)

python -m pytest
96 passed, 1 skipped
```

Test bị skip là kiểm thử hai yêu cầu đồng thời đặt cùng một phòng khi đang dùng SQLite. Hãy chạy test với PostgreSQL để kiểm tra row-level lock thật.

### 26.4. Lệnh chạy và kiểm tra thủ công

- Lệnh cài/chạy đầy đủ nằm trong `INSTALL_WINDOWS.md`.
- Kịch bản demo theo vai trò nằm trong `DEMO_CHECKLIST.md`.
- Sau khi giải nén: tạo `.venv`, cài requirements, sao chép `.env.example` thành `.env`, migrate, seed và runserver.
- Để gọi Gemini thật, nhập API key vào `.env` rồi khởi động lại server.

## 27. Điều chỉnh tài khoản demo theo yêu cầu

- Quản lý đổi từ `manager@spkhotel.vn` / `Demo@12345` thành `quanli@hotel.com` / `1`.
- Kế toán đổi từ `accountant@spkhotel.vn` / `Demo@12345` thành `ketoan@hotel.com` / `1`.
- Lễ tân giữ `letan@hotel.com` / `1`.
- `seed_demo` tự chuyển tài khoản cũ sang email mới, giữ các liên kết dữ liệu và không tạo trùng tài khoản.
- Test xác nhận hai email cũ không còn tồn tại sau khi seed và cả hai tài khoản mới đăng nhập được bằng mật khẩu `1`.

## 28. Manager toàn quyền nghiệp vụ và thanh toán mô phỏng cho Customer

### 28.1. Quyền Manager đã mở rộng

- Tạo và sửa hồ sơ khách hàng.
- Tạo, xác nhận, hủy booking hợp lệ; check-in và check-out.
- Chuyển phòng đã dọn từ `CLEANING` về `AVAILABLE`.
- Ghi dịch vụ khách sử dụng, điều chỉnh phụ thu/giảm giá và ghi nhận thanh toán.
- Dùng AI tư vấn phòng, sinh/duyệt email, phân tích báo cáo và xem lịch sử AI.
- Tất cả quyền đều được kiểm tra tại view và service; không chỉ hiển thị nút trên giao diện.

### 28.2. Thanh toán một chạm của Customer

- Chi tiết hóa đơn còn công nợ hiển thị nút **Thanh toán ngay** và modal xác nhận.
- Endpoint chỉ nhận `POST`, có CSRF và lọc hóa đơn theo tài khoản sở hữu.
- Backend khóa hóa đơn bằng `select_for_update()`, tính lại công nợ và tạo một Payment bằng đúng toàn bộ số còn thiếu.
- Hóa đơn chuyển sang `PAID`, số còn thiếu về 0 và giao diện báo **Thanh toán thành công**.
- Bấm lại không tạo thanh toán trùng; khách không thể thanh toán hóa đơn người khác.
- Đây là giao dịch mô phỏng cho đồ án, không kết nối cổng thanh toán và không lưu dữ liệu ngân hàng thật.

### 28.3. File đã tạo hoặc sửa

- `apps/customers/services.py`, `views.py`, `tests.py`.
- `apps/bookings/services.py`, `views.py`, `tests.py`.
- `apps/services/services.py`, `views.py`, `tests.py`.
- `apps/billing/services.py`, `views.py`, `customer_urls.py`, `tests.py`.
- `apps/ai_integration/views.py`, `tests.py`.
- Các template khách hàng, booking, phòng, hóa đơn, tìm phòng và sidebar.
- `README.md`, `DEMO_CHECKLIST.md`, `PROJECT_PLAN.md`.

### 28.4. Migration và kiểm thử

```text
python manage.py migrate
No migrations to apply

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced)

python manage.py check --deploy --settings=config.settings.production
System check identified no issues (0 silenced)

python manage.py test
Ran 104 tests — OK (skipped=1)

python -m pytest
103 passed, 1 skipped, 28 subtests passed
```

Test bị skip là kiểm thử đồng thời cần PostgreSQL và row-level lock. SQLite chỉ dùng cho development.

### 28.5. Kiểm tra thủ công

1. Đăng nhập `quanli@hotel.com` / `1`; thử sửa khách, tạo booking, check-in/out, ghi dịch vụ và ghi thanh toán.
2. Đăng nhập `customer1@spkhotel.vn` / `Demo@12345`; mở một hóa đơn còn thiếu và nhấn **Thanh toán ngay**.
3. Xác nhận modal; kiểm tra thông báo thành công, trạng thái `PAID`, còn thiếu `0 ₫` và một dòng lịch sử thanh toán mới.
4. Thử gửi lại URL thanh toán; hệ thống phải báo hóa đơn đã thanh toán và không tạo Payment thứ hai.
5. Đổi ID hóa đơn trên URL sang hóa đơn người khác; backend phải trả 404.

## 29. Chuyển AI sang Gemini 2.5 Flash

- Nhà cung cấp AI được đổi sang Gemini theo yêu cầu mới nhất của người dùng.
- `apps/ai_integration/client.py` gọi `POST /v1beta/models/{model}:generateContent`, dùng model `gemini-2.5-flash` và JSON mode qua `generationConfig.responseMimeType`.
- Cấu hình bí mật dùng `GEMINI_API_KEY`; key không được hard-code hoặc ghi vào log.
- Django vẫn truy vấn và kiểm tra phòng trống trước khi gửi allow-list cho AI.
- Kết quả phòng từ AI vẫn được kiểm tra lại ID/số phòng; tối đa 3 phòng hợp lệ.
- Timeout, lỗi xác thực, hết số dư, model không được cấp quyền hoặc JSON sai đều chuyển sang `FALLBACK` và không chặn đặt phòng.
- Prompt email và báo cáo vẫn loại bỏ CCCD, mật khẩu, dữ liệu thẻ và tài khoản ngân hàng.
- Đã bổ sung test xác nhận endpoint `generateContent`, model `gemini-2.5-flash`, JSON mode và trường hợp thiếu key.

```text
python manage.py check
System check identified no issues (0 silenced)

python -m pytest
105 passed, 1 skipped, 28 subtests passed
```

```dotenv
GEMINI_API_KEY=
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```
