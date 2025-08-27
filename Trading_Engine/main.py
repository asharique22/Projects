# main.py
import os
import threading
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from build_feature import build_features

from backtester import Backtester
from strategy import EnsembleStrategy, EMACrossoverStrategy, BollingerBandsStrategy, MeanReversionStrategy, MovingAverageStrategy, MLStrategy
from Virtual_trader import PaperTrader
from binance import ThreadedWebsocketManager


# ================= CONFIG =================
MODE            = "paper"           # "backtest" or "paper"
SYMBOL          = "BTCUSDT"
KLINE_INTERVAL  = "1s"
INITIAL_CASH    = 10_000
CSV_FILE        = "features.csv"
MODEL_PATH      = "model.pkl"

# Plot performance
MAX_POINTS      = 3000
REFRESH_MS      = 500
# ==========================================

strategy = EnsembleStrategy([
    EMACrossoverStrategy(),
    BollingerBandsStrategy(),
    MeanReversionStrategy(20, 0.02),
    MovingAverageStrategy(5, 10),
    MLStrategy(MODEL_PATH)
])

# ---------- Realtime Plot Helper ----------
class LivePlotter:
    def __init__(self, max_points=3000):
        self.max_points = max_points

        # buffers
        self.ts_buf, self.price_buf = [], []
        self.eq_ts_buf, self.equity_buf = [], []
        self.buy_ts, self.buy_px = [], []
        self.sell_ts, self.sell_px = [], []

        # locks
        self.lock = threading.Lock()

        # figure
        self.fig, (self.ax_price, self.ax_equity) = plt.subplots(
            2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios":[3, 2]}
        )
        self.fig.suptitle(f"{SYMBOL} — Live Price & Equity", fontsize=12)

        # artists
        (self.price_line,)  = self.ax_price.plot([], [], label="Price")
        self.buy_scatter    = self.ax_price.scatter([], [], marker="^", s=40, c="g", label="BUY")
        self.sell_scatter   = self.ax_price.scatter([], [], marker="v", s=40, c="r", label="SELL")
        (self.equity_line,) = self.ax_equity.plot([], [], label="Equity", color="purple")

        # style
        self.ax_price.grid(True, alpha=0.3)
        self.ax_equity.grid(True, alpha=0.3)
        self.ax_price.legend(loc="upper left")
        self.ax_equity.legend(loc="upper left")
        self.ax_equity.set_ylabel("Equity")
        self.ax_price.set_ylabel("Price")

        self.ax_equity.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        self.fig.autofmt_xdate()

    def add_price_point(self, ts, price):
        with self.lock:
            self.ts_buf.append(ts)
            self.price_buf.append(price)
            self.ts_buf = self.ts_buf[-self.max_points:]
            self.price_buf = self.price_buf[-self.max_points:]

    def add_equity_point(self, ts, equity):
        with self.lock:
            self.eq_ts_buf.append(ts)
            self.equity_buf.append(equity)
            self.eq_ts_buf = self.eq_ts_buf[-self.max_points:]
            self.equity_buf = self.equity_buf[-self.max_points:]

    def add_buy(self, ts, price):
        with self.lock:
            self.buy_ts.append(ts)
            self.buy_px.append(price)

    def add_sell(self, ts, price):
        with self.lock:
            self.sell_ts.append(ts)
            self.sell_px.append(price)

    def _snapshot(self):
        with self.lock:
            return (
                list(self.ts_buf), list(self.price_buf),
                list(self.eq_ts_buf), list(self.equity_buf),
                list(self.buy_ts), list(self.buy_px),
                list(self.sell_ts), list(self.sell_px),
            )

    def animate(self, _frame):
        ts, px, ets, eq, bts, bpx, sts, spx = self._snapshot()

        if ts:
            self.price_line.set_data(mdates.date2num(ts), px)
            self.ax_price.relim()
            self.ax_price.autoscale_view()

        if bts:
            self.buy_scatter.set_offsets(np.column_stack([mdates.date2num(bts), bpx]))
        if sts:
            self.sell_scatter.set_offsets(np.column_stack([mdates.date2num(sts), spx]))

        if ets:
            self.equity_line.set_data(mdates.date2num(ets), eq)
            self.ax_equity.relim()
            self.ax_equity.autoscale_view()

        return (self.price_line, self.buy_scatter, self.sell_scatter, self.equity_line)

    def start(self, interval_ms=500):
        self.ani = FuncAnimation(self.fig, self.animate, interval=interval_ms, blit=False)
        print("📈 Live plot started...")
        while plt.fignum_exists(self.fig.number):
            plt.pause(0.1)
# ------------------------------------------


def run_backtest():
    print("📊 Running BACKTEST...")
    df = pd.read_csv(CSV_FILE)

    backtester = Backtester(df, initial_cash=INITIAL_CASH)
    equity_curve = backtester.run(strategy)

    equity_df = pd.DataFrame(equity_curve, columns=["Date", "Equity"])
    equity_df = equity_df.iloc[::max(1, len(equity_df)//3000)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pd.to_datetime(equity_df["Date"]), equity_df["Equity"], label="Equity")
    ax.set_title("Backtest Equity Curve")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    plt.show()

    print("\n✅ Backtest complete")
    print("Final Equity:", float(equity_df["Equity"].iloc[-1]))
    print("Trades:", backtester.trades)


def run_papertrade():
    print("🚀 Starting PAPER TRADING... (live Binance feed)")
    print("Type 'q' + Enter anytime to stop.")

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    trader = PaperTrader(initial_cash=INITIAL_CASH)
    plotter = LivePlotter(max_points=MAX_POINTS)

    history, history_lock = [], threading.Lock()

    def handle_socket_message(msg):
        if msg.get("e") != "kline":
            return
        k = msg["k"]
        
        new_row = {
            "Date": pd.to_datetime(k['t'], unit='ms'),
            "Open": float(k['o']),
            "High": float(k['h']),
            "Low": float(k['l']),
            "Close": float(k['c']),
            "Volume": float(k['v']),
        }
        
        close_price = float(k["c"])
        ts = datetime.fromtimestamp(k["T"] / 1000.0)

        # Store incoming price
        with history_lock:
            history.append(new_row)
            df = pd.DataFrame(history)

        # Detect if strategy is ML or ensemble with ML inside
        requires_features = (
            isinstance(strategy, MLStrategy) or
            any(hasattr(s, "feature_columns") for s in getattr(strategy, "strategies", []))
        )

        if requires_features:
            if len(df) < 50:  # not enough history to compute indicators
                plotter.add_price_point(ts, new_row["Close"])
                equity_now = trader.cash + trader.position * new_row["Close"]
                plotter.add_equity_point(ts, equity_now)
                return

            df = build_features(df)

            # Latest row of features (excluding non-feature columns)
            X_live = df.iloc[[-1]].drop(columns=["Date"])
            signal = strategy.generate_signal(
                price=new_row["Close"], date=ts, X_live=X_live
            )
        else:
            # Pure rule-based strategy
            signal = strategy.generate_signal(price=new_row["Close"], date=ts)


        # Execute trade
        buy_signals, sell_signals = [], []
        trader.execute(signal, close_price, ts, buy_signals, sell_signals)

        # Update plot with trade markers
        for bts, bpx in buy_signals:
            plotter.add_buy(bts, bpx)
        for sts, spx in sell_signals:
            plotter.add_sell(sts, spx)

        # Update live price + equity
        plotter.add_price_point(ts, close_price)
        equity_now = trader.cash + trader.position * close_price
        plotter.add_equity_point(ts, equity_now)

    def stop_listener():
        while True:
            cmd = input()
            if cmd.lower() in ("q", "quit", "exit", "stop"):
                print("🛑 Stopping...")
                twm.stop()
                plt.close("all")
                break

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()
    twm.start_kline_socket(callback=handle_socket_message, symbol=SYMBOL, interval=KLINE_INTERVAL)

    threading.Thread(target=stop_listener, daemon=True).start()

    plotter.start(interval_ms=REFRESH_MS)

if __name__ == "__main__":
    if MODE == "backtest":
        run_backtest()
    elif MODE == "paper":
        run_papertrade()
    else:
        print("❌ Invalid MODE. Use 'backtest' or 'paper'.")
