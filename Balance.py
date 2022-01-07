import tinvest as ti

class Balance:
    def __init__(self, client, id=None):
        self.client = client
        self.id = id
        self.rub = 0
        self.usd = 0
        self.euro = 0
        self.blocked = [0, 0, 0] # rub, usd, euro
    
    def update(self):
        response = self.client.get_portfolio_currencies(self.id)
        # print(response.payload)
        for currencyData in response.payload.currencies:
            if currencyData.currency == ti.Currency.rub:
                self.rub = float(currencyData.balance)
                self.blocked[0] = float(currencyData.blocked) if currencyData.blocked else 0

            if currencyData.currency == ti.Currency.usd:
                self.usd = float(currencyData.balance)
                self.blocked[1] = float(currencyData.blocked) if currencyData.blocked else 0

            if currencyData.currency == ti.Currency.eur:
                self.euro = float(currencyData.balance)
                self.blocked[2] = float(currencyData.blocked) if currencyData.blocked else 0

        # print(self.rub, self.usd, self.euro)
        # print(self.blocked)
    
    def get_current(self) -> str:
        return f'''Balance:
        RUB: {self.rub},
        USD: {self.usd},
        EUR: {self.euro},
        Blocked: {self.blocked}'''
