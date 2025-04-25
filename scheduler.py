"""
Scheduler module for managing renewal reminders
"""
import logging
from datetime import datetime, time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from config import ADMIN_CHAT_ID, REMINDER_DAYS_BEFORE
from data_manager import DataManager
from utils import format_reminder_message

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """
    Handles scheduling and sending of renewal reminders
    """
    
    def __init__(self, bot: Bot, data_manager: DataManager):
        """Initialize the scheduler with bot and data manager"""
        self.bot = bot
        self.data_manager = data_manager
        self.scheduler = BackgroundScheduler()
        self.chat_id = ADMIN_CHAT_ID
    
    def start(self):
        """Start the scheduler"""
        # Schedule daily check at 8:00 AM
        self.scheduler.add_job(
            self._run_check_renewals_wrapper,
            CronTrigger(hour=8, minute=0),
            name='daily_renewal_check'
        )
        
        # Add a job that runs immediately after starting
        self.scheduler.add_job(
            self._run_check_renewals_wrapper,
            name='initial_renewal_check'
        )
        
        self.scheduler.start()
        logger.info("Reminder scheduler started")
        
    def _run_check_renewals_wrapper(self):
        """
        Non-async wrapper for check_renewals to be used with scheduler
        Creates and runs a new event loop for the async function
        """
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.check_renewals())
        finally:
            loop.close()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Reminder scheduler stopped")
    
    async def check_renewals(self):
        """Check for upcoming renewals and send reminders"""
        logger.info("Checking for upcoming renewals...")
        upcoming_renewals = self.data_manager.get_upcoming_renewals(days_before=REMINDER_DAYS_BEFORE)
        
        if not upcoming_renewals:
            logger.info("No upcoming renewals found")
            return
        
        logger.info(f"Found {len(upcoming_renewals)} upcoming renewals")
        
        # Send reminders for each upcoming renewal
        for renewal in upcoming_renewals:
            try:
                if renewal['type'] == 'phone':
                    message = format_reminder_message(
                        'phone', 
                        renewal['phone_number'], 
                        renewal['renewal_date']
                    )
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent reminder for phone {renewal['phone_number']}")
                
                elif renewal['type'] == 'account':
                    message = format_reminder_message(
                        'account',
                        renewal['phone_number'],
                        renewal['renewal_date'],
                        renewal['account_name']
                    )
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent reminder for account {renewal['account_name']} of phone {renewal['phone_number']}")
            
            except Exception as e:
                logger.error(f"Error sending reminder: {e}")
    
    async def run_manual_check(self):
        """Manually trigger a check for renewals"""
        await self.check_renewals()
        logger.info("Manual renewal check triggered")
