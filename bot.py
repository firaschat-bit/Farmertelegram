import os
import sys
import subprocess

# تثبيت المكتبات تلقائياً داخل السيرفر
def install_packages():
    required_packages = ["pyTelegramBotAPI", "Pillow", "google-genai"]
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"جاري تثبيت المكتبة: {package} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

import telebot
from google import genai
from PIL import Image
import io
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# تشغيل منفذ اتصال وهمي لاستقرار سيرفر Render
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot is live and kicking!")
            
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise ValueError("خطأ: تأكد من ضبط BOT_TOKEN و GEMINI_API_KEY في إعدادات Render!")

client = genai.Client(api_key=GEMINI_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

try:
    bot.remove_webhook()
except:
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك يا هندسة! البوت مستقر وجاهز تماماً الآن. أرسل لي أي صورة لقائمة مواد أو أسعار لفرزها فوراً بذكاء Gemini.")

@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        bot.reply_to(message, "جاري معالجة الصورة وقراءة البيانات عبر Gemini، انتظر لحظة من فضلك...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image = Image.open(io.BytesIO(downloaded_file))
        
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
        bot.reply_to(message, f"عذراً هندسة، حدثت مشكلة أثناء المعالجة: {str(e)}")

print("البوت جاهز ويعمل...")
# التعديل الهام لحل مشكلة 409 Conflict وتطهير جلسات الاتصال القديمة
bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
