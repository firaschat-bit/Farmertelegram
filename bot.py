import os
import sys
import subprocess
import time
import telebot
import io
from PIL import Image
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import google.generativeai as genai # المكتبة الرسمية المستقرة

# 1. تثبيت المكتبات الضرورية
def install_packages():
    pkgs = ["pyTelegramBotAPI", "Pillow", "google-generativeai"]
    for p in pkgs:
        try: __import__(p.replace("-", "_"))
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

install_packages()

# 2. إعدادات السيرفر الوهمي لـ Render
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Live!")
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), Handler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 3. تهيئة البوت و Gemini
BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # الموديل الأكثر استقراراً

# 4. المعالج الأساسي
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "أهلاً بك! أرسل لي صورة الفاتورة وسأقوم بتفريغها في جدول.")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري المعالجة...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        
        prompt = "قم باستخراج البيانات من هذه الفاتورة ووضعها في جدول Markdown باللغة العربية."
        response = model.generate_content([prompt, img])
        
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {e}", m.chat.id, status.message_id)

bot.infinity_polling(skip_pending=True)
