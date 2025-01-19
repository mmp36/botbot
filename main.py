import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import google.generativeai as genai

from config import Config
from database import DatabaseManager
from analyzer import ChannelAnalyzer
from handlers import BotHandlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=Config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Config.LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot function"""
    try:
        # Initialize bot and dispatcher
        bot = Bot(token=Config.BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())

        # Configure Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)

        # Initialize components
        db = DatabaseManager()
        analyzer = ChannelAnalyzer()

        # Start analyzer
        if not await analyzer.start():
            logger.error("Failed to start channel analyzer")
            return

        # Initialize and setup handlers
        handlers = BotHandlers(db, analyzer)
        dp.include_router(handlers.router)

        # Start polling
        logger.info("Bot is starting...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Bot is stopping...")
        if analyzer:
            await analyzer.stop()
        if bot:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
        sys.exit(1)