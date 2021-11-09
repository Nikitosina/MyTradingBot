import telegram
import logging
import tokens
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

updater = Updater(token=tokens.TELEGRAM_BOT_TOKEN, use_context=True)
bot = telegram.Bot(token=tokens.TELEGRAM_BOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)


def start(update, context):    
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# def store_chat(id: str):
    


dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)
updater.start_polling()

