import os
import sys
import subprocess
import time

# 1. تثبيت المكتبات تلقائياً
def install_packages():
    required_packages = ["pyTelegramBotAPI", "Pillow", "google-genai"]
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

import telebot
from google import genai
from PIL import Image
import io
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 2. السيرفر الوهمي لاستقرار Render
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Engine is Ready!")
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ⭐ الحسم: تطهير وتنظيف شامل ومكرر لقطع أي اتصالات قديمة معلقة ومنع خطأ 409
try:
    print("جاري سحق أي جلسات معلقة قديمة في تيليجرام...")
    bot.remove_webhook()
    # إيقاف مؤقت لمدة ثانيتين لمنح تيليجرام وقتاً لتحديث الحالة وإغلاق الاتصال القديم
    time.sleep(2) 
except Exception as e:
    print(f"تنبيه أثناء التنظيف: {e}")

# 3. دالة الترحيب المباشرة
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎯 أهلاً بك يا هندسة! البوت تم تطهيره من التداخل ويعمل الآن بكفاءة.\n\nأرسل لي صورة القائمة ليتم فرزها فوراً.")
    except Exception as e:
        print(f"خطأ ترحيب: {e}")

# 4. استقبال الصور ومعالجتها
@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        bot.reply_to(message, "⏳ جاري استلام الصورة وتحليل البيانات عبر Gemini، انتظر لحظات...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        
        client = genai.Client(api_key=GEMINI_KEY)
        prompt (
            "أنت مساعد محترف في قراءة الصور وتفريغ البيانات. "
            "قم باستخراج جميع المواد والأسعار الموجودة في هذه الصورة، "
            "ورتبها في جدول واضح ومنظم باللغة العربية مع تنظيم الترقيم والأسماء."
        )
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[image, prompt]
        )
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة:\n{str(e)}")

print("البوت انطلق على نظافة...")
# تشغيل مستمر مع تجاهل الرسائل المعلقة أثناء فترة التوقف والتعليق القديمة
bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout=40)
