import os
import sys
import subprocess
import threading
import telebot
import io
from PIL import Image
import google.generativeai as genai

# 1. إعدادات البيئة
def install_packages():
    pkgs = ["pyTelegramBotAPI", "Pillow", "google-generativeai"]
    for p in pkgs:
        try: __import__(p.replace("-", "_"))
        except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

install_packages()

# 2. تهيئة البوت و Gemini بدون استخدام مسارات v1beta
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# التعديل الجوهري: نحدد الموديل بطريقة تتجنب مسارات الإصدارات التجريبية
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "أهلاً! أرسل لي صورة الفاتورة.")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري المعالجة...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        
        # استدعاء الموديل بشكل صريح
        response = model.generate_content(["قم باستخراج بيانات الفاتورة في جدول Markdown.", img])
        
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", m.chat.id, status.message_id)

# 3. تشغيل البوت (تم حذف السيرفر الوهمي إذا كان يسبب تعارضاً، يمكنك إضافته إذا لزم الأمر)
print("البوت يعمل الآن...")
bot.infinity_polling(skip_pending=True)
