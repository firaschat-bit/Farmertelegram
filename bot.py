import os
import sys
import subprocess
import time

# 1. تثبيت المكتبات تلقائياً لضمان بيئة عمل نظيفة داخل Render
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

# 2. سيرفر وهمي للحفاظ على استقرار الخدمة في Render ومنع الانهيار الإجباري
def run_dummy_server():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Engine Live and Stable!")
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# جلب متغيرات البيئة
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# تنظيف الجلسات السابقة لضمان عدم حدوث تداخل 409 مجدداً
try:
    bot.remove_webhook()
    time.sleep(1)
except Exception as e:
    print(f"تنبيه تنظيف الويب هوك: {e}")

# 3. معالج رسائل الترحيب
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎯 أهلاً بك يا هندسة! البوت مستقر وجاهز تماماً الآن.\n\nأرسل لي صورة القائمة أو الفاتورة مباشرة، وسأقوم بفرزها وتفريغها لك في جدول منظم.")
    except Exception as e:
        print(f"خطأ ترحيب: {e}")

# 4. المعالج المطور والمستقر لاستقبال الصور تفادياً للصمت الإجباري
@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    status_msg = None
    try:
        # إرسال رسالة فورية لكسر الصمت وتأكيد الاستلام
        status_msg = bot.reply_to(message, "⏳ جاري استلام الفاتورة وتجهيزها... انتظر لحظة.")
        
        # جلب تفاصيل الصورة وتحميلها بأمان
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح الصورة باستخدام Pillow
        image = Image.open(io.BytesIO(downloaded_file))
        
        # تحديث نص الحالة للمستخدم لإعلامه بالانتقال لـ Gemini
        bot.edit_message_text(
            text="🔄 جاري الآن فرز البيانات وتحليل الجدول عبر طاقة Gemini الاصطناعية...",
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )
        
        # إعداد عميل Gemini الحديث
        client = genai.Client(api_key=GEMINI_KEY)
        
        prompt_text = (
            "أنت مساعد محترف وخبير في تحليل وقراءة الفواتير وتفريغ البيانات. "
            "قم بقراءة الصورة بدقة واستخراج جميع المواد، الكميات، الأسعار، والمبالغ الإجمالية الواردة فيها. "
            "رتب البيانات المستخرجة في جدول ماركداون (Markdown Table) واضح ومنظم باللغة العربية."
        )
        
        # إرسال الطلب للنموذج
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[image, prompt_text]
        )
        
        # مسح رسالة الانتظار المؤقتة وإرسال النتيجة النهائية
        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        bot.reply_to(message, response.text, parse_mode="Markdown")
        
    except Exception as e:
        error_text = f"❌ حدثت مشكلة أثناء المعالجة:\n{str(e)}"
        if status_msg:
            try:
                bot.edit_message_text(text=error_text, chat_id=message.chat.id, message_id=status_msg.message_id)
            except:
                bot.reply_to(message, error_text)
        else:
            bot.reply_to(message, error_text)

print("البوت انطلق بكفاءة تشغيلية كاملة...")
# تشغيل الاقتراع اللانهائي بإعدادات متينة ضد انقطاع الشبكة
bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout=40)
