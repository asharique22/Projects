# backtester.py
from engine import MatchingEngine

class Backtester:
    def __init__(self, data, initial_cash=10000, engine=None):
        self.data = data
        self.cash = initial_cash
        self.position = 0
        self.trades = []
        self.equity_curve = []
        self.engine = engine if engine else MatchingEngine()

    def run(self, strategy):
        for date, row in self.data.iterrows():
            price = float(row['Close'])
            signal = strategy.generate_signal(price, date)

            if signal == "BUY" and self.cash >= price:
                qty = int(self.cash // price)
                trades = self.engine.add_order("BUY", qty, price)
                for t in trades:
                    cost = t["qty"] * t["price"]
                    self.cash -= cost
                    self.position += t["qty"]
                    self.trades.append((date, "BUY", t["qty"], t["price"]))

            elif signal == "SELL" and self.position > 0:
                qty = self.position
                trades = self.engine.add_order("SELL", qty, price)
                for t in trades:
                    value = t["qty"] * t["price"]
                    self.cash += value
                    self.position -= t["qty"]
                    self.trades.append((date, "SELL", t["qty"], t["price"]))

            equity = self.cash + self.position * price
            self.equity_curve.append((date, equity))

        return self.equity_curve
