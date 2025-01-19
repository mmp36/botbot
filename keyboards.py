from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config


class KeyboardManager:
    """Manages all bot keyboards"""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("📊 تحلیل کانال", "analyze"),
            ("💫 خرید اشتراک", "subscription"),
            ("👥 دعوت دوستان", "referral"),
            ("❔ راهنما", "help"),
            ("ℹ️ درباره ربات", "about")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)  # Two buttons per row
        return builder.as_markup()

    @staticmethod
    def subscription_menu() -> InlineKeyboardMarkup:
        """Create subscription plans keyboard"""
        builder = InlineKeyboardBuilder()

        # Add subscription plans
        builder.add(InlineKeyboardButton(
            text=f"پلن پایه - {Config.PLANS['basic']['price']:,} تومان",
            callback_data="pay_basic"
        ))
        builder.add(InlineKeyboardButton(
            text=f"پلن حرفه‌ای - {Config.PLANS['pro']['price']:,} تومان",
            callback_data="pay_pro"
        ))

        # Add back button
        builder.add(InlineKeyboardButton(
            text="🔙 بازگشت به منو",
            callback_data="back_to_main"
        ))

        builder.adjust(1)  # One button per row
        return builder.as_markup()

    @staticmethod
    def back_button() -> InlineKeyboardMarkup:
        """Create back button keyboard"""
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔙 بازگشت به منو",
            callback_data="back_to_main"
        ))
        return builder.as_markup()

    @staticmethod
    def channel_settings() -> InlineKeyboardMarkup:
        """Create channel settings keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("⚙️ تنظیمات تحلیل", "analysis_settings"),
            ("📊 گزارش دوره‌ای", "periodic_report"),
            ("🔔 تنظیمات اعلان", "notification_settings"),
            ("🔙 بازگشت", "back_to_main")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def payment_confirmation(payment_id: str) -> InlineKeyboardMarkup:
        """Create payment confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("✅ تایید پرداخت", f"confirm_payment_{payment_id}"),
            ("❌ انصراف", "cancel_payment"),
            ("🔙 بازگشت", "back_to_main")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def analysis_options() -> InlineKeyboardMarkup:
        """Create analysis options keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("📈 آمار کلی", "general_stats"),
            ("👥 آمار مخاطبین", "audience_stats"),
            ("📊 تحلیل محتوا", "content_analysis"),
            ("⏰ زمان‌های مناسب", "timing_analysis"),
            ("💡 پیشنهادات", "suggestions"),
            ("🔙 بازگشت", "back_to_main")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def support_menu() -> InlineKeyboardMarkup:
        """Create support menu keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("📝 ارسال پیام", "send_message"),
            ("❓ سوالات متداول", "faq"),
            ("📞 تماس با پشتیبانی", "contact_support"),
            ("🔙 بازگشت", "back_to_main")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
        """Create generic confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        buttons = [
            ("✅ تایید", f"confirm_{action}"),
            ("❌ انصراف", f"cancel_{action}"),
            ("🔙 بازگشت", "back_to_main")
        ]
        for text, callback_data in buttons:
            builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def pagination_keyboard(current_page: int, total_pages: int, base_callback: str) -> InlineKeyboardMarkup:
        """Create pagination keyboard"""
        builder = InlineKeyboardBuilder()

        # Add navigation buttons
        if current_page > 1:
            builder.add(InlineKeyboardButton(
                text="◀️ قبلی",
                callback_data=f"{base_callback}_page_{current_page - 1}"
            ))

        builder.add(InlineKeyboardButton(
            text=f"📄 {current_page} از {total_pages}",
            callback_data="current_page"
        ))

        if current_page < total_pages:
            builder.add(InlineKeyboardButton(
                text="بعدی ▶️",
                callback_data=f"{base_callback}_page_{current_page + 1}"
            ))

        # Add back button
        builder.add(InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_main"
        ))

        builder.adjust(3, 1)  # Navigation buttons in one row, back button in another
        return builder.as_markup()