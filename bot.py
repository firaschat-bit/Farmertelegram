import os
import sys
import subprocess
import telebot
from PIL import Image
import io
from flask import Flask, request
from google import genai # استخدام المكتبة الجديدة والمدعومة

# 1. تثبيت المكتبات الصحيحة
def install_requirements():
    required = ["pyTelegramBotAPI", "Pillow", "google-genai", "flask"]
    for package in required:
        try: __import__(package.replace("-", "_"))
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

# 2. إعدادات البوت والعميل الجديد
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
app = Flask(__name__)

@app.route('/' + os.getenv('BOT_TOKEN'), methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "البوت يعمل الآن بأحدث مكتبة من Google. أرسل صورة الفاتورة.")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري التحليل...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        
        # استخدام المكتبة الجديدة
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=["قم باستخراج بيانات الفاتورة في جدول Markdown منظم.", img]
        )
        
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ تقني:\n{str(e)}", m.chat.id, status.message_id)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv('RENDER_EXTERNAL_URL') + '/' + os.getenv('BOT_TOKEN'))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
