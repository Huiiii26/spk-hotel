# Kịch bản demo đồ án SPK Hotel

## 1. Quản lý

1. Đăng nhập `quanli@hotel.com` / `1`.
2. Giới thiệu dashboard, phòng, booking, doanh thu và công suất.
3. Tạo hoặc khóa/mở một tài khoản nhân viên.
4. Mở loại phòng, phòng và dịch vụ để chứng minh quyền quản lý.
5. Mở Báo cáo, lọc ngày và trình diễn bốn biểu đồ Chart.js.
6. Mở AI phân tích để xem nhận xét và tối đa 3 gợi ý khuyến mãi.
7. Mở Lịch sử AI để chỉ ra `SUCCESS` hoặc `FALLBACK`.
8. Mở một khách hàng và sửa thông tin; sau đó tạo/duyệt booking, check-in/out, ghi dịch vụ hoặc thanh toán để chứng minh Manager có toàn quyền nghiệp vụ.

## 2. Lễ tân

1. Đăng nhập `letan@hotel.com` / `1`.
2. Tìm phòng trống theo ngày; giải thích backend kiểm tra lịch giao nhau.
3. Tạo booking cho khách và xác nhận booking chờ.
4. Check-in: booking thành `CHECKED_IN`, phòng thành `OCCUPIED`.
5. Ghi một dịch vụ sử dụng.
6. Check-out: tạo/cập nhật hóa đơn, phòng thành `CLEANING`.
7. Nhấn hoàn tất dọn phòng để phòng thành `AVAILABLE`.
8. Sinh email xác nhận/hủy và duyệt bản nháp.

## 3. Kế toán

1. Đăng nhập `ketoan@hotel.com` / `1`.
2. Mở danh sách hóa đơn và công nợ.
3. Ghi thanh toán một phần, sau đó thanh toán đủ.
4. Thử nhập vượt công nợ để chứng minh backend từ chối.
5. Sinh email nhắc thanh toán.
6. Mở báo cáo và AI nhận xét/gợi ý khuyến mãi.

## 4. Khách hàng

1. Đăng nhập `customer1@spkhotel.vn` / `Demo@12345` hoặc tự đăng ký tài khoản mới.
2. Cập nhật hồ sơ, tìm phòng và dùng AI tư vấn phòng.
3. Tạo booking; trạng thái phải là `PENDING`.
4. Xem booking và hóa đơn của chính mình.
5. Thử đổi ID booking/hóa đơn trên URL; dữ liệu người khác không được hiển thị.
6. Hủy booking của mình trước check-in.
7. Mở hóa đơn còn thiếu, nhấn **Thanh toán ngay**, xác nhận và kiểm tra thông báo **Thanh toán thành công** cùng trạng thái `PAID`.
8. Giải thích đây là giao dịch mô phỏng cho đồ án, không kết nối hoặc trừ tiền ngân hàng thật.

## 5. Trình diễn fallback AI

1. Để trống `GEMINI_API_KEY` rồi khởi động lại server.
2. Dùng AI tư vấn phòng: hệ thống vẫn trả phòng hợp lệ theo bộ lọc.
3. Sinh email: Django dùng mẫu email tĩnh.
4. Phân tích báo cáo: số liệu gốc vẫn hiển thị, AI báo trạng thái fallback.
5. Nhấn mạnh rằng AI chỉ hỗ trợ, không chặn đặt phòng, hóa đơn hoặc thanh toán.
