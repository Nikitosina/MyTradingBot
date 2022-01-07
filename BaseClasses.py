from enum import Enum
from datetime import datetime
import tinvest as ti
from Logger import logger, LogType

class OperationType(Enum):
    SELL = 0
    BUY = 1


class Canal:
    # two points from bottom(top) and one from top(bottom)
    def __init__(self, name: str, p1: tuple = (0, 0), p2: tuple = (0, 0), p3: tuple = (0, 0), k: float = None, b1: float = None, b2: float = None):
        if k and b1 and b2:
            self.name = name
            self.k = k
            self.b1 = b1
            self.b2 = b2
            return

        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3

        self.name = name
        self.k = (y1 - y2) / (x1 - x2)
        self.b1 = y2 - self.k * x2
        self.b2 = y3 - self.k * x3
    
    def get_lower_bound(self, time: datetime = datetime.now()) -> float:
        y_low = self.k * time.timestamp() + self.b1
        return y_low
    
    def get_upper_bound(self, time: datetime = datetime.now()) -> float:
        y_high = self.k * time.timestamp() + self.b2
        return y_high

    def print_line_functions(self):
        print(f"y = {self.k}x + {self.b1}")
        print(f"y = {self.k}x + {self.b2}")
        # print(y_low, y_high)


class Operation:
    def __init__(self, type_: OperationType, price: float, currency: ti.Currency, lots: int):
        self.type_ = type_
        self.price = price
        self.currency = currency
        self.lots = lots
        self.date = datetime.now().timestamp()
        self.total_money = price * lots


class Deal:
    def __init__(self, 
        ticker: str, 
        figi: str, 
        buy_limit: float, 
        currency: ti.Currency = ti.Currency.usd, 
        profit: float = 0, 
        lots: int = 0, 
        operations: list = [],
        is_active: bool = True
        ):
        self.ticker = ticker
        self.figi = figi
        self.buy_limit = buy_limit
        self.available_money = buy_limit
        self.currency = currency
        self.profit = profit
        self.lots = lots
        self.operations = operations
        self.is_active = is_active

    def make_operation(self, operation: Operation) -> None:
        if operation.type_ == OperationType.BUY:
            self.available_money -= operation.total_money
            self.lots += operation.lots
        
        if operation.type_ == OperationType.SELL:
            self.available_money += operation.total_money
            self.lots -= operation.lots
            if self.available_money > self.buy_limit:
                self.profit += self.available_money - self.buy_limit
                self.available_money = self.buy_limit

        self.operations.append(operation)
    
    def total_percentage_profit(self) -> float:
        return '{0:.2f}'.format(float((((self.buy_limit + self.profit) / self.buy_limit) - 1) * 100))
    
    def generate_json(self) -> dict:
        res = {
            # "deal": {
                "ticker": self.ticker,
                "figi": self.figi,
                "currency": self.currency,
                "money_limit": self.buy_limit,
                "profit": self.profit,
                "available_money": self.available_money,
                "lots": self.lots,
                "is_active": self.is_active,
                "operations": []
            # }
        }

        for operation in self.operations:
            res["operations"].append({
                "type": "buy" if operation.type_ == OperationType.BUY else "sell",
                "price": operation.price,
                "lots": operation.lots
            })
        
        return res
    
    # def send_summary(self):
    #     telegram.MessageEntity()


class Strategy:
    # When to sell from top of canal
    TAKE_PROFIT_PERCENTAGE = 0.01
    # When to sell if price went down from bottom of canal
    STOP_LOSS_PERCENTAGE = 0.05
    # When to buy from bottom of canal
    BUY_THRESHOLD = 0.02

    def __init__(self, 
        ticker: str, 
        canal: Canal, 
        take_profit_percentage: float = 0.01,
        stop_loss_percentage: float = 0.05,
        buy_threshold: float = 0.02
        ):
        
        self.ticker = ticker
        self.canal = canal
        self.TAKE_PROFIT_PERCENTAGE = take_profit_percentage
        self.STOP_LOSS_PERCENTAGE = stop_loss_percentage
        self.BUY_THRESHOLD = buy_threshold
        
        self.setup()

        logger.create_log(LogType.info, 
            f'''Created Strategy for {self.ticker} with: 
                Buy range: {self.buy_range}
                Stop loss price: {self.stop_loss_price},
                Take profit price: {self.take_profit_price},
                Canal median: {self.canal_median}''')

        # print(self.buy_range)
        # print(self.stop_loss_price)
        # print(self.take_profit_price)
        # print(self.canal_median)

    def setup(self, date: datetime = datetime.now()):
        lower_bound = self.canal.get_lower_bound(date)
        upper_bound = self.canal.get_upper_bound(date)

        self.buy_range = (lower_bound * (1 - self.BUY_THRESHOLD), lower_bound * (1 + self.BUY_THRESHOLD))
        self.stop_loss_price = lower_bound * (1 - self.STOP_LOSS_PERCENTAGE)
        self.take_profit_price = upper_bound * (1 - self.TAKE_PROFIT_PERCENTAGE)
        self.canal_median = (lower_bound + upper_bound) / 2
    
    def generate_json(self):
        return {
            # "strategy": {
                "type": "canal",
                "take_profit_percentage": self.TAKE_PROFIT_PERCENTAGE,
                "buy_threshold": self.BUY_THRESHOLD,
                "stop_loss_percentage": self.STOP_LOSS_PERCENTAGE,
                "canal": {
                    "k": self.canal.k,
                    "b1": self.canal.b1,
                    "b2": self.canal.b2
                }
            # }
        }