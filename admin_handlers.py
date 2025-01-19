from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import DatabaseManager
from keyboards import KeyboardManager
from config import ADMIN_IDS  # Add your admin IDs to config.py

router = Router()

class AdminStates(StatesGroup):
    waiting_for_premium_duration = State()
    waiting_for_user_id = State()

class AdminHandlers:
    def __init__(self, db: DatabaseManager):
        self.db = db

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_IDS

    @router.message(Command("add_premium"))
    async def add_premium_command(self, message: Message, command: CommandObject):
        """Handle /add_premium command
        Usage: /add_premium user_id days
        Example: /add_premium 123456789 30"""
        
        if not await self.is_admin(message.from_user.id):
            return await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")

        try:
            args = command.args.split()
            if len(args) != 2:
                return await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/add_premium USER_ID DAYS\n"
                    "مثال: /add_premium 123456789 30"
                )

            user_id = int(args[0])
            days = int(args[1])

            if days <= 0:
                return await message.reply("❌ تعداد روز باید بیشتر از صفر باشد.")

            # Calculate expiration date
            expiration_date = datetime.now() + timedelta(days=days)
            
            # Update user's premium status
            if self.db.update_premium_status(user_id, expiration_date):
                await message.reply(
                    f"✅ کاربر {user_id} با موفقیت پرمیوم شد!\n"
                    f"📅 تاریخ انقضا: {expiration_date.strftime('%Y-%m-%d')}"
                )
            else:
                await message.reply("❌ خطا در ثبت کاربر پرمیوم.")

        except ValueError:
            await message.reply("❌ لطفاً شناسه کاربر و تعداد روز را به درستی وارد کنید.")
        except Exception as e:
            await message.reply(f"❌ خطایی رخ داد: {str(e)}")

    @router.message(Command("remove_premium"))
    async def remove_premium_command(self, message: Message, command: CommandObject):
        """Handle /remove_premium command
        Usage: /remove_premium user_id"""
        
        if not await self.is_admin(message.from_user.id):
            return await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")

        try:
            if not command.args:
                return await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/remove_premium USER_ID\n"
                    "مثال: /remove_premium 123456789"
                )

            user_id = int(command.args)
            
            # Remove premium status
            if self.db.remove_premium_status(user_id):
                await message.reply(f"✅ وضعیت پرمیوم کاربر {user_id} با موفقیت حذف شد.")
            else:
                await message.reply("❌ خطا در حذف وضعیت پرمیوم.")

        except ValueError:
            await message.reply("❌ لطفاً شناسه کاربر را به درستی وارد کنید.")
        except Exception as e:
            await message.reply(f"❌ خطایی رخ داد: {str(e)}")

    @router.message(Command("check_premium"))
    async def check_premium_command(self, message: Message, command: CommandObject):
        """Handle /check_premium command
        Usage: /check_premium user_id"""
        
        if not await self.is_admin(message.from_user.id):
            return await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")

        try:
            if not command.args:
                return await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/check_premium USER_ID\n"
                    "مثال: /check_premium 123456789"
                )

            user_id = int(command.args)
            premium_info = self.db.get_premium_info(user_id)
            
            if premium_info:
                expiration_date = datetime.strptime(premium_info['expiration_date'], '%Y-%m-%d %H:%M:%S')
                is_active = expiration_date > datetime.now()
                
                await message.reply(
                    f"👤 اطلاعات کاربر {user_id}:\n"
                    f"🔰 وضعیت: {'فعال ✅' if is_active else 'منقضی شده ❌'}\n"
                    f"📅 تاریخ انقضا: {expiration_date.strftime('%Y-%m-%d')}"
                )
            else:
                await message.reply("❌ این کاربر پرمیوم نیست.")

        except ValueError:
            await message.reply("❌ لطفاً شناسه کاربر را به درستی وارد کنید.")
        except Exception as e:
            await message.reply(f"❌ خطایی رخ داد: {str(e)}")

    @router.message(Command("list_premium"))
    async def list_premium_command(self, message: Message):
        """Handle /list_premium command to list all premium users"""
        
        if not await self.is_admin(message.from_user.id):
            return await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")

        try:
            premium_users = self.db.get_all_premium_users()
            
            if not premium_users:
                return await message.reply("📝 هیچ کاربر پرمیومی یافت نشد.")

            response = "📋 لیست کاربران پرمیوم:\n\n"
            for user in premium_users:
                expiration_date = datetime.strptime(user['expiration_date'], '%Y-%m-%d %H:%M:%S')
                is_active = expiration_date > datetime.now()
                
                response += (
                    f"👤 کاربر: {user['user_id']}\n"
                    f"🔰 وضعیت: {'فعال ✅' if is_active else 'منقضی شده ❌'}\n"
                    f"📅 تاریخ انقضا: {expiration_date.strftime('%Y-%m-%d')}\n"
                    "──────────────\n"
                )

            await message.reply(response)
