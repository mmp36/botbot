import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from telethon import TelegramClient
from telethon.tl.types import Channel, Message
import google.generativeai as genai

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ChannelStats:
    """Data class for channel statistics"""
    total_messages: int = 0
    views: int = 0
    forwards: int = 0
    replies: int = 0
    media_count: int = 0
    active_hours: Dict[int, int] = None
    engagement_rate: float = 0.0
    post_frequency: float = 0.0
    daily_stats: Dict[str, int] = None
    media_types: Dict[str, int] = None
    content_analysis: str = ""
    post_samples: List[Dict] = None

    def __post_init__(self):
        """Initialize default dictionaries"""
        self.active_hours = self.active_hours or {}
        self.daily_stats = self.daily_stats or {}
        self.post_samples = self.post_samples or []
        self.media_types = self.media_types or {
            'photo': 0,
            'video': 0,
            'document': 0,
            'audio': 0,
            'other': 0
        }


class ChannelAnalyzer:
    def __init__(self):
        """Initialize channel analyzer"""
        self.client: Optional[TelegramClient] = None
        self.model = genai.GenerativeModel('gemini-pro')
        self.iran_tz = timezone(timedelta(**Config.IRAN_TZ_OFFSET))

    async def start(self) -> bool:
        """Start Telegram client"""
        try:
            if not self.client:
                self.client = TelegramClient(
                    'bot_session',
                    Config.API_ID,
                    Config.API_HASH
                )
                await self.client.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            return False

    async def stop(self):
        """Stop Telegram client"""
        try:
            if self.client:
                await self.client.disconnect()
        except Exception as e:
            logger.error(f"Error stopping client: {e}")

    def _clean_channel_input(self, channel_input: str) -> str:
        """Clean and format channel input"""
        if channel_input.startswith(('https://t.me/', 't.me/')):
            channel_input = channel_input.split('/')[-1]
        if not channel_input.startswith('@'):
            channel_input = '@' + channel_input
        return channel_input

    async def get_channel_entity(self, channel_input: str) -> Optional[Channel]:
        """Get channel entity from input string"""
        try:
            channel_input = self._clean_channel_input(channel_input)
            entity = await self.client.get_entity(channel_input)
            if not isinstance(entity, Channel):
                logger.warning(f"Entity {channel_input} is not a channel")
                return None
            return entity
        except Exception as e:
            logger.error(f"Failed to get channel entity for {channel_input}: {e}")
            return None

    def _update_media_stats(self, message: Message, stats: ChannelStats):
        """Update media statistics"""
        if not message.media:
            return

        stats.media_count += 1
        media_type = type(message.media).__name__.lower()

        if 'photo' in media_type:
            stats.media_types['photo'] += 1
        elif 'video' in media_type:
            stats.media_types['video'] += 1
        elif 'document' in media_type:
            stats.media_types['document'] += 1
        elif 'audio' in media_type:
            stats.media_types['audio'] += 1
        else:
            stats.media_types['other'] += 1

    def _update_post_sample(self, message: Message, stats: ChannelStats):
        """Update post samples"""
        if len(stats.post_samples) >= 5 or not message.text:
            return

        stats.post_samples.append({
            'text': message.text[:200] + '...' if len(message.text) > 200 else message.text,
            'views': getattr(message, 'views', 0) or 0,
            'forwards': getattr(message, 'forwards', 0) or 0,
            'date': message.date.astimezone(self.iran_tz),
            'has_media': bool(message.media)
        })

    async def _analyze_content(self, message_texts: List[str]) -> str:
        """Analyze channel content using AI"""
        try:
            if not message_texts:
                return "محتوای کافی برای تحلیل یافت نشد."

            analysis_prompt = f"""
            لطفا محتوای این کانال تلگرام را تحلیل کنید و به فارسی پاسخ دهید:

            1. موضوعات و تم‌های اصلی
            2. سبک نگارش و لحن محتوا
            3. الگوهای تعامل مخاطبان
            4. پیشنهادات برای بهبود محتوا

            نمونه پست‌های اخیر:
            {' '.join(message_texts[:10])}
            """

            response = self.model.generate_content(analysis_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return "خطا در تحلیل هوشمند محتوا"

    async def analyze_channel(self, channel_entity: Channel) -> Optional[ChannelStats]:
        """Analyze channel and return statistics"""
        try:
            stats = ChannelStats()
            message_texts = []
            current_day = None
            day_message_count = 0

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=Config.ANALYSIS_DAYS)

            async for message in self.client.iter_messages(
                    channel_entity,
                    limit=Config.MAX_MESSAGES_ANALYZE
            ):
                if message.date < start_date:
                    break

                # Convert to Iran timezone
                message_date = message.date.astimezone(self.iran_tz)
                message_day = message_date.date()

                # Update daily stats
                if current_day != message_day:
                    if current_day is not None:
                        stats.daily_stats[current_day.isoformat()] = day_message_count
                    current_day = message_day
                    day_message_count = 1
                else:
                    day_message_count += 1

                # Update basic stats
                stats.total_messages += 1
                stats.views += getattr(message, 'views', 0) or 0
                stats.forwards += getattr(message, 'forwards', 0) or 0
                if hasattr(message, 'replies') and message.replies:
                    stats.replies += message.replies.replies or 0

                # Update hour stats
                hour = message_date.hour
                stats.active_hours[hour] = stats.active_hours.get(hour, 0) + 1

                # Update media stats
                self._update_media_stats(message, stats)

                # Update post samples
                self._update_post_sample(message, stats)

                # Collect message text for analysis
                if message.text:
                    message_texts.append(message.text)

            # Add final day's stats
            if current_day:
                stats.daily_stats[current_day.isoformat()] = day_message_count

            # Calculate derived stats
            if stats.total_messages > 0:
                stats.engagement_rate = ((stats.views + stats.forwards + stats.replies) /
                                         (stats.total_messages * 100))
                stats.post_frequency = stats.total_messages / Config.ANALYSIS_DAYS

                # Get AI content analysis
                stats.content_analysis = await self._analyze_content(message_texts)

            return stats

        except Exception as e:
            logger.error(f"Channel analysis failed: {e}")
            return None

    def format_analysis(self, stats: ChannelStats) -> str:
        """Format channel statistics into readable Persian text"""
        if not stats:
            return "❌ خطا در تحلیل کانال"

        # Format active hours
        active_hours = sorted(stats.active_hours.items(),
                              key=lambda x: x[1],
                              reverse=True)[:5]

        total_posts = sum(stats.active_hours.values())
        active_hours_text = []

        for hour, count in active_hours:
            percentage = (count / total_posts) * 100
            time_str = f"{hour:02d}:00"
            active_hours_text.append(
                f"• ساعت {time_str} - {count} پست ({percentage:.1f}٪)"
            )

        active_hours_formatted = "\n".join(active_hours_text)

        # Format media statistics
        media_text = ""
        if stats.media_count > 0:
            media_text = "\n\n📊 آمار رسانه‌ها:"
            for media_type, count in stats.media_types.items():
                if count > 0:
                    percentage = (count / stats.media_count) * 100
                    media_text += f"\n• {media_type}: {count} ({percentage:.1f}٪)"

        # Format sample posts
        sample_text = ""
        if stats.post_samples:
            sample_text = "\n\n📝 نمونه پست‌های اخیر:\n"
            for idx, post in enumerate(stats.post_samples, 1):
                sample_text += f"""
• پست {idx}:
  - متن: {post['text']}
  - بازدید: {post['views']:,}
  - فوروارد: {post['forwards']:,}
  - تاریخ: {post['date'].strftime('%Y-%m-%d %H:%M')}
  - رسانه: {'دارد' if post['has_media'] else 'ندارد'}
"""

        return f"""
📊 تحلیل آماری کانال - {Config.ANALYSIS_DAYS} روز گذشته

📈 آمار کلی:
• تعداد پست‌ها: {stats.total_messages:,}
• میانگین بازدید: {stats.views // max(stats.total_messages, 1):,}
• نرخ تعامل: {stats.engagement_rate:.1f}%
• تعداد فوروارد: {stats.forwards:,}
• تعداد کامنت: {stats.replies:,}

🎯 عملکرد محتوا:
• پست‌های رسانه‌دار: {stats.media_count:,}
• میانگین پست روزانه: {stats.post_frequency:.1f}{media_text}

⏰ ساعات فعال:
{active_hours_formatted}

💡 تحلیل هوشمند:
{stats.content_analysis}{sample_text}
"""