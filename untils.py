"""
Utility functions for the Telegram bot
"""
import datetime
import re

def validate_phone_number(phone_number):
    """
    Validate if the provided string is a valid phone number format
    Returns True if valid, False otherwise
    """
    # Basic phone number validation (can be customized for specific country formats)
    # This validates common Vietnamese phone number formats
    pattern = r'^(0|\+84)([35789][0-9]{8}|[16][0-9]{8}|[2][0-9]{9})$'
    return bool(re.match(pattern, phone_number))

def validate_date_format(date_str):
    """
    Validate if the provided string is in DD/MM/YYYY format
    Returns True if valid, False otherwise
    """
    pattern = r'^([0-2][0-9]|3[0-1])/(0[1-9]|1[0-2])/\d{4}$'
    if not re.match(pattern, date_str):
        return False
    
    # Further validate the date is actually valid
    try:
        day, month, year = map(int, date_str.split('/'))
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

def parse_date(date_str):
    """
    Parse a date string in DD/MM/YYYY format to a datetime object
    """
    if not validate_date_format(date_str):
        raise ValueError("Invalid date format, use DD/MM/YYYY")
    
    day, month, year = map(int, date_str.split('/'))
    return datetime.datetime(year, month, day)

def format_date(date_obj):
    """
    Format a datetime object to DD/MM/YYYY string
    """
    return date_obj.strftime("%d/%m/%Y")

def is_renewal_soon(renewal_date, days_before=1):
    """
    Check if the renewal date is approaching within specified days
    """
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    target_date = today + datetime.timedelta(days=days_before)
    
    # Compare only the date part
    renewal_date = renewal_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return renewal_date.date() == target_date.date()

def format_reminder_message(item_type, identifier, renewal_date, account_name=None):
    """
    Format a reminder message based on item type (phone or account)
    """
    if item_type == "phone":
        return f"⚠️ *NHẮC NHỞ GIA HẠN SỐ ĐIỆN THOẠI* ⚠️\n\nSố điện thoại: *{identifier}*\nNgày gia hạn: *{format_date(renewal_date)}*\n(Ngày mai)"
    elif item_type == "account":
        return f"⚠️ *NHẮC NHỞ GIA HẠN TÀI KHOẢN* ⚠️\n\nSố điện thoại: *{identifier}*\nTài khoản: *{account_name}*\nNgày gia hạn: *{format_date(renewal_date)}*\n(Ngày mai)"
    return None
