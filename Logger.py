from enum import Enum
from datetime import datetime


class LogType(Enum):
    info = 0
    error = 1
    buy = 2
    sell = 3


class Logger:
    def __init__(self):
        pass

    def create_log(self, type: LogType, message: str):
        res = ""
        if type == LogType.info:
            res += "[INFO] "
        if type == LogType.error:
            res += "[ERROR]"
        if type == LogType.buy:
            res += "[BUY]  "
        if type == LogType.sell:
            res += "[SELL] "
        res += " (" + str(datetime.now()) + ") " + message
        print(res)