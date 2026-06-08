import os
import sys
import subprocess
import threading
import telebot
import io
from PIL import Image
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler, HTTPServer

# تثبيت المكتبات
def install_packages():
    pkgs = ["pyTelegramBotAPI", "Pillow", "google-generativeai"]
    for p in pkgs:
        try: __import__(p.replace("-", "_"))
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

install_packages()

# تشغيل سيرفر وهمي للحفاظ على نشاط Render
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
model = genai.GenerativeModel('gemini-1.5-flash')

# !!! هذا السطر هو الحل الحاسم لمشكلة 409 !!!
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "أهلاً! أرسل لي صورة الفاتورة.")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري المعالجة...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        response = model.generate_content(["استخرج بيانات هذه الفاتورة في جدول Markdown.", img])
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", m.chat.id, status.message_id)

print("البوت يعمل الآن...")
bot.infinity_polling(skip_pending=True)
