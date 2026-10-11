# Triển khai SPK Hotel lên Render

## Cách nhanh nhất: dùng Blueprint

1. Đưa thư mục dự án này lên một repository GitHub riêng tư hoặc công khai.
2. Đăng nhập Render, chọn **New > Blueprint**.
3. Kết nối repository GitHub và chọn file `render.yaml` ở thư mục gốc.
4. Khi Render hỏi giá trị `GEMINI_API_KEY`, nhập khóa Gemini của bạn.
5. Chọn **Apply** và chờ Web Service cùng PostgreSQL chuyển sang trạng thái Live.

Render tự chạy `build.sh` để cài thư viện, thu thập static và migrate cơ sở dữ liệu.
Web Service chạy bằng Gunicorn theo cấu hình trong `render.yaml`.

## Tạo dữ liệu trình diễn

Nếu cần tài khoản demo ngay trên lần deploy đầu tiên, tạm thêm dòng sau vào cuối `build.sh`:

```bash
python manage.py seed_demo
```

Sau lần deploy đầu tiên, nên xóa dòng đó để tránh đặt lại dữ liệu/tài khoản demo ở các lần deploy sau.

## Lưu ý dữ liệu

- Không đưa `.env` lên GitHub.
- Dữ liệu nghiệp vụ được lưu trong PostgreSQL, không dùng `db.sqlite3` trên Render.
- Thư mục `media/` của Web Service miễn phí không bền vững. Nếu dùng chức năng tải ảnh phòng, cần dịch vụ lưu trữ ngoài hoặc Persistent Disk trả phí.
- PostgreSQL miễn phí của Render chỉ nên dùng cho demo ngắn hạn.
