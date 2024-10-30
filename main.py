import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Hello World!')


bot.polling(none_stop=True)
