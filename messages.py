from config import Config

class Messages:
    WELCOME = """
🌟 به ربات تحلیل کانال خوش آمدید!

با این ربات می‌توانید:
📊 آمار کانال را تحلیل کنید
📈 پیشنهادهای بهبود بگیرید
🎯 عملکرد کانال را بهینه کنید

از منو یک گزینه را انتخاب کنید:
"""

    CHANNEL_REQUEST = """
🔍 لطفاً لینک یا شناسه کانال را وارد کنید:

نمونه‌های صحیح:
• @channel
• https://t.me/channel
• channel

⚠️ نکته: ربات باید در کانال عضو باشد
"""

    HELP = """
❔ راهنمای استفاده:

1️⃣ تحلیل کانال:
• "تحلیل کانال" را انتخاب کنید
• لینک کانال را وارد کنید
• منتظر تحلیل بمانید

2️⃣ اشتراک:
• هر کاربر 2 تحلیل رایگان دارد
• با دعوت هر دوست 5 تحلیل می‌گیرید
• می‌توانید اشتراک بخرید

🆘 نیاز به راهنمایی دارید؟
با پشتیبانی تماس بگیرید: @tech_guypr
"""

    @staticmethod
    def get_subscription_info():
        return f"""
💫 پلن‌های اشتراک:

1️⃣ پلن {Config.PLANS['basic']['name']}:
• {' • '.join(Config.PLANS['basic']['features'])}
• قیمت: {Config.PLANS['basic']['price']:,} تومان

2️⃣ پلن {Config.PLANS['pro']['name']}:
• {' • '.join(Config.PLANS['pro']['features'])}
• قیمت: {Config.PLANS['pro']['price']:,} تومان

برای خرید پلن مورد نظر را انتخاب کنید:
"""

    @staticmethod
    def get_payment_info(plan_type: str, user_id: int):
        plan = Config.PLANS[plan_type]
        return f"""
💳 راهنمای پرداخت پلن {plan['name']}

1️⃣ مبلغ: {plan['price']:,} تومان

2️⃣ شماره کارت:
`{Config.PAYMENT['card_number']}`
به نام: {Config.PAYMENT['card_holder']}

3️⃣ کد پیگیری:
`PAY{user_id}`

📝 مراحل:
1. واریز مبلغ به کارت بالا
2. ارسال رسید و کد پیگیری به @tech_guypr

⚠️ حتماً کد پیگیری را ذکر کنید
"""

    @staticmethod
    def get_referral_text(bot_username: str, user_id: int):
        return f"""
👥 دعوت دوستان

با هر دعوت {Config.REFERRAL_REWARD} تحلیل رایگان بگیرید!

🔗 لینک دعوت شما:
https://t.me/{bot_username}?start=REF{user_id}

راهنما:
1. لینک را کپی کنید
2. برای دوستان بفرستید
3. با عضویت آنها {Config.REFERRAL_REWARD} تحلیل می‌گیرید

🎁 دوستان بیشتر = تحلیل بیشتر
"""