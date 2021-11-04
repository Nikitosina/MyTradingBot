from enum import Enum
from pprint import pprint
from datetime import datetime
import tinvest as ti
from tinvest.schemas import CandlesResponse
import tokens
from Balance import Balance


class Operation(Enum):
    SELL = 0
    BUY = 1


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


class Canal:
    # two points from bottom(top) and one from top(bottom)
    def __init__(self, name: str, p1: tuple, p2: tuple, p3: tuple):
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


class Strategy:
    # When to sell from top of canal
    TAKE_PROFIT_PERCENTAGE = 0.01
    # When to sell if price went down from bottom of canal
    STOP_LOSS_PERCENTAGE = 0.05
    # When to buy from bottom of canal
    BUY_THRESHOLD = 0.02

    def __init__(self, ticker: str, figi: str, canal: Canal):
        self.ticker = ticker
        self.figi = figi
        self.canal = canal

        lower_bound = canal.get_lower_bound()
        upper_bound = canal.get_upper_bound()

        self.buy_range = (lower_bound * (1 - self.BUY_THRESHOLD), lower_bound * (1 + self.BUY_THRESHOLD))
        self.stop_loss_price = lower_bound * (1 - self.STOP_LOSS_PERCENTAGE)
        self.take_profit_price = upper_bound * (1 - self.TAKE_PROFIT_PERCENTAGE)
        self.canal_median = (lower_bound + upper_bound) / 2

        # print(self.buy_range)
        # print(self.stop_loss_price)
        # print(self.take_profit_price)
        # print(self.canal_median)


class Helper: 
    def __init__(self):
        self.logger = Logger()
        self.client = ti.SyncClient(tokens.SANDBOX_TOKEN, use_sandbox=True)
        # self.next_operation = Operation.BUY
        self.setup_sandbox()
        
        self.logger.create_log(LogType.info, "Sandbox was created")
        
        self.balance = Balance(self.client, tokens.SANDBOX_ACCOUNT_ID)
        self.balance.update()

        self.strategies = []
        
        apple_figi = self.get_figi_from_ticker("AAPL")
        point1 = self.generate_point(apple_figi, datetime(2020, 9, 14), datetime(2020, 9, 21), ti.CandleResolution.week)
        point2 = self.generate_point(apple_figi, datetime(2021, 3, 8), datetime(2021, 3, 15), ti.CandleResolution.week)
        point3 = self.generate_point(apple_figi, datetime(2021, 1, 18), datetime(2021, 1, 25), ti.CandleResolution.week, "h")
        canal = Canal("Apple", point1, point2, point3)
        self.strategy = Strategy("AAPL", apple_figi, canal)
        self.logger.create_log(LogType.info, 
            f'''Created Strategy for {self.strategy.ticker} with: 
                Buy range: {self.strategy.buy_range}
                Stop loss price: {self.strategy.stop_loss_price},
                Take profit price: {self.strategy.take_profit_price},
                Canal median: {self.strategy.canal_median}''')
    
    def setup_sandbox(self):
        body = ti.SandboxRegisterRequest.tinkoff_iis()
        self.client.register_sandbox_account(body)
        body = ti.SandboxSetCurrencyBalanceRequest(
            balance=100000,
            currency='RUB',
        )
        self.client.set_sandbox_currencies_balance(body, tokens.SANDBOX_ACCOUNT_ID)
    
    # target is one of: o, c, h, l
    def generate_point(self, figi: str, from_: datetime, to: datetime, interval: ti.CandleResolution, target: str = "l"):
        response = self.client.get_market_candles(figi, from_, to, interval)
        candle = response.payload.candles[0]
        if target == "l":
            point = (from_.timestamp(), float(candle.l))
        if target == "h":
            point = (from_.timestamp(), float(candle.h))
        return point

    def get_balance(self):
        response = self.client.get_portfolio("2026763157")
    
    def get_figi_from_ticker(self, ticker):
        response = self.client.get_market_search_by_ticker(ticker)
        return response.payload.instruments[0].figi


# print(tokens.TRADE_TOKEN, tokens.SANDBOX_TOKEN)
# client = ti.SyncClient(tokens.TRADE_TOKEN)

# response = client.get_market_search_by_ticker("AAPL")
# print(response.payload.instruments[0].name)

helper = Helper()
# helper.get_balance()
