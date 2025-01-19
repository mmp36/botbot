from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import logging

from database import DatabaseManager
from keyboards import KeyboardManager
from config import Config

logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_premium_duration = State()
    waiting_for_user_id = State()

class AdminHandlers:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup all admin handlers"""
        # Admin commands
        self.router.message.register(self.add_premium_command, Command("add_premium"))
        self.router.message.register(self.remove_premium_command, Command("remove_premium"))
        self.router.message.register(self.check_premium_command, Command("check_premium"))
        self.router.message.register(self.list_premium_command, Command("list_premium"))

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in Config.ADMIN_IDS

    async def add_premium_command(self, message: Message, command: CommandObject):
        """Handle /add_premium command"""
        if not await self.is_admin(message.from_user.id):
            await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        try:
            if not command.args:
                await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/add_premium USER_ID DAYS\n"
                    "مثال: /add_premium 123456789 30"
                )
                return

            args = command.args.split()
            if len(args) != 2:
                await message.reply("❌ لطفاً شناسه کاربر و تعداد روز را وارد کنید.")
                return

            user_id = int(args[0])
            days = int(args[1])

            if days <= 0:
                await message.reply("❌ تعداد روز باید بیشتر از صفر باشد.")
                return

            expiration_date = datetime.now() + timedelta(days=days)
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
            logger.error(f"Error in add_premium_command: {e}")
            await message.reply("❌ خطایی رخ داد.")

    async def remove_premium_command(self, message: Message, command: CommandObject):
        """Handle /remove_premium command"""
        if not await self.is_admin(message.from_user.id):
            await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        try:
            if not command.args:
                await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/remove_premium USER_ID\n"
                    "مثال: /remove_premium 123456789"
                )
                return

            user_id = int(command.args)
            if self.db.remove_premium_status(user_id):
                await message.reply(f"✅ وضعیت پرمیوم کاربر {user_id} با موفقیت حذف شد.")
            else:
                await message.reply("❌ خطا در حذف وضعیت پرمیوم.")

        except ValueError:
            await message.reply("❌ لطفاً شناسه کاربر را به درستی وارد کنید.")
        except Exception as e:
            logger.error(f"Error in remove_premium_command: {e}")
            await message.reply("❌ خطایی رخ داد.")

    async def check_premium_command(self, message: Message, command: CommandObject):
        """Handle /check_premium command"""
        if not await self.is_admin(message.from_user.id):
            await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        try:
            if not command.args:
                await message.reply(
                    "❌ فرمت نادرست. استفاده صحیح:\n"
                    "/check_premium USER_ID\n"
                    "مثال: /check_premium 123456789"
                )
                return

            user_id = int(command.args)
            premium_info = self.db.get_premium_info(user_id)
            
            if premium_info:
                expiration_date = datetime.strptime(
                    premium_info['expiration_date'],
                    '%Y-%m-%d %H:%M:%S'
                )
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
            logger.error(f"Error in check_premium_command: {e}")
            await message.reply("❌ خطایی رخ داد.")

    async def list_premium_command(self, message: Message):
        """Handle /list_premium command"""
        if not await self.is_admin(message.from_user.id):
            await message.reply("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        try:
            premium_users = self.db.get_all_premium_users()
            
            if not premium_users:
                await message.reply("📝 هیچ کاربر پرمیومی یافت نشد.")
                return

            response = "📋 لیست کاربران پرمیوم:\n\n"
            for user in premium_users:
                expiration_date = datetime.strptime(
                    user['expiration_date'],
                    '%Y-%m-%d %H:%M:%S'
                )
                is_active = expiration_date > datetime.now()
                
                response += (
                    f"👤 کاربر: {user['user_id']}\n"
                    f"🔰 وضعیت: {'فعال ✅' if is_active else 'منقضی شده ❌'}\n"
                    f"📅 تاریخ انقضا: {expiration_date.strftime('%Y-%m-%d')}\n"
                    "──────────────\n"
                )

            await message.reply(response)

        except Exception as e:
            logger.error(f"Error in list_premium_command: {e}")
            await message.reply("❌ خطایی رخ داد.")
