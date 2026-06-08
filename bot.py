import os
import sys
import subprocess
import time

# 1. تثبيت المكتبات تلقائياً داخل Render
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

# 2. تشغيل سيرفر وهمي لضمان استقرار Render ومنع الانهيار
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

# سحب التوكن والمفتاح
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# تنظيف وتطهير الجلسات المعلقة كلياً لمنع تداخل 409
try:
    bot.remove_webhook()
    time.sleep(1)
except Exception as e:
    print(f"تنبيه تنظيف: {e}")

# 3. أمر الترحيب
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎯 أهلاً بك يا هندسة! البوت مستقر وجاهز تماماً الآن.\n\nأرسل لي أي صورة لقائمة مواد أو أسعار (مثل الفواتير)، وسأقوم بفرزها وتفريغها لك بالذكاء الاصطناعي.")
    except Exception as e:
        print(f"خطأ ترحيب: {e}")

# 4. استقبال الصورة ومعالجتها (تم تصحيح السطر وإضافة رسائل تتبع مدمجة)
@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        # إرسال رسالة فورية للمستخدم لتأكيد الاستلام كسر الصمت
        status_msg = bot.reply_to(message, "⏳ جاري استلام الفاتورة وتجهيزها لإرسالها إلى Gemini... انتظر لحظة.")
        
        # تحميل الصورة من سيرفرات تيليجرام
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        
        # تحديث نص الحالة
        bot.edit_message_text("🔄 الصورة جاهزة، جاري تحليل البيانات واستخراج الجدول عبر Gemini...", chat_id=message.chat.id, message_id=status_msg.message_id)
        
        # الاتصال بـ Gemini بالصيغة الصحيحة
        client = genai.Client(api_key=GEMINI_KEY)
        
        # الـ Prompt المعدل بدقة وجاهز للعمل
        prompt_text = (
            "أنت مساعد محترف في قراءة الفواتير وتفريغ البيانات. "
            "قم باستخراج جميع المواد، الكميات، الأسعار، والمبالغ الإجمالية الموجودة في هذه الصورة، "
            "ورتبها في جدول منظم وواضح باللغة العربية."
        )
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[image, prompt_text]
        )
        
        # مسح رسالة الانتظار وإرسال الجدول النهائي
        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدثت مشكلة أثناء المعالجة للأسف:\n{str(e)}")

print("Bot is fully running...")
bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout=40)
