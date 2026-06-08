import os
import telebot
import io
from PIL import Image
import google.generativeai as genai
from flask import Flask, request

# تهيئة البوت و Gemini
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# إعداد خادم Flask للتعامل مع الـ Webhook
app = Flask(__name__)

@app.route('/' + os.getenv('BOT_TOKEN'), methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "البوت يعمل بنظام Webhook الآن!")

@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    status = bot.reply_to(m, "⏳ جاري المعالجة...")
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        response = model.generate_content(["استخرج البيانات في جدول Markdown.", img])
        bot.delete_message(m.chat.id, status.message_id)
        bot.reply_to(m, response.text, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", m.chat.id, status.message_id)

# إعداد الـ Webhook
bot.remove_webhook()
bot.set_webhook(url=os.getenv('RENDER_EXTERNAL_URL') + '/' + os.getenv('BOT_TOKEN'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
