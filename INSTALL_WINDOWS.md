# Hướng dẫn cài SPK Hotel trên Windows

## 1. Chuẩn bị

- Python 3.12 trở lên.
- PostgreSQL nếu muốn chạy giống môi trường chính; có thể dùng SQLite để demo nhanh.
- Gemini API key nếu muốn gọi AI thật. Không có key thì hệ thống tự chạy fallback.

## 2. Cài và chạy bằng PowerShell

```powershell
cd hotel_management
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Mở `http://127.0.0.1:8000/`.

Nếu PowerShell chặn activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Cấu hình `.env`

SQLite development:

```dotenv
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=chuoi_bi_mat_tu_tao
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
GEMINI_API_KEY=
```

PostgreSQL:

```dotenv
DATABASE_URL=postgresql://hotel_user:mat_khau@localhost:5432/hotel_management
```

AI thật:

```dotenv
GEMINI_API_KEY=key_moi_cua_ban
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Sau khi đổi `.env`, dừng server bằng `Ctrl+C` rồi chạy lại.

Không gửi Gemini API key trong tin nhắn, ảnh hoặc đưa key vào Git. Nếu key bị lộ, hãy thu hồi và tạo key mới trong Google AI Studio.

## 4. Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản lý | `quanli@hotel.com` | `1` |
| Lễ tân | `letan@hotel.com` | `1` |
| Kế toán | `ketoan@hotel.com` | `1` |
| Khách hàng | `customer1@spkhotel.vn` | `Demo@12345` |

Mật khẩu `1` của các tài khoản nhân viên chỉ dùng để demo local.

## 5. Kiểm tra khi gặp lỗi đăng nhập

Chạy lại dữ liệu mẫu để khôi phục đúng email và mật khẩu demo:

```powershell
python manage.py seed_demo
```

Đảm bảo không nhập khoảng trắng ở đầu/cuối email và dùng đúng tài khoản kế toán là `ketoan@hotel.com`.

## 6. Chạy kiểm thử

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python -m pytest
```

Test đặt phòng đồng thời chỉ chạy đầy đủ trên PostgreSQL. Khi dùng SQLite, test này được skip có chủ đích.
