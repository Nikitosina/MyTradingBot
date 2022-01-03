from enum import Enum
from datetime import datetime
from pprint import pprint
from tinvest import OperationTrade
# from TelegramBot import bot as telegram_bot
import tokens
import json

# Strategy = MAIN.Strategy
# Deal = MAIN.Deal
# Canal = MAIN.Canal
# OperationType = MAIN.OperationType

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
        self.file.write(res + "\n")

        # if send_to_telegram:
        #     telegram_bot.send_message(tokens.TELEGRAM_CHAT_ID, res)
    
    def save_deal(self, deal: dict, strategy: dict):
        new_data = {
            "deal": deal,
            "strategy": strategy
        }

        with open("deals.json", "r+") as f:
            read = f.read()
            # print(read)
            if read == "":
                file_data = {}
            else:
                file_data = json.loads(read)
            # print(file_data)

            if deal["ticker"] in file_data:
                file_data[deal["ticker"]].update(new_data)
            else:
                file_data[deal["ticker"]] = new_data
            
            pprint(file_data)
            f.seek(0)
            json.dump(file_data, f, indent = 4)
            f.truncate()


logger = Logger()
