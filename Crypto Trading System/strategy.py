# strategy.py
# Contains different trading strategies for backtesting
# Each strategy has a generate_signal(price, date) method
# that returns "BUY", "SELL", or "HOLD".

import numpy as np
import pandas as pd

import joblib

class MovingAverageStrategy:
    def __init__(self, short_window, long_window):
        self.short_window = short_window
        self.long_window = long_window
        self.history = []
        self.short_ma_values = []
        self.long_ma_values = []
        self.last_signal = "HOLD"

    def generate_signal(self, price, date):
        self.history.append(price)

        if len(self.history) < self.long_window:
            self.short_ma_values.append(None)
            self.long_ma_values.append(None)
            return "HOLD"

        short_ma = sum(self.history[-self.short_window:]) / self.short_window
        long_ma = sum(self.history[-self.long_window:]) / self.long_window

        self.short_ma_values.append(short_ma)
        self.long_ma_values.append(long_ma)

        if short_ma > long_ma and self.last_signal != "BUY":
            self.last_signal = "BUY"
            return "BUY"
        elif short_ma < long_ma and self.last_signal != "SELL":
            self.last_signal = "SELL"
            return "SELL"
        else:
            return "HOLD"

class MeanReversionStrategy:
    """
    A Mean Reversion strategy.
    - Assumes price tends to revert to its recent average.
    - BUY signal: when price falls below (mean - threshold%)
    - SELL signal: when price rises above (mean + threshold%)
    - HOLD otherwise.
    """
    def __init__(self, window, threshold):
        self.window = window
        self.threshold = threshold
        self.history = []

    def generate_signal(self, price, date):
        self.history.append(price)

        if len(self.history) < self.window:
            return "HOLD"

        # Use past `window` days (excluding today for realism)
        mean_price = sum(self.history[-self.window-1:-1]) / self.window

        if price < mean_price * (1 - self.threshold):
            return "BUY"
        elif price > mean_price * (1 + self.threshold):
            return "SELL"
        else:
            return "HOLD"

class MLStrategy:
    def __init__(self, model_path="model.pkl"):
        self.model, self.feature_columns = joblib.load(model_path)

    def generate_signal(self, X_live, ts):
        X_live = X_live.reindex(columns=self.feature_columns, fill_value=0)

        prediction = self.model.predict(X_live)[0]
        
        if prediction == 1:
            return "BUY"
        elif prediction == -1:
            return "SELL"
        else:
            return "HOLD"
