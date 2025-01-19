from pathlib import Path


class Config:
    # Bot Configuration
   BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Telegram API Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

    # Database Configuration
    DB_NAME = "bot_database.db"
    DB_PATH = Path(__file__).parent / DB_NAME

    # Logging Configuration
    LOG_FILE = "bot.log"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Subscription Plans
    PLANS = {
        "basic": {
            "name": "پایه",
            "price": 50000,
            "analyses": 5,
            "features": ["تحلیل ۵ کانال"]
        },
        "pro": {
            "name": "حرفه‌ای",
            "price": 100000,
            "analyses": float('inf'),
            "features": ["تحلیل نامحدود", "گزارش هفتگی"]
        }
    }

    # Payment Information
    PAYMENT = {
        "card_number": "5892-1014-3689-6993",
        "card_holder": "آرش فراهانی"
    }

    # Referral System
    REFERRAL_REWARD = 5  # Number of free analyses for referrals

    # Time Zone
    IRAN_TZ_OFFSET = {"hours": 3, "minutes": 30}

    # Analysis Settings
    MAX_MESSAGES_ANALYZE = 100
    ANALYSIS_DAYS = 7
