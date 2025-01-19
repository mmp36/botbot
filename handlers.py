import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import DatabaseManager
from analyzer import ChannelAnalyzer
from keyboards import KeyboardManager
from messages import Messages

logger = logging.getLogger(__name__)


class BotStates(StatesGroup):
    """Bot states for FSM"""
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

        # Callback handlers
        self.router.callback_query.register(self.analyze_callback, F.data == "analyze")
        self.router.callback_query.register(self.subscription_callback, F.data == "subscription")
        self.router.callback_query.register(self.referral_callback, F.data == "referral")
        self.router.callback_query.register(self.help_callback, F.data == "help")
        self.router.callback_query.register(self.about_callback, F.data == "about")
        self.router.callback_query.register(self.back_to_main_callback, F.data == "back_to_main")
        self.router.callback_query.register(self.handle_payment_selection, F.data.startswith("pay_"))
        self.router.message.register(self.add_premium, Command("add_premium"))
        self.router.message.register(self.remove_premium, Command("remove_premium"))
        self.router.message.register(self.check_premium, Command("check_premium"))
        self.router.message.register(self.list_premium, Command("list_premium"))
        # State handlers
        self.router.message.register(self.handle_channel_input, BotStates.waiting_for_channel)

    async def start_command(self, message: Message, state: FSMContext):
        """Handle /start command"""
        await state.clear()
        user = message.from_user
        referral_code = f"REF{user.id}"

        # Add user to database
        self.db.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            referral_code
        )

        # Process referral if exists
        text_parts = message.text.split()
        if len(text_parts) > 1 and text_parts[1].startswith("REF"):
            if self.db.process_referral(user.id, text_parts[1]):
                await message.answer("🎉 تبریک! 5 تحلیل رایگان به حساب شما اضافه شد!")

        await message.answer(
            Messages.WELCOME,
            reply_markup=KeyboardManager.main_menu()
        )

    async def analyze_callback(self, callback: CallbackQuery, state: FSMContext):
        """Handle analyze button click"""
        user_data = self.db.get_user(callback.from_user.id)

        if not user_data or user_data[4] <= 0:  # Check remaining analyses
            await callback.message.edit_text(
                "⚠️ تعداد تحلیل‌های رایگان شما تمام شده است!\n\n"
                "برای ادامه می‌توانید:\n"
                "• دوستان خود را دعوت کنید (5 تحلیل رایگان)\n"
                "• اشتراک تهیه کنید",
                reply_markup=KeyboardManager.main_menu()
            )
            return

        await state.set_state(BotStates.waiting_for_channel)
        await callback.message.edit_text(
            Messages.CHANNEL_REQUEST,
            reply_markup=KeyboardManager.back_button()
        )

    async def handle_channel_input(self, message: Message, state: FSMContext):
        """Handle channel link/username input"""
        user_data = self.db.get_user(message.from_user.id)

        if not user_data or user_data[4] <= 0:
            await message.answer(
                "⚠️ تعداد تحلیل‌های رایگان شما تمام شده است!",
                reply_markup=KeyboardManager.main_menu()
            )
            await state.clear()
            return

        status_message = await message.answer("⏳ در حال تحلیل کانال...")

        try:
            # Get channel entity
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

            # Analyze channel
            stats = await self.analyzer.analyze_channel(channel_entity)

            if not stats:
                await status_message.edit_text(
                    "❌ خطا در تحلیل کانال!",
                    reply_markup=KeyboardManager.main_menu()
                )
                await state.clear()
                return

            # Update remaining analyses
            remaining_analyses = user_data[4] - 1
            self.db.update_analyses_count(message.from_user.id, remaining_analyses)

            # Format and send analysis
            analysis = self.analyzer.format_analysis(stats)
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

    async def subscription_callback(self, callback: CallbackQuery):
        """Handle subscription button click"""
        await callback.message.edit_text(
            Messages.get_subscription_info(),
            reply_markup=KeyboardManager.subscription_menu()
        )

    async def handle_payment_selection(self, callback: CallbackQuery):
        """Handle payment plan selection"""
        plan_type = "basic" if callback.data == "pay_basic" else "pro"

        await callback.message.edit_text(
            Messages.get_payment_info(plan_type, callback.from_user.id),
            reply_markup=KeyboardManager.back_button(),
            parse_mode="Markdown"
        )

    async def referral_callback(self, callback: CallbackQuery):
        """Handle referral button click"""
        bot_info = await callback.bot.get_me()
        await callback.message.edit_text(
            Messages.get_referral_text(bot_info.username, callback.from_user.id),
            reply_markup=KeyboardManager.back_button()
        )

    async def help_callback(self, callback: CallbackQuery):
        """Handle help button click"""
        await callback.message.edit_text(
            Messages.HELP,
            reply_markup=KeyboardManager.back_button()
        )

    async def about_callback(self, callback: CallbackQuery):
        """Handle about button click"""
        await callback.message.edit_text(
            Messages.ABOUT,
            reply_markup=KeyboardManager.back_button()
        )
    
    async def back_to_main_callback(self, callback: CallbackQuery, state: FSMContext):
        """Handle back button click"""
        await state.clear()
        await callback.message.edit_text(
            Messages.WELCOME,
            reply_markup=KeyboardManager.main_menu()
        )
    async def add_premium(self, message: Message):
        """Handle /add_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            return await message.reply("⛔️ دسترسی محدود به ادمین")
        
        try:
            args = message.text.split()[1:]
            if len(args) != 2:
                return await message.reply(
                    "⚠️ فرمت صحیح:\n"
                    "/add_premium USER_ID DAYS"
                )
            
            user_id = int(args[0])
            days = int(args[1])
            
            if days <= 0:
                return await message.reply("❌ تعداد روز باید بیشتر از صفر باشد")
            
            expiry_date = datetime.now() + timedelta(days=days)
            if self.db.update_premium_status(user_id, expiry_date):
                await message.reply(
                    f"✅ کاربر {user_id} پرمیوم شد\n"
                    f"📅 تاریخ انقضا: {expiry_date.strftime('%Y-%m-%d')}"
                )
            else:
                await message.reply("❌ خطا در ثبت وضعیت پرمیوم")
                
        except ValueError:
            await message.reply("❌ خطا در فرمت ورودی")
        except Exception as e:
            await message.reply(f"❌ خطای سیستمی: {str(e)}")

    async def remove_premium(self, message: Message):
        """Handle /remove_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            return await message.reply("⛔️ دسترسی محدود به ادمین")
        
        try:
            user_id = int(message.text.split()[1])
            if self.db.remove_premium_status(user_id):
                await message.reply(f"✅ وضعیت پرمیوم کاربر {user_id} حذف شد")
            else:
                await message.reply("❌ خطا در حذف وضعیت پرمیوم")
        except (ValueError, IndexError):
            await message.reply(
                "⚠️ فرمت صحیح:\n"
                "/remove_premium USER_ID"
            )

    async def check_premium(self, message: Message):
        """Handle /check_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            return await message.reply("⛔️ دسترسی محدود به ادمین")
        
        try:
            user_id = int(message.text.split()[1])
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
            await message.reply(
                "⚠️ فرمت صحیح:\n"
                "/check_premium USER_ID"
            )

    async def list_premium(self, message: Message):
        """Handle /list_premium command"""
        if message.from_user.id not in ADMIN_IDS:
            return await message.reply("⛔️ دسترسی محدود به ادمین")
        
        users = self.db.get_all_premium_users()
        if not users:
            return await message.reply("📝 هیچ کاربر پرمیومی یافت نشد")
        
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
