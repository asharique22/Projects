from datetime import datetime

class PaperTrader:
    def __init__(self, initial_cash=100000):
        self.cash = initial_cash
        self.position = 0
        self.trades = []
        self.equity_curve = []
        self.equity = self.cash

    def execute(self, signal, price, date, buy_signal, sell_signal):
        executed = "X"

        if signal == "BUY" and self.cash > 0:
            qty = self.cash / price
            self.cash -= qty * price
            self.position += qty
            self.trades.append((date, "BUY", qty, price))
            executed = "BUY"

        elif signal == "SELL" and self.position > 0:
            qty = self.position
            self.cash += qty * price
            self.position = 0
            self.trades.append((date, "SELL", qty, price))
            executed = "SELL"

        self.equity = self.cash + self.position * price
        self.equity_curve.append((date, self.equity))

        if executed != "X":
            last_trade = self.trades[-1]
            print(
                f"TRADE EXECUTED: {last_trade[1]} {last_trade[2]:.4f} "
                f"@ {last_trade[3]:.2f} | Cash={self.cash:.2f}, "
                f"Pos={self.position:.4f}, Equity={self.equity:.2f}"
            )
            if executed == "BUY":
                buy_signal.append((date, price))
            elif executed == "SELL":
                sell_signal.append((date, price))
        else:
            print(
                f"HOLD | Time={date} | Price={price:.2f} | Equity={self.equity:.2f}"
            )

        return self.equity
