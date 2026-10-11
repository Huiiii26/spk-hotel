# Hệ thống quản lý khách sạn có tích hợp AI

Dự án đồ án sử dụng Python 3.12+, Django 5, Django Templates, PostgreSQL/SQLite và Gemini API.

## Yêu cầu kỹ thuật của đề tài

Đề bài cho phép lựa chọn:

- Backend: FastAPI, Flask hoặc Django.
- Frontend: React, Vue hoặc HTML template.
- CSDL: SQLite, MySQL hoặc PostgreSQL.
- AI Engine: OpenAI, Gemini, Claude, Hugging Face hoặc Ollama.

Phương án của dự án này là **Django + HTML template + PostgreSQL/SQLite + Gemini 2.5 Flash**. Dự án có prompt template cho tư vấn phòng và sinh email, kiểm tra trùng lịch tại backend, cùng test case cho đặt phòng, trả phòng, tính hóa đơn và AI sinh email.

## Chạy nhanh trên Windows PowerShell

```powershell
cd hotel_management
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Mở `http://127.0.0.1:8000/`.

## Dữ liệu và tài khoản demo

Chạy lệnh sau sau khi migrate:

```powershell
python manage.py seed_demo
```

Lệnh có thể chạy nhiều lần mà không tạo trùng dữ liệu. Dữ liệu hiện có 3 loại phòng, 10 phòng, 5 khách hàng và 5 booking mẫu.

| Vai trò | Email |
| --- | --- |
| Quản lý | `quanli@hotel.com` — mật khẩu `1` |
| Lễ tân | `letan@hotel.com` — mật khẩu `1` |
| Kế toán | `ketoan@hotel.com` — mật khẩu `1` |
| Khách hàng | `customer1@spkhotel.vn` |
| Khách hàng | `customer2@spkhotel.vn` |
| Khách hàng | `customer3@spkhotel.vn` |

Ba tài khoản nhân viên dùng mật khẩu `1`; các tài khoản khách dùng `Demo@12345`. Mật khẩu ngắn chỉ phục vụ trình diễn local, không sử dụng khi triển khai thật.

Lệnh hiện tạo cả dịch vụ, hóa đơn, thanh toán, bản nháp email và lịch sử AI mẫu.

Trước khi dùng môi trường thật, hãy tạo `DJANGO_SECRET_KEY` riêng trong `.env`. Không commit `.env` lên Git.

## Chạy bằng PostgreSQL

Thay `DATABASE_URL` trong `.env`:

```dotenv
DATABASE_URL=postgresql://hotel_user:your_password@localhost:5432/hotel_management
```

Sau đó chạy lại `python manage.py migrate`.

## Kiểm tra dự án

```powershell
python manage.py check
python manage.py test
python -m pytest
```

## Chức năng Giai đoạn 2

- Khách đăng ký tại `/accounts/register/`; role luôn là `CUSTOMER`.
- Đăng nhập email tại `/accounts/login/` và đổi mật khẩu tại `/accounts/password/change/`.
- Khách xem tổng quan tài khoản tại `/customer/`.
- Nhân viên xem dashboard tại `/staff/dashboard/`.
- Quản lý tạo, khóa hoặc mở tài khoản lễ tân/kế toán tại `/accounts/employees/`.
- Backend kiểm tra role; việc chỉ ẩn menu không được coi là phân quyền.

## Chức năng Giai đoạn 3

- Giao diện dashboard tông kem/cam theo mẫu, sidebar cố định và responsive trên mobile.
- Quản lý loại phòng tại `/staff/room-types/`.
- Quản lý phòng tại `/staff/rooms/`.
- Danh sách loại phòng công khai tại `/rooms/types/`.
- Quản lý/tra cứu khách hàng tại `/staff/customers/` theo đúng role.
- Khách cập nhật hồ sơ của mình tại `/customer/profile/`.
- Trạng thái vận hành phòng được tách khỏi tình trạng trống theo lịch booking.

## Chức năng Giai đoạn 4

- Tìm phòng trống tại `/bookings/search/` theo ngày, số khách, loại phòng, ngân sách và tiện ích.
- Backend loại phòng bảo trì, phòng ngừng hoạt động và booking giao lịch theo đúng công thức overlap; chỉ booking `CANCELLED` không chặn phòng.
- Khách tự tạo booking tại `/customer/bookings/create/`; trạng thái ban đầu là `PENDING`.
- Lễ tân tạo booking cho khách tại `/staff/bookings/create/`; trạng thái ban đầu là `CONFIRMED`.
- Giá mỗi đêm được snapshot vào booking, không đổi theo giá loại phòng về sau.
- Service dùng `transaction.atomic()` và `select_for_update()` để khóa phòng trước khi kiểm tra trùng lần cuối.
- Manager/lễ tân xem toàn bộ booking và có thể tạo booking cho khách; khách chỉ xem booking của chính mình.

## Chức năng Giai đoạn 5

- Quản lý hoặc lễ tân xác nhận booking `PENDING → CONFIRMED`.
- Quản lý hoặc lễ tân check-in booking `CONFIRMED → CHECKED_IN`; lưu thời gian thực tế và chuyển phòng sang `OCCUPIED`.
- Quản lý hoặc lễ tân check-out booking `CHECKED_IN → CHECKED_OUT`; lưu thời gian thực tế và chuyển phòng sang `CLEANING`.
- Sau khi dọn xong, quản lý hoặc lễ tân chuyển phòng `CLEANING → AVAILABLE`.
- Quản lý/lễ tân hủy booking `PENDING` hoặc `CONFIRMED`; khách chỉ được hủy booking của chính mình trước check-in.
- Mọi thao tác chuyển trạng thái dùng POST, kiểm tra role ở backend, khóa Booking/Room trong transaction và có modal xác nhận.
- Lịch phòng tại `/staff/calendar/` dành cho Manager và Receptionist; booking đã hủy không hiển thị.
- Phần tạo/cập nhật hóa đơn khi check-out được nối ở Giai đoạn 6 sau khi model Invoice và dịch vụ sử dụng được tạo.

## Chức năng Giai đoạn 6

- Manager quản lý danh mục dịch vụ tại `/staff/services/`.
- Manager hoặc Receptionist ghi dịch vụ cho booking đang `CHECKED_IN`; đơn giá và thành tiền được snapshot ở backend.
- Check-out tự tạo hoặc cập nhật hóa đơn trong cùng transaction.
- Tiền phòng = số đêm × giá lúc đặt; tổng tiền gồm phòng, dịch vụ, phụ thu, giảm giá.
- Manager có toàn quyền nghiệp vụ: sửa khách, booking, check-in/out, dịch vụ, phụ thu/giảm giá và ghi nhận thanh toán. Receptionist và Accountant vẫn bị giới hạn theo vai trò.
- Hóa đơn tự chuyển `UNPAID`, `PARTIALLY_PAID`, `PAID` và không cho thanh toán vượt công nợ.
- Customer chỉ xem hóa đơn thuộc booking của chính mình tại `/customer/invoices/` và có nút **Thanh toán ngay** để mô phỏng thanh toán toàn bộ số còn thiếu. Bản demo không kết nối ngân hàng và không trừ tiền thật.
- `seed_demo` có thêm 4 dịch vụ, dịch vụ đã sử dụng, 3 hóa đơn và 2 thanh toán mẫu.

## Chức năng Giai đoạn 7

- Dashboard lấy KPI phòng, booking, khách lưu trú, doanh thu, công suất và công nợ trực tiếp từ database.
- Báo cáo tại `/staff/reports/` dành cho Manager và Accountant, có lọc khoảng ngày và nhóm theo ngày/tháng.
- Doanh thu được tính từ các Payment đã ghi nhận; công suất tính theo số đêm phòng của booking đã xác nhận/đã ở/đã trả.
- Chart.js vẽ doanh thu theo thời gian, số booking, công suất phòng và doanh thu theo loại phòng.
- Hiển thị loại phòng được đặt nhiều nhất, dịch vụ dùng nhiều nhất và tỷ lệ hủy.
- AI không được dùng để tính bất kỳ KPI nào; AI chỉ nhận xét trên số liệu Django đã tổng hợp.

## Chức năng Giai đoạn 8

- AI tư vấn phòng tại `/ai/room-advisor/` cho Customer, Receptionist và Manager; chỉ chọn tối đa 3 phòng từ danh sách Django đã xác nhận còn trống.
- AI sinh bản nháp email xác nhận, hủy và nhắc thanh toán; nhân viên phải sửa/duyệt trước khi mô phỏng gửi.
- AI nhận xét báo cáo tại `/ai/reports/` cho Manager và Accountant, gồm xu hướng, cảnh báo và tối đa 3 gợi ý khuyến mãi.
- Manager xem lịch sử gọi AI tại `/ai/logs/`.
- Timeout, API lỗi, chưa nhập key hoặc hết số dư đều chuyển sang `FALLBACK`; tìm phòng, đặt phòng và báo cáo gốc vẫn hoạt động.
- Payload AI không chứa CCCD/hộ chiếu, mật khẩu, session, thông tin thẻ hoặc tài khoản ngân hàng.

Để gọi Gemini thật, tạo API key tại Google AI Studio rồi mở `.env` và nhập key:

```dotenv
GEMINI_API_KEY=api_key_cua_ban
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Sau khi sửa `.env`, hãy dừng rồi chạy lại `python manage.py runserver`. Nếu chưa có key hoặc API hết số dư, hệ thống tự dùng fallback.

## Hoàn thiện Giai đoạn 9

- Giao diện SPK Hotel responsive, menu công khai thu gọn trên mobile và sidebar theo role.
- Form POST có trạng thái loading và chống bấm lặp ở giao diện; backend vẫn kiểm tra transaction/quyền độc lập.
- Trang lỗi 403/404/500 thân thiện, không hiển thị traceback cho người dùng.

## Điều chỉnh quyền và thanh toán demo mới nhất

- Manager có thể thao tác toàn bộ nghiệp vụ của lễ tân/kế toán bên cạnh quản lý cấu hình và nhân viên.
- Customer có nút **Thanh toán ngay** trên hóa đơn của chính mình; hệ thống mô phỏng thanh toán toàn bộ, cập nhật `PAID` và báo thành công.
- Thanh toán demo không kết nối ngân hàng. Backend vẫn kiểm tra POST, CSRF, quyền sở hữu, khóa hóa đơn và chống thanh toán lặp.
- Bộ kiểm thử hiện có 106 test: Pytest báo `105 passed, 1 skipped`; test skip cần PostgreSQL để kiểm tra row-level lock.
- Production bật HTTPS redirect, secure cookie, HSTS, chống MIME sniffing và clickjacking.
- Có bộ acceptance test mở các trang chính theo từng role và kiểm tra truy cập chéo.
- Xem [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) để cài đặt và [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) để trình bày đồ án.

## Cấu trúc

- `config/settings/`: cấu hình development và production.
- `apps/accounts/`: Custom User Model và xác thực.
- `apps/core/`: trang chung và health check.
- Các app nghiệp vụ còn lại được triển khai theo từng giai đoạn trong `PROJECT_PLAN.md`.
