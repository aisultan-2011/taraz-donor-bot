import os
import telebot
from telebot import types

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Уақытша мәліметтер базасы (Жадыда сақталады)
donors_db = {}
user_states = {}

# Әкімшінің (Красный Полумесяц) Telegram ID-і (өз ID-іңді немесе сестренкаңдікін қой)
ADMIN_ID = 123456789  # Осы жерге өз Telegram ID-іңді жаз

BLOOD_GROUPS = ["I (+)", "I (-)", "II (+)", "II (-)", "III (+)", "III (-)", "IV (+)", "IV (-)"]
DISTRICTS = ["Центр", "Заводской", "12-15 мкр", "Баласағұн", "Алатау", "Басқа аудан"]

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_id in donors_db:
        markup.add("👤 Менің профилім", "ℹ️ Ақпарат")
        bot.send_message(
            user_id, 
            f"Сәлем, {donors_db[user_id]['name']}! Сіз жүйеде тіркелгенсіз.", 
            reply_markup=markup
        )
    else:
        markup.add("🩸 Донор болып тіркелу")
        bot.send_message(
            user_id, 
            "Сәлеметсіз бе! Тараз қаласының Қызыл Жарты Ай донорлық жүйесіне қош келдіңіз.\n\nШұғыл қан қажет болғанда хабарландыру алып тұру үшін тіркеліңіз.", 
            reply_markup=markup
        )

@bot.message_handler(func=lambda msg: msg.text == "🩸 Донор болып тіркелу")
def start_registration(message):
    user_id = message.chat.id
    user_states[user_id] = {'step': 'NAME'}
    bot.send_message(user_id, "Аты-жөніңізді енгізіңіз (мысалы: Нұрсултан):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'NAME')
def process_name(message):
    user_id = message.chat.id
    user_states[user_id]['name'] = message.text
    user_states[user_id]['step'] == 'BLOOD'
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*BLOOD_GROUPS)
    bot.send_message(user_id, "Қан тобыңыз бен резус-факторыңызды таңдаңыз:", reply_markup=markup)
    user_states[user_id]['step'] = 'BLOOD'

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'BLOOD')
def process_blood(message):
    user_id = message.chat.id
    if message.text not in BLOOD_GROUPS:
        bot.send_message(user_id, "Өтініш, батырмадан қан тобын таңдаңыз!")
        return
    
    user_states[user_id]['blood'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*DISTRICTS)
    bot.send_message(user_id, "Тараз қаласының қай ауданында тұрасыз?", reply_markup=markup)
    user_states[user_id]['step'] = 'DISTRICT'

@bot.message_handler(func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'DISTRICT')
def process_district(message):
    user_id = message.chat.id
    if message.text not in DISTRICTS:
        bot.send_message(user_id, "Өтініш, тізімнен ауданды таңдаңыз!")
        return
    
    user_states[user_id]['district'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_phone = types.KeyboardButton("📱 Контактіні жіберу", request_contact=True)
    markup.add(btn_phone)
    bot.send_message(user_id, "Экстрен байланыс үшін телефон нөміріңізді жіберіңіз:", reply_markup=markup)
    user_states[user_id]['step'] = 'PHONE'

@bot.message_handler(content_types=['contact'], func=lambda msg: msg.chat.id in user_states and user_states[msg.chat.id]['step'] == 'PHONE')
def process_phone(message):
    user_id = message.chat.id
    phone = message.contact.phone_number
    
    donors_db[user_id] = {
        'name': user_states[user_id]['name'],
        'blood': user_states[user_id]['blood'],
        'district': user_states[user_id]['district'],
        'phone': phone
    }
    
    del user_states[user_id]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Менің профилім", "ℹ️ Ақпарат")
    bot.send_message(user_id, "✅ Тіркелу сәтті аяқталды! Рақмет, сіз біреудің өмірін сақтап қалуыңыз мүмкін.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "👤 Менің профилім")
def show_profile(message):
    user_id = message.chat.id
    if user_id in donors_db:
        d = donors_db[user_id]
        text = f"📋 **Сіздің анкетаңыз:**\n\n👤 Аты: {d['name']}\n🩸 Қан тобы: {d['blood']}\n📍 Аудан: {d['district']}\n📞 Тел: {d['phone']}"
        bot.send_message(user_id, text, parse_mode="Markdown")

# Админ командасы: Қан керек кезде барлық донорларға хабарландыру жіберу
@bot.message_handler(commands=['alert'])
def alert_donors(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Бұл команда тек Қызыл Жарты Ай қызметкерлеріне арналған.")
        return
    
    msg = bot.send_message(message.chat.id, "Шұғыл хабарландыру мәтінін жазыңыз (мысалы: Тараз ауруханасына II (+) қан тобы шұғыл қажет!):")
    bot.register_next_step_handler(msg, broadcast_alert)

def broadcast_alert(message):
    alert_text = message.text
    count = 0
    for user_id in donors_db:
        try:
            bot.send_message(user_id, f"🚨 **ШҰҒЫЛ ШАҚЫРУ (Қызыл Жарты Ай):**\n\n{alert_text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ Хабарландыру {count} донорға жіберілді.")

if __name__ == '__main__':
    bot.infinity_polling()
