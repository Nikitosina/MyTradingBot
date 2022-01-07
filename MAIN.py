import tinvest as ti
import tokens
import json
import asyncio
import TelegramBot
from pprint import pprint
from datetime import datetime
from tinvest.schemas import CandlesResponse
from Balance import Balance
from BaseClasses import Canal, Strategy, Deal, Operation, OperationType
from Logger import logger, LogType
# from Logger import Logger
# import Logger
# import TelegramBot


class Trader: 
    def __init__(self):
        self.client = ti.SyncClient(tokens.TRADE_TOKEN)
        
        self.balance = Balance(self.client, tokens.MAIN_ACCOUNT_ID)
        self.balance.update()

        self.strategies = []
        self.deals = []
        self.inactive_deals = []
        
        # apple_figi = self.get_figi_from_ticker("AAPL")
        # point1 = self.generate_point(apple_figi, datetime(2020, 9, 14), datetime(2020, 9, 21), ti.CandleResolution.week)
        # point2 = self.generate_point(apple_figi, datetime(2021, 3, 8), datetime(2021, 3, 15), ti.CandleResolution.week)
        # point3 = self.generate_point(apple_figi, datetime(2021, 1, 18), datetime(2021, 1, 25), ti.CandleResolution.week, "h")
        # canal = Canal("Apple", point1, point2, point3)
        # self.strategies.append(Strategy("AAPL", canal))
        # self.deals.append(Deal("AAPL", apple_figi, 1000.0))

        # FSK_bond_ticker = "RU000A0ZYDH0"
        # FSK_bond_figi = self.get_figi_from_ticker(FSK_bond_ticker)
        # point1 = (datetime(2021, 11, 15).timestamp(), 983.5)
        # point2 = (datetime(2021, 9, 27).timestamp(), 993.2)
        # point3 = (datetime(2021, 9, 27).timestamp(), 1024.4)
        # canal = Canal(FSK_bond_ticker, point1, point2, point3)
        # self.strategies.append(Strategy(FSK_bond_ticker, canal, 0.005, 0.03, 0.005))
        # self.deals.append(Deal(FSK_bond_ticker, FSK_bond_figi, 10000.0, ti.Currency.rub))

        # self.test_strategy(self.strategies[0], self.deals[0], datetime(2020, 9, 21), datetime.now())
        # self.test_strategy(self.strategies[1], self.deals[1], datetime(2021, 3, 22), datetime.now())

        self.load_deals()
    
    def load_deals(self):
        with open("deals.json", "r") as f:
            data = json.loads(f.read())
            for key, value in data.items():
                deal_data = value["deal"]
                currency = str_to_currency(deal_data["currency"])
                if not currency:
                    raise ValueError("no currency found in json")

                deal = Deal(deal_data["ticker"], deal_data["figi"], deal_data["money_limit"], currency, deal_data["profit"], deal_data["lots"], deal_data["lots"], deal_data["is_active"])
                if not deal.is_active:
                    self.inactive_deals.append(deal)
                else:
                    self.deals.append(deal)
                
                strategy_data = value["strategy"]
                if strategy_data["type"] == "canal":
                    canal_data = strategy_data["canal"]
                    canal = Canal(key, k=canal_data["k"], b1=canal_data["b1"], b2=canal_data["b2"])
                    strategy = Strategy(key, canal, strategy_data["take_profit_percentage"], strategy_data["stop_loss_percentage"], strategy_data["buy_threshold"])
                    self.strategies.append(strategy)

        
        # print(self.deals, self.strategies, self.balance.get_current())
    
    async def main(self):
        async with ti.Streaming(tokens.TRADE_TOKEN) as streaming:
            for i in range(len(self.deals)):
                await streaming.candle.subscribe(self.deals[i].figi, ti.CandleResolution.min1)
            # await streaming.orderbook.subscribe('BBG0013HGFT4', 5)
            # await streaming.instrument_info.subscribe('BBG0013HGFT4')
            async for event in streaming:
                print(event)
                payload = event.payload
                price = payload.o
                for i in range(len(self.deals)):
                    deal = self.deals[i]
                    strategy = self.strategies[i]
                    if deal.figi == payload.figi:
                        if self.try_put_buy_order(price, deal, strategy):
                            pass

                        self.balance.update()    


    def try_put_buy_order(self, price: float, deal: Deal, strategy: Strategy) -> bool:
        print(self.client.get_orders())
        if strategy.buy_range[0] < price < strategy.buy_range[1] and deal.available_money > price:
            lots = int(deal.available_money / price)
            limit_order_request = ti.LimitOrderRequest(lots, ti.OperationType.buy, price)
            res = self.client.post_orders_limit_order(deal.figi, limit_order_request)
            logger.create_log(LogType.info, f"{res}")
            return True

        return False

    
    # target is one of: o, c, h, l
    def generate_point(self, figi: str, from_: datetime, to: datetime, interval: ti.CandleResolution, target: str = "l"):
        response = self.client.get_market_candles(figi, from_, to, interval)
        candle = response.payload.candles[0]
        if target == "l":
            point = (from_.timestamp(), float(candle.l))
        if target == "h":
            point = (from_.timestamp(), float(candle.h))
        return point
    
    def create_strategy(self, ticker: str, canal: Canal):
        strategy = Strategy(ticker, canal)
        self.strategies.append(strategy)
        return strategy

    def test_strategy(self,
        strategy: Strategy,
        deal: Deal,
        from_: datetime, 
        to: datetime, 
        interval: ti.CandleResolution = ti.CandleResolution.week):

        buy_price, sell_price = 0, 0
        response = self.client.get_market_candles(deal.figi, from_, to, interval)
        candles = response.payload.candles
        logger.create_log(LogType.info, f"Starting strategy test for {strategy.ticker}")
        logger.create_log(LogType.info, f"Got {len(candles)} candles for strategy test")

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
                    figi=deal.figi,
                )
                response = self.client.set_sandbox_positions_balance(body, tokens.SANDBOX_ACCOUNT_ID)

                deal.make_operation(Operation(OperationType.BUY, low_price, ti.Currency.usd, available_lots))
                buy_price = low_price
                # self.logger.create_log(LogType.info, f"Status: {response.status}")
                logger.create_log(LogType.buy, f'''Buy range achieved: 
                    {strategy.ticker} {available_lots} lots for price {low_price} {deal.currency}
                    Date: {candle.time}''')
                logger.create_log(LogType.info, f"Balance: {deal.available_money} {deal.currency}")
            
            # SELL
            if high_price >= strategy.take_profit_price and deal.lots > 0:
                body = ti.SandboxSetPositionBalanceRequest(
                    balance=0,
                    figi=deal.figi,
                )
                response = self.client.set_sandbox_positions_balance(body, tokens.SANDBOX_ACCOUNT_ID)

                deal.make_operation(Operation(OperationType.SELL, high_price, ti.Currency.usd, available_lots))
                sell_price = high_price
                # self.logger.create_log(LogType.info, f"Status: {response.status}")
                logger.create_log(LogType.sell, f'''Take profit achieved: 
                    {strategy.ticker} {available_lots} lots for price {high_price} {deal.currency}
                    Profit: +{'{0:.2f}'.format(float(((sell_price / buy_price) - 1) * 100))} %
                    Date: {candle.time}''')
                logger.create_log(LogType.info, f"Balance: {deal.available_money} {deal.currency}")
        
        logger.create_log(LogType.info, f"Overall profit: {pretty(deal.profit)} {deal.currency} (+{deal.total_percentage_profit()} %)", send_to_telegram=True)
        logger.save_deal(deal.generate_json(), strategy.generate_json())
        # telegram_bot.send_message(tokens.TELEGRAM_CHAT_ID, f"Overall profit: {pretty(deal.profit)} {deal.currency} (+{deal.total_percentage_profit()} %)")

        # for operation in deal.operations:
        #     print(operation.type_, operation.price, operation.total_money)
    
    def get_figi_from_ticker(self, ticker):
        response = self.client.get_market_search_by_ticker(ticker)
        return response.payload.instruments[0].figi


class Sandbox:
    def __init__(self):
        self.client = ti.SyncClient(tokens.SANDBOX_TOKEN, use_sandbox=True)
        self.setup_sandbox()
        logger.create_log(LogType.info, "Sandbox was created")
    
    def setup_sandbox(self):
        body = ti.SandboxRegisterRequest.tinkoff_iis()
        self.client.register_sandbox_account(body)
        body = ti.SandboxSetCurrencyBalanceRequest(
            balance=100000,
            currency='RUB',
        )
        self.client.set_sandbox_currencies_balance(body, tokens.SANDBOX_ACCOUNT_ID)


def pretty(x: float) -> float:
    return '{0:.2f}'.format(float(x))

def str_to_currency(s: str):
    if s == "RUB":
        return ti.Currency.rub
    elif s == "USD":
        return ti.Currency.usd
    elif s == "EUR":
        return ti.Currency.eur
    return None

# print(tokens.TRADE_TOKEN, tokens.SANDBOX_TOKEN)
# client = ti.SyncClient(tokens.TRADE_TOKEN)

# response = client.get_market_search_by_ticker("AAPL")
# print(response.payload.instruments[0].name)

if __name__ == "__main__":
    trader = Trader()
    TelegramBot.trader = trader
    # TelegramBot.main()
    asyncio.run(trader.main())

