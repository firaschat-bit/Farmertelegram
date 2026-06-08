import os
import sys
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
import io
from PIL import Image
import google.generativeai as genai

# تثبيت المكتبات (لضمان عمل بيئة Render)
def install_packages():
    pkgs = ["pyTelegramBotAPI", "Pillow", "google-generativeai"]
    for p in pkgs:
        try: __import__(p.replace("-", "_"))
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

install_packages()

# سيرفر للحفاظ على استقرار Render
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Stable!")
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), Handler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# تهيئة البوت و Gemini
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# التعديل الحاسم: تعريف الموديل بدون مسار v1beta
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز! أرسل لي صورة الفاتورة.")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري المعالجة...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        
        # استخراج البيانات
        response = model.generate_content(["قم باستخراج بيانات هذه الفاتورة في جدول Markdown منظم.", img])
        
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ تقني:\n{str(e)}", m.chat.id, status.message_id)

bot.infinity_polling(skip_pending=True)
