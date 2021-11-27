from enum import Enum
from datetime import datetime
# from MAIN import Strategy, Deal, OperationType
# from TelegramBot import bot as telegram_bot
import MAIN
import tokens
import json


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
    
    def save_deal(self, deal: Deal, strategy: Strategy):
        new_data = {
            "deal": {
                "figi": deal.figi,
                "currency": deal.currency,
                "money_limit": deal.buy_limit,
                "available_money": deal.available_money,
                "lots": deal.lots,
                "operations": []
            },
            "strategy": {
                "type": "canal",
                "take_profit_percentage": strategy.TAKE_PROFIT_PERCENTAGE,
                "buy_threshold": strategy.BUY_THRESHOLD,
                "stop_loss_percentage": strategy.STOP_LOSS_PERCENTAGE,
                "canal": {
                    "k": strategy.canal.k,
                    "b1": strategy.canal.b1,
                    "b2": strategy.canal.b2
                }
            }
        }

        for operation in deal.operations:
            new_data["deal"]["operations"].append({
                "type": "buy" if operation.type_ == OperationType.BUY else "sell",
                "price": operation.price,
                "lots": operation.lots
            })

        with open("deals.json", "r+") as f:
            file_data = json.load(f)

            if deal.ticker in file_data:
                file_data[deal.ticker].append(new_data)
            else:
                file_data[deal.ticker] = new_data
            
            f.seek(0)
            json.dump(file_data, f, indent = 4)
