import telegram
import logging
import tokens
from MAIN import helper
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

bot = telegram.Bot(token=tokens.TELEGRAM_BOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

TICKER, POINTS, STRATEGY_TEST = range(3)


def start(update, context):    
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def create_strategy(update: Update, context: CallbackContext):
    update.message.reply_text('If you want to create a strategy, enter the Ticket next')

    return TICKER


def process_ticker(update: Update, context: CallbackContext):
    result = helper.get_figi_from_ticker(update.message.text)
    update.message.reply_text(f'Got figi: {result}. If everything is OK, enter 3 point to set Canal')

    return POINTS


def process_points(update: Update, context: CallbackContext):
    print("YEEAH")
    
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Creation of Strategy is cancelled')

    return ConversationHandler.END


def main():
    updater = Updater(token=tokens.TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^(Create strategy)$'), create_strategy)],
        states={
            TICKER: [MessageHandler(Filters.text, process_ticker)],
            POINTS: [MessageHandler(Filters.text, process_points)]
            # STRATEGY_TEST: [
            #     MessageHandler(Filters.location, location),
            #     CommandHandler('skip', skip_location),
            # ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    

# dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
main()
# echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
# dispatcher.add_handler(start_handler)
# dispatcher.add_handler(echo_handler)
# updater.start_polling()

