import os
import threading
from flask import Flask
import telebot
from telebot import types

# 1. Render үшін кішкентай веб-сервер (портты жаппас үшін)
app = Flask(__name__)

@app.route('/')
def home():
    return "Taraz Donor Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# 2. Telegram Бот бөлімі
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Әкімшілердің Telegram ID-лері (Өзің мен әпкеңдікін сандармен жаз)
ADMIN_IDS = [7154594023]  # Осы жерге өз ID-леріңді үтір арқылы жазыңдар

BLOOD_GROUPS = ["I (+)", "I (-)", "II (+)", "II (-)", "III (+)", "III (-)", "IV (+)", "IV (-)"]
DISTRICTS = ["Центр", "Заводской", "12-15 мкр", "Баласағұн", "Алатау", "Басқа аудан"]

donors_db = {}
user_states = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_id in donors_db:
        markup.add("👤 Менің профилім", "ℹ️ Ақпарат")
        bot.send_message(user_id, f"Сәлем, {donors_db[user_id]['name']}! Сіз жүйеде тіркелгенсіз.", reply_markup=markup)
    else:
        markup.add("🩸 Донор болып тіркелу")
        bot.send_message(user_id, "Сәлеметсіз бе! Тараз қаласының Қызыл Жарты Ай донорлық ботына қош келдіңіз.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "🩸 Донор болып тіркелу")
def start_registration(message):
    user_id = message.chat.id
    user_states[user_id] = {'step': 'NAME'}
    bot.send_message(user_id, "Аты-жөніңізді енгізіңіз (мысалы: Нұрсултан):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'NAME')
def process_name(message):
    user_id = message.chat.id
    user_states[user_id]['name'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*BLOOD_GROUPS)
    bot.send_message(user_id, "Қан тобыңызды таңдаңыз:", reply_markup=markup)
    user_states[user_id]['step'] = 'BLOOD'

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'BLOOD')
def process_blood(message):
    user_id = message.chat.id
    user_states[user_id]['blood'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*DISTRICTS)
    bot.send_message(user_id, "Тараздың қай ауданында тұрасыз?", reply_markup=markup)
    user_states[user_id]['step'] = 'DISTRICT'

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'DISTRICT')
def process_district(message):
    user_id = message.chat.id
    user_states[user_id]['district'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_phone = types.KeyboardButton("📱 Контактіні жіберу", request_contact=True)
    markup.add(btn_phone)
    bot.send_message(user_id, "Байланыс телефоныңызды жіберіңіз:", reply_markup=markup)
    user_states[user_id]['step'] = 'PHONE'

@bot.message_handler(content_types=['contact'], func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'PHONE')
def process_phone(message):
    user_id = message.chat.id
    donors_db[user_id] = {
        'name': user_states[user_id]['name'],
        'blood': user_states[user_id]['blood'],
        'district': user_states[user_id]['district'],
        'phone': message.contact.phone_number
    }
    del user_states[user_id]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Менің профилім")
    bot.send_message(user_id, "✅ Тіркелу сәтті аяқталды!", reply_markup=markup)

@bot.message_handler(commands=['alert'])
def alert_donors(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "Бұл команда тек әкімшілерге арналған.")
        return
    msg = bot.send_message(message.chat.id, "Шұғыл хабарлама мәтінін жазыңыз:")
    bot.register_next_step_handler(msg, broadcast_alert)

def broadcast_alert(message):
    count = 0
    for uid in donors_db:
        try:
            bot.send_message(uid, f"🚨 **ШҰҒЫЛ ХАБАРЛАМА:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ {count} донорға жіберілді.")

# Серверді бөлек потокта іске қосу
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    print("Бот іске қосылды...")
    bot.infinity_polling()
