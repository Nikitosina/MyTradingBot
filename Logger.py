from enum import Enum
from datetime import datetime
# from TelegramBot import bot as telegram_bot
import tokens


class LogType(Enum):
    info = 0
    error = 1
    buy = 2
    sell = 3


class Logger:
    def __init__(self):
        self.file = open("activity.log", "w", encoding="utf8")
        self.file.write("\n ========== NEW LOG ========== \n")

    def create_log(self, type: LogType, message: str, send_to_telegram: bool = False):
        res = ""

        if type == LogType.info:
            res += "[INFO] "
        if type == LogType.error:
            res += "[ERROR]"
        if type == LogType.buy:
            res += "[BUY]  "
        if type == LogType.sell:
            res += "[SELL] "

        res += " (" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ") " + message    
        print(res)
        self.file.write(res)

        # if send_to_telegram:
        #     telegram_bot.send_message(tokens.TELEGRAM_CHAT_ID, res)
