# backtester.py
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Tuple, Any
import warnings
warnings.filterwarnings("ignore", message="X does not have valid feature names")


class Backtester:
    """
    Fast, memory-conscious backtester.

    Key optimizations:
    - Avoids per-row DataFrame creation (no X_live dict/DataFrame inside loop)
    - Vectorized ML predictions for pure-ML strategies
    - Lightweight loop that works on NumPy arrays
    - Optional equity downsampling during the run (not after)
    """

    def __init__(self, data: pd.DataFrame, initial_cash: float = 10_000, max_points: int = 3000):
        # Avoid copying unless you mutate
        self.data = data
        self.initial_cash = float(initial_cash)
        self.max_points = max_points

        # state
        self.cash = self.initial_cash
        self.position = 0.0  # quantity
        self.trades: List[Tuple[pd.Timestamp, str, float, float]] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []

    def reset(self) -> None:
        self.cash = self.initial_cash
        self.position = 0.0
        self.trades = []
        self.equity_curve = []

    # ---------- internals ----------
    def _sample_every(self, n: int) -> int:
        if self.max_points <= 0:
            return 1
        k = max(1, n // self.max_points)
        return k

    # ---------- ML path ----------
    def _run_pure_ml(self, strategy) -> List[Tuple[pd.Timestamp, float]]:
        """
        Fast path for pure MLStrategy:
          - bulk predict once
          - lightweight simulation loop using numpy arrays
        """
        self.reset()
        df = self.data

        # Features in the right order (fill missing with 0, but do this ONCE)
        X_all = df.reindex(columns=strategy.feature_columns, fill_value=0)
        # Use numpy array to avoid pandas overhead inside model
        preds = strategy.model.predict(X_all.values)  # expected in {-1,0,1}

        prices = df["Close"].to_numpy(dtype=float, copy=False)
        dates = pd.to_datetime(df["Date"]).to_numpy()

        n = len(prices)
        sample_every = self._sample_every(n)

        for i in range(n):
            signal = preds[i]
            price = prices[i]
            ts = dates[i]

            # all-in/all-out logic
            if signal == 1:
                if self.cash > 0.0:
                    qty = self.cash / price
                    self.cash -= qty * price
                    self.position += qty
                    self.trades.append((pd.Timestamp(ts), "BUY", float(qty), float(price)))

            elif signal == -1:
                if self.position > 0.0:
                    qty = self.position
                    self.cash += qty * price
                    self.position = 0.0
                    self.trades.append((pd.Timestamp(ts), "SELL", float(qty), float(price)))

            # record equity sparsely (and always record last)
            if (i % sample_every) == 0 or i == n - 1:
                equity = self.cash + self.position * price
                self.equity_curve.append((pd.Timestamp(ts), float(equity)))

        return self.equity_curve

    # ---------- Mixed/Rule-based path ----------
    def _run_general(self, strategy) -> List[Tuple[pd.Timestamp, float]]:
        """
        General path (rule-based or Ensemble with ML inside).
        Still lean: pre-slice once, avoid per-iteration allocations.
        """
        self.reset()
        df = self.data

        prices = df["Close"].to_numpy(dtype=float, copy=False)
        dates = pd.to_datetime(df["Date"]).to_numpy()
        n = len(prices)
        sample_every = self._sample_every(n)

        # If the strategy (or any sub strategy) needs features,
        # prepare a features frame ONCE and slice from it per step.
        needs_features = False
        feature_frame = None

        if hasattr(strategy, "strategies"):
            needs_features = any(hasattr(s, "feature_columns") for s in strategy.strategies)
        elif hasattr(strategy, "feature_columns"):
            needs_features = True

        if needs_features:
            # Keep only needed columns and in correct order; missing -> 0
            # For ensemble with multiple ML blocks, take the union of all needed columns.
            feature_cols = []
            if hasattr(strategy, "strategies"):
                for s in strategy.strategies:
                    if hasattr(s, "feature_columns"):
                        feature_cols.extend(list(s.feature_columns))
            else:
                feature_cols = list(strategy.feature_columns)

            feature_cols = sorted(set(feature_cols))
            feature_frame = df.reindex(columns=feature_cols, fill_value=0)

        # lightweight loop
        for i in range(n):
            price = prices[i]
            ts = pd.Timestamp(dates[i])

            if feature_frame is not None:
                # small one-row view; faster than re-constructing dict/DataFrame
                X_live = feature_frame.iloc[[i]]
                signal = strategy.generate_signal(price=price, date=ts, X_live=X_live)
            else:
                signal = strategy.generate_signal(price=price, date=ts)

            if signal == "BUY":
                if self.cash > 0.0:
                    qty = self.cash / price
                    self.cash -= qty * price
                    self.position += qty
                    self.trades.append((ts, "BUY", float(qty), float(price)))

            elif signal == "SELL":
                if self.position > 0.0:
                    qty = self.position
                    self.cash += qty * price
                    self.position = 0.0
                    self.trades.append((ts, "SELL", float(qty), float(price)))

            if (i % sample_every) == 0 or i == n - 1:
                equity = self.cash + self.position * price
                self.equity_curve.append((ts, float(equity)))

        return self.equity_curve

    # ---------- public ----------
    def run(self, strategy) -> List[Tuple[pd.Timestamp, float]]:
        """
        Dispatch for ML vs non-ML strategies.
        """
        # Pure ML strategy -> fastest path with bulk predict
        if strategy.__class__.__name__ == "MLStrategy":
            return self._run_pure_ml(strategy)

        # Ensemble: if contains ML, use general path (we still prebuild features)
        if strategy.__class__.__name__ == "EnsembleStrategy":
            has_ml = any(hasattr(s, "feature_columns") for s in strategy.strategies)
            return self._run_general(strategy) if has_ml else self._run_general(strategy)

        # Rule-based only
        return self._run_general(strategy)
