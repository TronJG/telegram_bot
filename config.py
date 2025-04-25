"""
Configuration settings for the Telegram bot
"""
import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7457507869:AAGIUIVl8hok9smOnGbF1XboElfjo4AEoho")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "7519889601")

# Application settings
MAX_ACCOUNTS_PER_NUMBER = 3
REMINDER_DAYS_BEFORE = 1

# Command help text
HELP_TEXT = """
🇻🇳 QUẢN LÝ SỐ ĐIỆN THOẠI - HƯỚNG DẪN SỬ DỤNG 🇻🇳

Các lệnh cơ bản:
/start - Bắt đầu sử dụng bot
/help - Hiển thị hướng dẫn này

Quản lý số điện thoại:
/themso <số điện thoại> <ngày gia hạn> - Thêm số điện thoại mới
   Ví dụ: /themso 0912345678 25/12/2025
/danhsachso - Liệt kê tất cả số điện thoại
/xoaso <số điện thoại> - Xóa số điện thoại
   Ví dụ: /xoaso 0912345678
/suaso <số điện thoại> <ngày gia hạn mới> - Chỉnh sửa ngày gia hạn
   Ví dụ: /suaso 0912345678 25/01/2026

Quản lý tài khoản:
/themtk <số điện thoại> <tên tài khoản> <ngày gia hạn> - Thêm tài khoản vào số điện thoại
   Ví dụ: /themtk 0912345678 Facebook 25/12/2025
/danhsachtk <số điện thoại> - Liệt kê tài khoản của số điện thoại
   Ví dụ: /danhsachtk 0912345678
/xoatk <số điện thoại> <tên tài khoản> - Xóa tài khoản
   Ví dụ: /xoatk 0912345678 Facebook
/suatk <số điện thoại> <tên tài khoản> <ngày gia hạn mới> - Chỉnh sửa ngày gia hạn tài khoản
   Ví dụ: /suatk 0912345678 Facebook 25/01/2026

Lưu ý:
- Mỗi số điện thoại có thể có tối đa 3 tài khoản
- Bot sẽ gửi thông báo trước 1 ngày khi đến ngày gia hạn
- Định dạng ngày: DD/MM/YYYY (ngày/tháng/năm)
"""
