# main.py
import os
import threading
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from binance import ThreadedWebsocketManager

from strategy import MovingAverageStrategy, MeanReversionStrategy, MLStrategy
from Virtual_trader import PaperTrader


SYMBOL = "BTCUSDT"
KLINE_INTERVAL = "1s" 
ANIM_INTERVAL_MS = 200 

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

strategy = MLStrategy()

trader = PaperTrader(initial_cash=1000)


# =========================
history = []         # list of dicts: {"Date": ts, "Close": price}
buy_signals = []     # list of tuples: (ts, price)
sell_signals = []    # list of tuples: (ts, price)

history_lock = threading.Lock()
signals_lock = threading.Lock()
trader_lock = threading.Lock()


def handle_socket_message(msg):
    if msg.get("e") != "kline":
        return

    k = msg["k"]
    close_price = float(k["c"])
    ts = datetime.fromtimestamp(k["T"] / 1000.0)

    # Append latest tick safely
    with history_lock:
        history.append({"Date": ts, "Close": close_price})
        df = pd.DataFrame(history)

    # Generate signal
    if isinstance(strategy, MLStrategy):
        # Need enough bars for features
        if len(df) < 50:
            return

        # Build live features (mirror training)
        df["return_1"] = df["Close"].pct_change()
        df["ma_5"] = df["Close"].rolling(5).mean()
        df["ma_10"] = df["Close"].rolling(10).mean()
        df["ma_diff"] = df["ma_5"] - df["ma_10"]

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI_14"] = 100 - (100 / (1 + rs))

        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        ma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        df["BB_upper"] = ma20 + (2 * std20)
        df["BB_lower"] = ma20 - (2 * std20)
        df["BB_width"] = df["BB_upper"] - df["BB_lower"]

        df["volatility_20"] = df["return_1"].rolling(20).std()
        df.dropna(inplace=True)

        X_live = df.iloc[[-1]].drop(columns=["Date", "Close"])
        signal = strategy.generate_signal(X_live, ts)
    else:
        signal = strategy.generate_signal(close_price, ts)

    with trader_lock:
        equity = trader.execute(signal, close_price, ts, buy_signals, sell_signals)


fig, (ax_price, ax_equity) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

def animate(_frame_idx):
    with history_lock:
        if not history:
            return
        df = pd.DataFrame(history).copy()

    df["ma_20"] = df["Close"].rolling(20).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()

    ax_price.clear()
    ax_price.plot(df["Date"], df["Close"], label="Close", color="black")
    if df["ma_20"].notna().any():
        ax_price.plot(df["Date"], df["ma_20"], label="MA20", color="blue")
    if df["ma_50"].notna().any():
        ax_price.plot(df["Date"], df["ma_50"], label="MA50", color="orange")

    with signals_lock:
        if buy_signals:
            ax_price.scatter(
                [t for t, _p in buy_signals],
                [p for _t, p in buy_signals],
                marker="^", color="green", s=80, label="BUY"
            )
        if sell_signals:
            ax_price.scatter(
                [t for t, _p in sell_signals],
                [p for _t, p in sell_signals],
                marker="v", color="red", s=80, label="SELL"
            )

    ax_price.set_title(f"{SYMBOL} — Price with MA20/MA50")
    ax_price.legend(loc="upper left")
    ax_price.grid(True, alpha=0.2)

    ax_equity.clear()
    with trader_lock:
        eq = getattr(trader, "equity_curve", None)
        if eq:
            equity_df = pd.DataFrame(eq, columns=["Date", "Equity"])
        else:
            equity_df = pd.DataFrame(columns=["Date", "Equity"])

    if not equity_df.empty:
        ax_equity.plot(equity_df["Date"], equity_df["Equity"], color="purple", label="Equity")
        ax_equity.legend(loc="upper left")
    ax_equity.set_title("Equity Curve")
    ax_equity.grid(True, alpha=0.2)

    plt.tight_layout()


if __name__ == "__main__":
    print("🚀 Starting real-time trading bot...")

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()
    twm.start_kline_socket(callback=handle_socket_message, symbol=SYMBOL, interval=KLINE_INTERVAL)

    ani = FuncAnimation(fig, animate, interval=ANIM_INTERVAL_MS)
    plt.show()

    twm.join()
