import telebot
import google.generativeai as genai
from PIL import Image
import io

# الرموز السرية الخاصة بك والمحمية تماماً
TELEGRAM_TOKEN = '8987486276:AAFc6yFa5JjD_4jaVsbkneGRUsXhspm03S4'
GEMINI_API_KEY = 'AQ.Ab8RN6KWBT84eYAnLaV1eD4yLcdLbEn1qM5sEWKVmZxGVY03ag'

# إعداد مكتبة جمناي
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# تشغيل البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك أستاذ فراس! أرسل لي أي صورة تحتوي على قائمة مواد، أسعار، أو جداول إنشائية، وسأقوم بقراءتها وتنسيقها لك فوراً بواسطة الذكاء الاصطناعي.")

@bot.message_handler(content_types=['photo'])
def handle_menu_photo(message):
    try:
        bot.reply_to(message, "جاري معالجة الصورة وقراءة البيانات، انتظر لحظة من فضلك...")
        
        # تحميل الصورة من سيرفرات تيليجرام
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # تحويل الملف إلى صورة يمكن لـ Gemini قراءتها
        image = Image.open(io.BytesIO(downloaded_file))
        
        # التوجيهات الموجهة للذكاء الاصطناعي لفرز القائمة بدقة هندسية
        prompt = (
            "أنت مساعد محترف وخبير في قراءة الصور وتفريغ الجداول والبيانات. "
            "قم باستخراج جميع المواد والأسعار أو البيانات الموجودة في هذه الصورة بدقة عالية، "
            "ورتبها في جدول واضح ومنظم جداً باللغة العربية مع تنظيم الترقيم والأسماء والرموز."
        )
        
        # إرسال الصورة لـ Gemini لطلب التحليل
        response = model.generate_content([prompt, image])
        
        # إرسال النتيجة النهائية للمستخدم
        bot.reply_to(message, response.text)
        
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء معالجة الصورة: {str(e)}")

# استمرار تشغيل البوت دون توقف
print("البوت يعمل الآن بنجاح...")
bot.infinity_polling()
