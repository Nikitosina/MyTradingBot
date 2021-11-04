from enum import Enum
from pprint import pprint
import tinvest as ti
import tokens


class Operation(Enum):
    SELL = 0
    BUY = 1


class Helper: 
    def __init__(self):
        self.client = ti.SyncClient(tokens.TRADE_TOKEN)
        self.next_operation = Operation.BUY
    
    def get_balance(self):
        response = self.client.get_portfolio()
        for position in response.payload:
            if position.name == "Доллар США":
                print(position)
        # pprint(response.payload)


# print(tokens.TRADE_TOKEN, tokens.SANDBOX_TOKEN)
# client = ti.SyncClient(tokens.TRADE_TOKEN)

# response = client.get_market_search_by_ticker("AAPL")
# print(response.payload.instruments[0].name)

helper = Helper()
helper.get_balance()
