from pathlib import Path


class Config:
    # Bot Configuration
    ADMIN_IDS =336543509
    BOT_TOKEN = "7777044856:AAEsgvgNPANF3KtMl8lqsJAflYknVu7RTgY"
    GEMINI_API_KEY = "AIzaSyD0vBAb0-1cfIzqh7qcTtAoYesVEcxgLfY"
    API_ID= 26154965
    API_HASH = 'e1d80dfcadf6e9ee5a370491ca05b6ab'
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
