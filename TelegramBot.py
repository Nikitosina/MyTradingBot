import telegram
import logging
import Logger
import tokens
from datetime import datetime
import tinvest as ti
import MAIN
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Strategy = MAIN.Strategy
# Deal = MAIN.Deal
# Canal = MAIN.Canal
# helper = MAIN.helper

bot = telegram.Bot(token=tokens.TELEGRAM_BOT_TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

TICKER, POINTS, DEAL, CHANGE_THRESHOLDS, BUY_THRESHOLD, STOP_LOSS_PERCANTAGE, TAKE_PROFIT_PERCENTAGE, STRATEGY_TEST, TEST_OR_SAVE, SAVE_AND_RUN = range(10)

current_ticker = ""
current_figi = ""
current_strategy: Strategy = None
current_deal: Deal = None

def start(update, context):    
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def end_conversation(update: Update, context: CallbackContext):
    global current_ticker, current_figi, current_strategy, current_deal
    update.message.reply_text("You cancelled the operation")
    current_ticker = ""
    current_figi = ""
    current_strategy = None
    current_deal = None

def create_strategy(update: Update, context: CallbackContext):
    global current_ticker, current_figi
    current_ticker = ""
    current_figi = ""
    update.message.reply_text('If you want to create a strategy, enter the Ticket next')

    return TICKER


def process_ticker(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END
    
    result = helper.get_figi_from_ticker(update.message.text)
    current_ticker = update.message.text
    current_figi = result
    update.message.reply_text(
        f'''Got figi: {result}. If everything is OK, enter 3 point to set Canal
            Expected input: <day>.<month>.<year> <price>
                           <day>.<month>.<year> <price>
                           <day>.<month>.<year> <price>'''
    )

    return POINTS


def process_points(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    global current_strategy
    data = update.message.text.split("\n")
    points = []

    for pointData in data:
        dateData, price = pointData.split()
        day, month, year = dateData.split(".")
        point = (datetime(int(year), int(month), int(day)).timestamp(), float(price))
        points.append(point)
    
    canal = Canal("Apple", points[0], points[1], points[2])
    current_strategy = helper.create_strategy(current_ticker, canal)
    
    update.message.reply_text(
        f'''Created Strategy with following parameters:
            Ticker: {current_strategy.ticker}
            Buy range: {current_strategy.buy_range}, (+- {current_strategy.BUY_THRESHOLD * 100} % of channel's bottom)
            Stop loss: {current_strategy.stop_loss_price}, (- {current_strategy.STOP_LOSS_PERCENTAGE * 100} % from channel's bottom)
            Teke profit: {current_strategy.take_profit_price}, (- {current_strategy.TAKE_PROFIT_PERCENTAGE * 100} % from channel's top)
            
            If everything is okay, enter OK to proceed to next steps.
            If not, you can modify thresholds by entering CHANGE
        '''
    )

    return CHANGE_THRESHOLDS

def process_is_changing_thresholds(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    text = update.message.text
    if text == "CHANGE":
        update.message.reply_text("Enter buy threshold (<= 1.00) or '-' to leave it unchanged")
        return BUY_THRESHOLD
    elif text == "OK":
        update.message.reply_text("All right. Let's now create a deal. Enter money limit for this strategy\nExpected input: <price> <currency: rub, usd, eur>")
        return DEAL
    else:
        update.message.reply_text("Did not understand you. Try again")
        return CHANGE_THRESHOLDS

def process_buy_threshold(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    if update.message.text == "-":
        update.message.reply_text("Enter stop loss percentage (<= 1.00) or '-' to leave it unchanged")
        return STOP_LOSS_PERCANTAGE

    new_threshold = float(update.message.text)
    if new_threshold <= 1:
        current_strategy.BUY_THRESHOLD = new_threshold
        current_strategy.setup()
        update.message.reply_text(f'''
            New buy range: {current_strategy.buy_range}
            Enter stop loss percentage (<= 1.00) or '-' to leave it unchanged
        ''')
        return STOP_LOSS_PERCANTAGE

def process_stop_loss(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    if update.message.text == "-":
        update.message.reply_text("Enter take profit percentage (<= 1.00) or '-' to leave it unchanged")
        return TAKE_PROFIT_PERCENTAGE

    new_percentage = float(update.message.text)
    if new_percentage <= 1:
        current_strategy.STOP_LOSS_PERCENTAGE = new_percentage
        current_strategy.setup()
        update.message.reply_text(f'''
            New stop loss price: {current_strategy.stop_loss_price}
            Enter take profit percentage (<= 1.00) or '-' to leave it unchanged
        ''')
        return TAKE_PROFIT_PERCENTAGE

def process_take_profit(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    if update.message.text == "-":
        update.message.reply_text(
            f'''The Strategy now looks like this:
            Ticker: {current_strategy.ticker}
            Buy range: {current_strategy.buy_range}, (+- {current_strategy.BUY_THRESHOLD * 100} % of channel's bottom)
            Stop loss: {current_strategy.stop_loss_price}, (- {current_strategy.STOP_LOSS_PERCENTAGE * 100} % from channel's bottom)
            Teke profit: {current_strategy.take_profit_price}, (- {current_strategy.TAKE_PROFIT_PERCENTAGE * 100} % from channel's bottom)
            
            If everything is okay, enter OK to proceed to next steps.
            If not, you can modify thresholds by entering CHANGE
        '''
        )
        return CHANGE_THRESHOLDS
    
    new_percentage = float(update.message.text)
    if new_percentage <= 1:
        current_strategy.TAKE_PROFIT_PERCENTAGE = new_percentage
        current_strategy.setup()
        update.message.reply_text(f'''
            The Strategy now looks like this:
            Ticker: {current_strategy.ticker}
            Buy range: {current_strategy.buy_range}, (+- {current_strategy.BUY_THRESHOLD * 100} % of channel's bottom)
            Stop loss: {current_strategy.stop_loss_price}, (- {current_strategy.STOP_LOSS_PERCENTAGE * 100} % from channel's bottom)
            Teke profit: {current_strategy.take_profit_price}, (- {current_strategy.TAKE_PROFIT_PERCENTAGE * 100} % from channel's bottom)
            
            If everything is okay, enter OK to proceed to next steps.
            If not, you can modify thresholds by entering CHANGE
        ''')
        return CHANGE_THRESHOLDS

def process_deal(update: Update, context: CallbackContext):
    if "cancel" in update.message.text.lower():
        end_conversation(update, context)
        return ConversationHandler.END

    data = update.message.text.split()
    limit_sum = float(data[0])
    
    currency: ti.Currency = None
    if data[1].lower() == "rub":
        currency = ti.Currency.rub
    if data[1].lower() == "usd":
        currency = ti.Currency.usd
    if data[1].lower() == "eur":
        currency = ti.Currency.eur
    
    current_deal = Deal(current_ticker, current_figi, limit_sum, currency)
    update.message.reply_text(f'''
        Deal was successfully created
        To test strategy enter TEST, to save and run strategy enter SAVE AND RUN
    ''')
    return ConversationHandler.END

def process_test_or_save(update: Update, context: CallbackContext):
    if update.message.text.strip() == "TEST":
        pass
    elif update.message.text.strip() == "SAVE AND RUN":
        update.message.reply_text("Saved")
        Logger.shared.save_deal(current_deal, current_strategy)
    else:
        update.message.reply_text("Try again")
        return TEST_OR_SAVE

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
            POINTS: [MessageHandler(Filters.text, process_points)],
            CHANGE_THRESHOLDS: [MessageHandler(Filters.text, process_is_changing_thresholds)],
            BUY_THRESHOLD: [MessageHandler(Filters.text, process_buy_threshold)],
            STOP_LOSS_PERCANTAGE: [MessageHandler(Filters.text, process_stop_loss)],
            TAKE_PROFIT_PERCENTAGE: [MessageHandler(Filters.text, process_take_profit)],
            DEAL: [MessageHandler(Filters.text, process_deal)],
            TEST_OR_SAVE: [MessageHandler(Filters.text, process_test_or_save)]
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

