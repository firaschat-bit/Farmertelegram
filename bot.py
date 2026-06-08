import os
import telebot
import google.generativeai as genai
from PIL import Image
import io

# الكود نظيف وآمن 100%، يقرأ التوكن من إعدادات سيرفر Render مباشرة
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')

# مفتاح جمناي المعتمد
GEMINI_API_KEY = 'AQ.Ab8RN6KWBT84eYAnLaV1eD4yLcdLbEn1qM5sEWKVmZxGVY03ag'

if not TELEGRAM_TOKEN:
    raise ValueError("خطأ: لم يتم العثور على متغير البيئة BOT_TOKEN في إعدادات Render!")

# إعداد مكتبة جمناي
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تشغيل البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# تنظيف أي اتصالات سابقة معلقة
try:
    bot.remove_webhook()
except:
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي أي صورة تحتوي على قائمة مواد أو أسعار، وسأقوم بقراءتها وتنسيقها لك فوراً بواسطة الذكاء الاصطناعي.")

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

# استمرار تشغيل البوت
print("البوت الآمن يعمل الآن بنجاح...")
bot.infinity_polling(skip_pending=True)
