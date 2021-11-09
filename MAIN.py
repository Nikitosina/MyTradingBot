from enum import Enum
from pprint import pprint
from datetime import datetime
import telegram
import tinvest as ti
from tinvest.schemas import CandlesResponse
import tokens
from Balance import Balance
from Logger import Logger, LogType
from TelegramBot import bot as telegram_bot


Logger.shared = Logger()


class OperationType(Enum):
    SELL = 0
    BUY = 1


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


class Operation:
    def __init__(self, type_: OperationType, price: float, currency: ti.Currency, lots: int):
        self.type_ = type_
        self.price = price
        self.currency = currency
        self.lots = lots
        self.total_money = price * lots


class Deal:
    def __init__(self, 
        ticker: str, 
        figi: str, 
        buy_limit: float, 
        currency: ti.Currency = ti.Currency.usd, 
        profit: float = 0, 
        lots: int = 0, 
        operations: list = []
        ):
        self.ticker = ticker
        self.figi = figi
        self.buy_limit = buy_limit
        self.available_money = buy_limit
        self.currency = currency
        self.profit = profit
        self.lots = lots
        self.operations = operations

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


class Strategy:
    # When to sell from top of canal
    TAKE_PROFIT_PERCENTAGE = 0.01
    # When to sell if price went down from bottom of canal
    STOP_LOSS_PERCENTAGE = 0.05
    # When to buy from bottom of canal
    BUY_THRESHOLD = 0.02

    def __init__(self, 
        ticker: str, 
        figi: str, 
        canal: Canal, 
        take_profit_percentage: float = 0.01,
        stop_loss_percentage: float = 0.05,
        buy_threshold: float = 0.02
        ):
        
        self.ticker = ticker
        self.figi = figi
        self.canal = canal
        self.TAKE_PROFIT_PERCENTAGE = take_profit_percentage
        self.STOP_LOSS_PERCENTAGE = stop_loss_percentage
        self.BUY_THRESHOLD = buy_threshold
        
        self.setup()

        Logger.shared.create_log(LogType.info, 
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
        self.deals = []
        
        apple_figi = self.get_figi_from_ticker("AAPL")
        point1 = self.generate_point(apple_figi, datetime(2020, 9, 14), datetime(2020, 9, 21), ti.CandleResolution.week)
        point2 = self.generate_point(apple_figi, datetime(2021, 3, 8), datetime(2021, 3, 15), ti.CandleResolution.week)
        point3 = self.generate_point(apple_figi, datetime(2021, 1, 18), datetime(2021, 1, 25), ti.CandleResolution.week, "h")
        canal = Canal("Apple", point1, point2, point3)
        self.strategies.append(Strategy("AAPL", apple_figi, canal))
        self.deals.append(Deal("AAPL", apple_figi, 1000.0))

        FSK_bond_ticker = "RU000A0ZYDH0"
        FSK_bond_figi = self.get_figi_from_ticker(FSK_bond_ticker)
        point1 = (datetime(2021, 11, 1).timestamp(), 989.5)
        point2 = (datetime(2021, 9, 27).timestamp(), 993.2)
        point3 = (datetime(2021, 9, 27).timestamp(), 1024.4)
        canal = Canal(FSK_bond_ticker, point1, point2, point3)
        self.strategies.append(Strategy(FSK_bond_ticker, FSK_bond_figi, canal, 0.005, 0.03, 0.005))
        self.deals.append(Deal(FSK_bond_ticker, FSK_bond_figi, 10000.0, ti.Currency.rub))

        # self.test_strategy(self.strategies[0], self.deals[0], datetime(2020, 9, 21), datetime.now())
        self.test_strategy(self.strategies[1], self.deals[1], datetime(2021, 3, 22), datetime.now())
    
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
    
    def test_strategy(self,
        strategy: Strategy,
        deal: Deal,
        from_: datetime, 
        to: datetime, 
        interval: ti.CandleResolution = ti.CandleResolution.week):

        buy_price, sell_price = 0, 0
        response = self.client.get_market_candles(strategy.figi, from_, to, interval)
        candles = response.payload.candles
        self.logger.create_log(LogType.info, f"Starting strategy test for {strategy.ticker}")
        self.logger.create_log(LogType.info, f"Got {len(candles)} candles for strategy test")

        for candle in candles:
            strategy.setup(candle.time)
            low_price = float(candle.l)
            mid_price = (float(candle.o) + float(candle.c)) / 2
            high_price = float(candle.h)
            
            # BUY
            if strategy.buy_range[0] < low_price < strategy.buy_range[1] and deal.available_money - low_price > 0:
                available_lots = int(deal.available_money / low_price)
                body = ti.SandboxSetPositionBalanceRequest(
                    balance=available_lots,
                    figi=strategy.figi,
                )
                response = self.client.set_sandbox_positions_balance(body, tokens.SANDBOX_ACCOUNT_ID)

                deal.make_operation(Operation(OperationType.BUY, low_price, ti.Currency.usd, available_lots))
                buy_price = low_price
                # self.logger.create_log(LogType.info, f"Status: {response.status}")
                self.logger.create_log(LogType.buy, f'''Buy range achieved: 
                    {strategy.ticker} {available_lots} lots for price {low_price} {deal.currency}
                    Date: {candle.time}''')
                self.logger.create_log(LogType.info, f"Balance: {deal.available_money} {deal.currency}")
            
            # SELL
            if high_price >= strategy.take_profit_price and deal.lots > 0:
                body = ti.SandboxSetPositionBalanceRequest(
                    balance=0,
                    figi=strategy.figi,
                )
                response = self.client.set_sandbox_positions_balance(body, tokens.SANDBOX_ACCOUNT_ID)

                deal.make_operation(Operation(OperationType.SELL, high_price, ti.Currency.usd, available_lots))
                sell_price = high_price
                # self.logger.create_log(LogType.info, f"Status: {response.status}")
                self.logger.create_log(LogType.sell, f'''Take profit achieved: 
                    {strategy.ticker} {available_lots} lots for price {high_price} {deal.currency}
                    Profit: +{'{0:.2f}'.format(float(((sell_price / buy_price) - 1) * 100))} %
                    Date: {candle.time}''')
                self.logger.create_log(LogType.info, f"Balance: {deal.available_money} {deal.currency}")
        
        self.logger.create_log(LogType.info, f"Overall profit: {deal.profit} {deal.currency} (+{deal.total_percentage_profit()} %)")
        telegram_bot.send_message(f"Overall profit: {deal.profit} {deal.currency} (+{deal.total_percentage_profit()} %)")

        # for operation in deal.operations:
        #     print(operation.type_, operation.price, operation.total_money)
        
        

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
