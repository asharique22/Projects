# strategy.py
from __future__ import annotations
import collections
import numpy as np
import pandas as pd
import joblib

# ========================
# Moving Average Crossover
# ========================
class MovingAverageStrategy:
    """
    O(1) updates using rolling sums instead of recomputing means on full history.
    """
    def __init__(self, short_window: int, long_window: int):
        self.short_window = int(short_window)
        self.long_window = int(long_window)

        self.short_q = collections.deque(maxlen=self.short_window)
        self.long_q  = collections.deque(maxlen=self.long_window)
        self.sum_short = 0.0
        self.sum_long  = 0.0
        self.last_signal = "HOLD"

    def _push(self, q: collections.deque, s_attr: str, price: float):
        # subtract old val if deque is full
        if len(q) == q.maxlen:
            old = q[0]
            setattr(self, s_attr, getattr(self, s_attr) - old)
        q.append(price)
        setattr(self, s_attr, getattr(self, s_attr) + price)

    def generate_signal(self, price, date):
        price = float(price)
        self._push(self.short_q, "sum_short", price)
        self._push(self.long_q,  "sum_long",  price)

        if len(self.long_q) < self.long_window:
            return "HOLD"

        short_ma = self.sum_short / len(self.short_q)
        long_ma  = self.sum_long  / len(self.long_q)

        if short_ma > long_ma and self.last_signal != "BUY":
            self.last_signal = "BUY"
            return "BUY"
        elif short_ma < long_ma and self.last_signal != "SELL":
            self.last_signal = "SELL"
            return "SELL"
        else:
            return "HOLD"

# ========================
# Mean Reversion
# ========================
class MeanReversionStrategy:
    """
    Sliding window with deque; O(1) mean via rolling sum.
    """
    def __init__(self, window: int, threshold: float):
        self.window = int(window)
        self.threshold = float(threshold)
        self.q = collections.deque(maxlen=self.window)
        self.sum_win = 0.0

    def generate_signal(self, price, date):
        price = float(price)
        if len(self.q) == self.window:
            self.sum_win -= self.q[0]
        self.q.append(price)
        self.sum_win += price

        if len(self.q) < self.window + 1:
            return "HOLD"

        # Last window excludes current price to mirror your original logic
        mean_price = (self.sum_win - price) / self.window

        if price < mean_price * (1 - self.threshold):
            return "BUY"
        elif price > mean_price * (1 + self.threshold):
            return "SELL"
        else:
            return "HOLD"

# ========================
# ML-based Strategy
# ========================
class MLStrategy:
    """
    Keep API compatible with Ensemble:
      generate_signal(price=None, date=None, X_live=<1xN DataFrame>)
    """
    def __init__(self, model_path: str = "model.pkl"):
        self.model, self.feature_columns = joblib.load(model_path)

    def generate_signal(self, price=None, date=None, X_live: pd.DataFrame | None = None):
        if X_live is None:
            raise ValueError("X_live required for MLStrategy")
        X_live = X_live.reindex(columns=self.feature_columns, fill_value=0)
        pred = self.model.predict(X_live.values)[0]  # {-1,0,1}

        if pred == 1:
            return "BUY"
        elif pred == -1:
            return "SELL"
        else:
            return "HOLD"

class EMACrossoverStrategy:
    """
    EMA crossover with O(1) updates (no re-creating Series each tick).
    """
    def __init__(self, short_window=12, long_window=26):
        self.short_window = int(short_window)
        self.long_window  = int(long_window)
        self.alpha_s = 2.0 / (self.short_window + 1.0)
        self.alpha_l = 2.0 / (self.long_window  + 1.0)
        self.ema_s = None
        self.ema_l = None
        self.seed = []
        self.last_signal = "HOLD"

    def generate_signal(self, price, date):
        price = float(price)
        # Warmup until we have long_window prices
        if len(self.seed) < self.long_window:
            self.seed.append(price)
            if len(self.seed) == self.long_window:
                s_series = pd.Series(self.seed[-self.short_window:])
                l_series = pd.Series(self.seed)
                self.ema_s = s_series.mean()
                self.ema_l = l_series.mean()
            return "HOLD"

        # Recursive EMA updates
        self.ema_s = self.alpha_s * price + (1 - self.alpha_s) * self.ema_s
        self.ema_l = self.alpha_l * price + (1 - self.alpha_l) * self.ema_l

        if self.ema_s > self.ema_l and self.last_signal != "BUY":
            self.last_signal = "BUY"
            return "BUY"
        elif self.ema_s < self.ema_l and self.last_signal != "SELL":
            self.last_signal = "SELL"
            return "SELL"
        else:
            return "HOLD"

class BollingerBandsStrategy:
    """
    Sliding window with deque; window is small (default 20), so np ops are cheap.
    """
    def __init__(self, window=20, num_std=2.0):
        self.window = int(window)
        self.num_std = float(num_std)
        self.q = collections.deque(maxlen=self.window)

    def generate_signal(self, price, date):
        price = float(price)
        self.q.append(price)
        if len(self.q) < self.window:
            return "HOLD"

        arr = np.fromiter(self.q, dtype=float, count=len(self.q))
        mean = arr.mean()
        std = arr.std(ddof=1) if len(arr) > 1 else 0.0
        upper = mean + self.num_std * std
        lower = mean - self.num_std * std

        if price < lower:
            return "BUY"
        elif price > upper:
            return "SELL"
        else:
            return "HOLD"

class MomentumStrategy:
    def __init__(self, lookback=10):
        self.lookback = int(lookback)
        self.q = collections.deque(maxlen=self.lookback + 1)

    def generate_signal(self, price, date):
        price = float(price)
        self.q.append(price)
        if len(self.q) <= self.lookback:
            return "HOLD"
        past_price = self.q[0]
        ret = (price - past_price) / past_price if past_price != 0 else 0.0
        if ret > 0:
            return "BUY"
        elif ret < 0:
            return "SELL"
        else:
            return "HOLD"

class EnsembleStrategy:
    """
    Weighted voting across strategies.
    """
    def __init__(self, strategies, weights=None):
        self.strategies = strategies
        self.weights = weights if weights else [1] * len(strategies)

    def generate_signal(self, price=None, date=None, X_live: pd.DataFrame | None = None):
        signals = []
        for strat in self.strategies:
            if hasattr(strat, "feature_columns"):
                if X_live is None:
                    raise ValueError("X_live (features) required for MLStrategy within Ensemble")
                signals.append(strat.generate_signal(X_live=X_live, date=date))
            else:
                signals.append(strat.generate_signal(price, date))

        score = 0
        for sig, w in zip(signals, self.weights):
            if sig == "BUY":
                score += w
            elif sig == "SELL":
                score -= w

        return "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
