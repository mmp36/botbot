import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import DatabaseManager
from analyzer import ChannelAnalyzer
from keyboards import KeyboardManager
from messages import Messages


logger = logging.getLogger(__name__)
ADMIN_IDS =336543509
class BotStates(StatesGroup):
    waiting_for_channel = State()

class BotHandlers:
    def __init__(self, db: DatabaseManager, analyzer: ChannelAnalyzer):
        self.db = db
        self.analyzer = analyzer
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.router.message.register(self.start_command, Command("start"))
        self.router.message.register(self.add_premium_command, Command("add_premium"))
        self.router.message.register(self.remove_premium_command, Command("remove_premium"))
        self.router.message.register(self.check_premium_command, Command("check_premium"))
        self.router.message.register(self.list_premium_command, Command("list_premium"))
        
        # State handlers
        self.router.message.register(self.handle_channel_input, BotStates.waiting_for_channel)

    async def start_command(self, message: Message, state: FSMContext):
        """Handle /start command"""
        await state.clear()
        user = message.from_user
        referral_code = f"REF{user.id}"

        self.db.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            referral_code
        )

        text_parts = message.text.split()
        if len(text_parts) > 1 and text_parts[1].startswith("REF"):
            if self.db.process_referral(user.id, text_parts[1]):
                await message.answer("🎉 5 تحلیل رایگان به حساب شما اضافه شد!")

        await message.answer(
            Messages.WELCOME,
            reply_markup=KeyboardManager.main_menu()
        )

    async def add_premium_command(self, message: Message):
        """Handle /add_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("⛔️ دسترسی محدود به ادمین")
            return

        try:
            parts = message.text.split()
            if len(parts) != 3:
                await message.reply(
                    "⚠️ فرمت صحیح:\n"
                    "/add_premium USER_ID DAYS"
                )
                return

            user_id = int(parts[1])
            days = int(parts[2])

            if days <= 0:
                await message.reply("❌ تعداد روز باید بیشتر از صفر باشد")
                return

            expiry_date = datetime.now() + timedelta(days=days)
            if self.db.update_premium_status(user_id, expiry_date):
                await message.reply(
                    f"✅ کاربر {user_id} پرمیوم شد\n"
                    f"📅 تاریخ انقضا: {expiry_date.strftime('%Y-%m-%d')}"
                )
            else:
                await message.reply("❌ خطا در ثبت وضعیت پرمیوم")

        except (ValueError, IndexError):
            await message.reply("❌ خطا در فرمت ورودی")
        except Exception as e:
            logger.error(f"Error in add_premium_command: {e}")
            await message.reply(f"❌ خطای سیستمی: {str(e)}")

    async def remove_premium_command(self, message: Message):
        """Handle /remove_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("⛔️ دسترسی محدود به ادمین")
            return

        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.reply(
                    "⚠️ فرمت صحیح:\n"
                    "/remove_premium USER_ID"
                )
                return

            user_id = int(parts[1])
            if self.db.remove_premium_status(user_id):
                await message.reply(f"✅ وضعیت پرمیوم کاربر {user_id} حذف شد")
            else:
                await message.reply("❌ خطا در حذف وضعیت پرمیوم")
        except (ValueError, IndexError):
            await message.reply("❌ خطا در فرمت ورودی")
        except Exception as e:
            logger.error(f"Error in remove_premium_command: {e}")
            await message.reply(f"❌ خطای سیستمی: {str(e)}")

    async def check_premium_command(self, message: Message):
        """Handle /check_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("⛔️ دسترسی محدود به ادمین")
            return

        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.reply(
                    "⚠️ فرمت صحیح:\n"
                    "/check_premium USER_ID"
                )
                return

            user_id = int(parts[1])
            info = self.db.get_premium_info(user_id)
            
            if info:
                expiry = datetime.strptime(info['expiration_date'], '%Y-%m-%d %H:%M:%S')
                is_active = expiry > datetime.now()
                
                await message.reply(
                    f"👤 کاربر: {user_id}\n"
                    f"🔰 وضعیت: {'فعال ✅' if is_active else 'منقضی شده ❌'}\n"
                    f"📅 تاریخ انقضا: {expiry.strftime('%Y-%m-%d')}"
                )
            else:
                await message.reply("❌ کاربر پرمیوم نیست")

        except (ValueError, IndexError):
            await message.reply("❌ خطا در فرمت ورودی")
        except Exception as e:
            logger.error(f"Error in check_premium_command: {e}")
            await message.reply(f"❌ خطای سیستمی: {str(e)}")

    async def list_premium_command(self, message: Message):
        """Handle /list_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("⛔️ دسترسی محدود به ادمین")
            return

        try:
            users = self.db.get_all_premium_users()
            if not users:
                await message.reply("📝 هیچ کاربر پرمیومی یافت نشد")
                return

            text = "📋 لیست کاربران پرمیوم:\n\n"
            for user in users:
                expiry = datetime.strptime(user['expiration_date'], '%Y-%m-%d %H:%M:%S')
                is_active = expiry > datetime.now()
                
                text += (
                    f"👤 کاربر: {user['user_id']}\n"
                    f"🔰 وضعیت: {'فعال ✅' if is_active else 'منقضی شده ❌'}\n"
                    f"📅 انقضا: {expiry.strftime('%Y-%m-%d')}\n"
                    "──────────────\n"
                )
            
            await message.reply(text)

        except Exception as e:
            logger.error(f"Error in list_premium_command: {e}")
            await message.reply(f"❌ خطای سیستمی: {str(e)}")

    async def handle_channel_input(self, message: Message, state: FSMContext):
        """Handle channel link/username input"""
        user_data = self.db.get_user(message.from_user.id)
        
        if not user_data:
            await message.answer("❌ خطا در دریافت اطلاعات کاربر")
            await state.clear()
            return

        # Check if user is premium or has remaining analyses
        is_premium = self.db.check_premium_status(message.from_user.id)
        remaining_analyses = user_data[4]  # Index of remaining_analyses in user tuple

        if not is_premium and remaining_analyses <= 0:
            await message.answer(
                "⚠️ تعداد تحلیل‌های رایگان شما تمام شده است!\n\n"
                "برای ادامه می‌توانید:\n"
                "• دوستان خود را دعوت کنید (5 تحلیل رایگان)\n"
                "• اشتراک تهیه کنید",
                reply_markup=KeyboardManager.main_menu()
            )
            await state.clear()
            return

        status_message = await message.answer("⏳ در حال تحلیل کانال...")

        try:
            channel_entity = await self.analyzer.get_channel_entity(message.text)
            
            if not channel_entity:
                await status_message.edit_text(
                    "❌ کانال یافت نشد یا دسترسی ندارید!\n\n"
                    "لطفاً:\n"
                    "• مطمئن شوید لینک صحیح است\n"
                    "• ربات در کانال عضو است\n"
                    "• دسترسی ادمین به ربات داده‌اید",
                    reply_markup=KeyboardManager.main_menu()
                )
                await state.clear()
                return

            stats = await self.analyzer.analyze_channel(channel_entity)
            
            if not stats:
                await status_message.edit_text(
                    "❌ خطا در تحلیل کانال!",
                    reply_markup=KeyboardManager.main_menu()
                )
                await state.clear()
                return

            # Update remaining analyses only for non-premium users
            if not is_premium:
                remaining_analyses = remaining_analyses - 1
                self.db.update_analyses_count(message.from_user.id, remaining_analyses)

            # Format and send analysis
            analysis = self.analyzer.format_analysis(stats)
            if not is_premium:
                analysis += f"\n\n📊 تحلیل‌های باقیمانده: {remaining_analyses}"

            await status_message.edit_text(
                analysis,
                reply_markup=KeyboardManager.main_menu()
            )

        except Exception as e:
            logger.error(f"Error in channel analysis: {e}")
            await status_message.edit_text(
                "❌ خطا در تحلیل کانال!",
                reply_markup=KeyboardManager.main_menu()
            )
        finally:
            await state.clear()
