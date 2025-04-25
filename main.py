"""
Main application file - includes both Telegram bot and Flask web app
This dual-mode file supports both:
1. Running as a Telegram bot directly (if run with 'python main.py')
2. Running as a Flask web application (if imported by Gunicorn)
"""
import logging
import sys
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    MessageHandler,
    filters
)

from config import BOT_TOKEN, ADMIN_CHAT_ID, HELP_TEXT, MAX_ACCOUNTS_PER_NUMBER
from data_manager import DataManager
from scheduler import ReminderScheduler
from utils import validate_phone_number, validate_date_format, parse_date, format_date

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize data manager
data_manager = DataManager()

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued"""
    await update.message.reply_text(
        "👋 Chào mừng đến với Bot Quản lý Số Điện Thoại!\n\n"
        "Bot này giúp bạn quản lý số điện thoại và tài khoản liên kết, "
        "đồng thời gửi thông báo trước khi đến ngày gia hạn.\n\n"
        "Gõ /help để xem hướng dẫn sử dụng chi tiết."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued"""
    await update.message.reply_text(HELP_TEXT)

async def add_phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new phone number with renewal date"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 2:
        command = update.message.text.split()[0]
        if '/themso' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/themso <số điện thoại> <ngày gia hạn>\n"
                "Ví dụ: /themso 0912345678 25/12/2025"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/add_phone <số điện thoại> <ngày gia hạn>\n"
                "Ví dụ: /add_phone 0912345678 25/12/2025"
            )
        return
    
    phone_number = context.args[0]
    renewal_date_str = context.args[1]
    
    # Validate phone number
    if not validate_phone_number(phone_number):
        await update.message.reply_text("❌ Số điện thoại không hợp lệ.")
        return
    
    # Validate date format
    if not validate_date_format(renewal_date_str):
        await update.message.reply_text(
            "❌ Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY."
        )
        return
    
    try:
        # Parse the date string to datetime object
        renewal_date = parse_date(renewal_date_str)
        
        # Add the phone number
        success = data_manager.add_phone(phone_number, renewal_date)
        
        if success:
            await update.message.reply_text(
                f"✅ Đã thêm số điện thoại {phone_number} với ngày gia hạn {renewal_date_str}."
            )
        else:
            await update.message.reply_text(
                f"❌ Số điện thoại {phone_number} đã tồn tại."
            )
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def list_phones_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all phone numbers with their renewal dates"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    phones = data_manager.get_all_phones()
    
    if not phones:
        await update.message.reply_text("📱 Không có số điện thoại nào trong danh sách.")
        return
    
    message = "📱 DANH SÁCH SỐ ĐIỆN THOẠI\n\n"
    
    for phone, data in phones.items():
        renewal_date = format_date(data['renewal_date'])
        account_count = len(data['accounts'])
        
        message += f"{phone}\n"
        message += f"📅 Ngày gia hạn: {renewal_date}\n"
        message += f"👤 Số tài khoản: {account_count}/3\n\n"
    
    await update.message.reply_text(message)

async def delete_phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a phone number"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 1:
        command = update.message.text.split()[0]
        if '/xoaso' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/xoaso <số điện thoại>\n"
                "Ví dụ: /xoaso 0912345678"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/delete_phone <số điện thoại>\n"
                "Ví dụ: /delete_phone 0912345678"
            )
        return
    
    phone_number = context.args[0]
    
    # Check if phone exists before deleting
    if data_manager.get_phone(phone_number) is None:
        await update.message.reply_text(f"❌ Số điện thoại {phone_number} không tồn tại.")
        return
    
    # Confirm and delete
    success = data_manager.delete_phone(phone_number)
    
    if success:
        await update.message.reply_text(f"✅ Đã xóa số điện thoại {phone_number} và tất cả tài khoản liên kết.")
    else:
        await update.message.reply_text(f"❌ Không thể xóa số điện thoại {phone_number}.")

async def edit_phone_date_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit renewal date for a phone number"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 2:
        command = update.message.text.split()[0]
        if '/suaso' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/suaso <số điện thoại> <ngày gia hạn mới>\n"
                "Ví dụ: /suaso 0912345678 25/01/2026"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/edit_phone_date <số điện thoại> <ngày gia hạn mới>\n"
                "Ví dụ: /edit_phone_date 0912345678 25/01/2026"
            )
        return
    
    phone_number = context.args[0]
    new_date_str = context.args[1]
    
    # Check if phone exists
    if data_manager.get_phone(phone_number) is None:
        await update.message.reply_text(f"❌ Số điện thoại {phone_number} không tồn tại.")
        return
    
    # Validate date format
    if not validate_date_format(new_date_str):
        await update.message.reply_text(
            "❌ Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY."
        )
        return
    
    try:
        # Parse the date string to datetime object
        new_date = parse_date(new_date_str)
        
        # Update the phone renewal date
        success = data_manager.update_phone_renewal(phone_number, new_date)
        
        if success:
            await update.message.reply_text(
                f"✅ Đã cập nhật ngày gia hạn cho số {phone_number} thành {new_date_str}."
            )
        else:
            await update.message.reply_text(f"❌ Không thể cập nhật ngày gia hạn cho số {phone_number}.")
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def add_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an account to a phone number"""
    logger.info(f"Processing add_account command: {update.message.text}")
    logger.info(f"Args: {context.args}")
    
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 3:
        # Kiểm tra lệnh nào được sử dụng (tiếng Anh hay tiếng Việt)
        command = update.message.text.split()[0]
        logger.info(f"Command with insufficient args: {command}")
        if '/themtk' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/themtk <số điện thoại> <tên tài khoản> <ngày gia hạn>\n"
                "Ví dụ: /themtk 0912345678 Facebook 25/12/2025"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/add_account <số điện thoại> <tên tài khoản> <ngày gia hạn>\n"
                "Ví dụ: /add_account 0912345678 Facebook 25/12/2025"
            )
        return
    
    phone_number = context.args[0]
    account_name = context.args[1]
    renewal_date_str = context.args[2]
    
    logger.info(f"Adding account: Phone={phone_number}, Account={account_name}, Date={renewal_date_str}")
    
    # Check if phone exists
    if data_manager.get_phone(phone_number) is None:
        await update.message.reply_text(f"❌ Số điện thoại {phone_number} không tồn tại.")
        return
    
    # Validate date format
    if not validate_date_format(renewal_date_str):
        await update.message.reply_text(
            "❌ Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY."
        )
        return
    
    try:
        # Parse the date string to datetime object
        renewal_date = parse_date(renewal_date_str)
        
        # Add the account
        logger.info(f"Calling data_manager.add_account with: {phone_number}, {account_name}, {renewal_date}")
        success, message = data_manager.add_account(phone_number, account_name, renewal_date)
        logger.info(f"Result: success={success}, message={message}")
        
        await update.message.reply_text(
            f"{'✅' if success else '❌'} {message}"
        )
    
    except ValueError as e:
        logger.error(f"Error adding account: {str(e)}")
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def list_accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all accounts for a phone number"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 1:
        # Kiểm tra lệnh nào được sử dụng
        command = update.message.text.split()[0]
        if '/danhsachtk' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/danhsachtk <số điện thoại>\n"
                "Ví dụ: /danhsachtk 0912345678"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/list_accounts <số điện thoại>\n"
                "Ví dụ: /list_accounts 0912345678"
            )
        return
    
    phone_number = context.args[0]
    
    # Check if phone exists
    phone_data = data_manager.get_phone(phone_number)
    if phone_data is None:
        await update.message.reply_text(f"❌ Số điện thoại {phone_number} không tồn tại.")
        return
    
    accounts = phone_data.get('accounts', [])
    
    if not accounts:
        await update.message.reply_text(f"📱 Số điện thoại {phone_number} chưa có tài khoản nào.")
        return
    
    message = f"👤 TÀI KHOẢN CỦA SỐ {phone_number}\n\n"
    
    for i, account in enumerate(accounts, 1):
        account_name = account['name']
        renewal_date = format_date(account['renewal_date'])
        
        message += f"{i}. {account_name}\n"
        message += f"📅 Ngày gia hạn: {renewal_date}\n\n"
    
    await update.message.reply_text(message)

async def delete_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete an account from a phone number"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 2:
        command = update.message.text.split()[0]
        if '/xoatk' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/xoatk <số điện thoại> <tên tài khoản>\n"
                "Ví dụ: /xoatk 0912345678 Facebook"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/delete_account <số điện thoại> <tên tài khoản>\n"
                "Ví dụ: /delete_account 0912345678 Facebook"
            )
        return
    
    phone_number = context.args[0]
    account_name = context.args[1]
    
    # Delete account
    success, message = data_manager.delete_account(phone_number, account_name)
    
    await update.message.reply_text(
        f"{'✅' if success else '❌'} {message}"
    )

async def edit_account_date_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit renewal date for an account"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    
    # Check if correct arguments are provided
    if len(context.args) < 3:
        command = update.message.text.split()[0]
        if '/suatk' in command:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/suatk <số điện thoại> <tên tài khoản> <ngày gia hạn mới>\n"
                "Ví dụ: /suatk 0912345678 Facebook 25/01/2026"
            )
        else:
            await update.message.reply_text(
                "❌ Sai cú pháp. Vui lòng sử dụng:\n"
                "/edit_account_date <số điện thoại> <tên tài khoản> <ngày gia hạn mới>\n"
                "Ví dụ: /edit_account_date 0912345678 Facebook 25/01/2026"
            )
        return
    
    phone_number = context.args[0]
    account_name = context.args[1]
    new_date_str = context.args[2]
    
    # Validate date format
    if not validate_date_format(new_date_str):
        await update.message.reply_text(
            "❌ Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY."
        )
        return
    
    try:
        # Parse the date string to datetime object
        new_date = parse_date(new_date_str)
        
        # Update the account renewal date
        success, message = data_manager.update_account_renewal(phone_number, account_name, new_date)
        
        await update.message.reply_text(
            f"{'✅' if success else '❌'} {message}"
        )
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to unknown commands"""
    await update.message.reply_text(
        "❓ Lệnh không được nhận dạng. Gõ /help để xem danh sách lệnh."
    )

def main() -> None:
    """Start the bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    # Lệnh tiếng Anh
    application.add_handler(CommandHandler("add_phone", add_phone_command))
    application.add_handler(CommandHandler("list_phones", list_phones_command))
    application.add_handler(CommandHandler("delete_phone", delete_phone_command))
    application.add_handler(CommandHandler("edit_phone_date", edit_phone_date_command))
    application.add_handler(CommandHandler("add_account", add_account_command))
    application.add_handler(CommandHandler("list_accounts", list_accounts_command))
    application.add_handler(CommandHandler("delete_account", delete_account_command))
    application.add_handler(CommandHandler("edit_account_date", edit_account_date_command))
    # Lệnh tiếng Việt
    application.add_handler(CommandHandler("themso", add_phone_command))
    application.add_handler(CommandHandler("danhsachso", list_phones_command))
    application.add_handler(CommandHandler("xoaso", delete_phone_command))
    application.add_handler(CommandHandler("suaso", edit_phone_date_command))
    application.add_handler(CommandHandler("themtk", add_account_command))
    application.add_handler(CommandHandler("danhsachtk", list_accounts_command))
    application.add_handler(CommandHandler("xoatk", delete_account_command))
    application.add_handler(CommandHandler("suatk", edit_account_date_command))
    
    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Initialize and start the scheduler
    reminder_scheduler = ReminderScheduler(application.bot, data_manager)
    reminder_scheduler.start()
    
    # Start the Bot
    application.run_polling()
    
    # Stop the scheduler when the bot is stopped
    reminder_scheduler.stop()

# Flask web application code
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os

# Create Flask app instance for use with Gunicorn
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Routes for adding and managing phones via web interface
@app.route('/add_phone', methods=['POST'])
def add_phone():
    """Add a new phone number via web interface"""
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        renewal_date_str = request.form.get('renewal_date')
        
        # Validate phone number
        if not validate_phone_number(phone_number):
            flash('Số điện thoại không hợp lệ', 'danger')
            return redirect(url_for('index'))
        
        # Validate date format
        if not validate_date_format(renewal_date_str):
            flash('Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY', 'danger')
            return redirect(url_for('index'))
        
        try:
            # Parse the date string to datetime object
            renewal_date = parse_date(renewal_date_str)
            
            # Add the phone number
            success = data_manager.add_phone(phone_number, renewal_date)
            
            if success:
                flash(f'Đã thêm số điện thoại {phone_number} với ngày gia hạn {renewal_date_str}', 'success')
            else:
                flash(f'Số điện thoại {phone_number} đã tồn tại', 'warning')
            
        except ValueError as e:
            flash(f'Lỗi: {str(e)}', 'danger')
        
        return redirect(url_for('index'))

@app.route('/add_account', methods=['POST'])
def add_account():
    """Add a new account to a phone number via web interface"""
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        account_name = request.form.get('account_name')
        renewal_date_str = request.form.get('renewal_date')
        
        # Check if phone exists
        if data_manager.get_phone(phone_number) is None:
            flash(f'Số điện thoại {phone_number} không tồn tại', 'danger')
            return redirect(url_for('index'))
        
        # Validate date format
        if not validate_date_format(renewal_date_str):
            flash('Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY', 'danger')
            return redirect(url_for('phone_detail', phone_number=phone_number))
        
        try:
            # Parse the date string to datetime object
            renewal_date = parse_date(renewal_date_str)
            
            # Add the account
            success, message = data_manager.add_account(phone_number, account_name, renewal_date)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'warning')
            
        except ValueError as e:
            flash(f'Lỗi: {str(e)}', 'danger')
        
        return redirect(url_for('phone_detail', phone_number=phone_number))

@app.route('/')
def index():
    """Home page - show all phone numbers"""
    phones = data_manager.get_all_phones()
    return render_template('index.html', phones=phones, format_date=format_date)

@app.route('/phone/<phone_number>')
def phone_detail(phone_number):
    """Detail page for a specific phone number"""
    phone_data = data_manager.get_phone(phone_number)
    if not phone_data:
        flash('Số điện thoại không tồn tại', 'danger')
        return redirect(url_for('index'))
        
    return render_template('phone_detail.html', phone_number=phone_number, phone_data=phone_data, format_date=format_date)

@app.route('/api/phones', methods=['GET'])
def get_phones():
    """API to get all phones as JSON"""
    phones = data_manager.get_all_phones()
    
    # Convert datetime objects to strings for JSON serialization
    serializable_data = {}
    for phone, phone_data in phones.items():
        serializable_data[phone] = phone_data.copy()
        if isinstance(phone_data.get('renewal_date'), datetime):
            serializable_data[phone]['renewal_date'] = format_date(phone_data['renewal_date'])
        
        serializable_data[phone]['accounts'] = []
        for account in phone_data.get('accounts', []):
            account_copy = account.copy()
            if isinstance(account.get('renewal_date'), datetime):
                account_copy['renewal_date'] = format_date(account['renewal_date'])
            serializable_data[phone]['accounts'].append(account_copy)
    
    return jsonify(serializable_data)

@app.route('/api/upcoming_renewals', methods=['GET'])
def get_upcoming_renewals():
    """API to get upcoming renewals as JSON"""
    days_before = request.args.get('days', default=1, type=int)
    renewals = data_manager.get_upcoming_renewals(days_before=days_before)
    
    # Convert datetime objects to strings for JSON serialization
    for renewal in renewals:
        if isinstance(renewal.get('renewal_date'), datetime):
            renewal['renewal_date'] = format_date(renewal['renewal_date'])
    
    return jsonify(renewals)

# Main function for running the Telegram bot
if __name__ == "__main__":
    # When this file is run directly, start the bot
    main()
