import os
import telebot
import google.generativeai as genai
from PIL import Image
import io
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. تشغيل منفذ اتصال وهمي لاستقرار سيرفر Render
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot checking is live!")
            
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. سحب المتغيرات وطباعة فحص أمان في السجلات
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

print("--- فحص المتغيرات المستلمة من السيرفر ---")
if TELEGRAM_TOKEN:
    print(f"توكن تيليجرام موجود ويبدأ بـ: {TELEGRAM_TOKEN[:8]}")
else:
    print("خطأ: توكن تيليجرام غير موجود!")

if GEMINI_KEY:
    print(f"مفتاح جمناي موجود ويبدأ بـ: {GEMINI_KEY[:8]}")
else:
    print("خطأ: مفتاح جمناي غير موجود!")
print("---------------------------------------")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise ValueError("توقف السيرفر: تأكد من إضافة BOT_TOKEN و GEMINI_API_KEY في إعدادات Render!")

# إعداد مكتبة جمناي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تشغيل البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

try:
    bot.remove_webhook()
except:
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك يا هندسة! البوت مستقر وجاهز للعمل الآن. أرسل لي أي صورة لقائمة مواد أو أسعار، وسأقوم بفرزها فوراً بذكاء Gemini.")

@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        bot.reply_to(message, "جاري معالجة الصورة وقراءة البيانات، انتظر لحظة من فضلك...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image = Image.open(io.BytesIO(downloaded_file))
        
        prompt = (
            "أنت مساعد محترف في قراءة الصور وتفريغ البيانات. "
            "قم باستخراج جميع المواد والأسعار الموجودة في هذه الصورة، "
            "ورتبها في جدول واضح ومنظم باللغة العربية مع تنظيم الترقيم والأسماء."
        )
        
        response = model.generate_content([prompt, image])
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء معالجة الصورة: {str(e)}")

# استمرار التشغيل
bot.infinity_polling(skip_pending=True)
