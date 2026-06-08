import os
import sys
import subprocess

# 1. تثبيت المكتبات تلقائياً داخل سيرفر ريندر
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

# 2. تشغيل منفذ اتصال وهمي لضمان استقرار Render ومنع الانهيار
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Server is Active!")
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 3. سحب توكن تيليجرام ومفتاح جمناي
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# الحسم: حذف الويب هوك وتنظيف الجلسات المعلقة كلياً لمنع الصمت والتعليق
try:
    print("جاري تنظيف جلسات تيليجرام المعلقة...")
    bot.remove_webhook()
except Exception as e:
    print(f"تنبيه تنظيف: {e}")

# 4. أمر الترحيب (مباشر وسريع بدون أي شروط لكسر الصمت فوراً)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎯 أهلاً بك يا هندسة! البوت استيقظ واستجاب بنجاح الآن.\n\nأرسل لي أي صورة لقائمة مواد أو أسعار، وسأقوم بتمريرها لـ Gemini لفرزها لك.")
    except Exception as e:
        print(f"خطأ إرسال الترحيب: {e}")

# 5. استقبال الصورة ومعالجتها
@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        bot.reply_to(message, "⏳ جاري استلام الصورة وتحليل البيانات عبر Gemini، انتظر لحظات...")
        
        # تحميل الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        
        # الاتصال بجمناي بالعميل الحديث
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = (
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
        bot.reply_to(message, f"❌ حدثت مشكلة أثناء المعالجة:\n{str(e)}\n\n(إذا كان الخطأ 401، يرجى تجديد مفتاح GEMINI_API_KEY في إعدادات Render)")

print("البوت انطلق ويعمل بشكل مستقر...")
# تشغيل البوت بأعلى درجات الاستقرار ومنع التداخل
bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
