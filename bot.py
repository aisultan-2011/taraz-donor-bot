import os
import telebot

# Токенді Render жүйесінен аламыз
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Сәлем! Бұл Тараз қаласының Қызыл Жарты Ай (Красный Полумесяц) донорлық ботының тесттік нұсқасы 🚀\n\nСервер 24/7 белсенді жұмыс істеп тұр!"
    )

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Сіз жаздыңыз: {message.text}")

if __name__ == '__main__':
    print("Бот іске қосылды...")
    bot.infinity_polling()
