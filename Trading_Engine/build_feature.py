import pandas as pd
import numpy as np

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build technical indicator features for trading strategy.
    Expects df with columns: ["timestamp" or "Date", "Close", "High", "Low", "Volume"]
    Returns df with features and signals.
    """

    # Create a single, definitive copy to work on
    df = df.copy()

    # Ensure Date column exists
    if "timestamp" in df.columns:
        df.loc[:, "Date"] = pd.to_datetime(df["timestamp"], unit="ms")
    elif "Date" not in df.columns:
        raise ValueError("DataFrame must contain either 'timestamp' or 'Date'")

    # Ensure correct datatypes
    df = df.astype({
        "Close": float,
        "High": float,
        "Low": float,
        "Volume": float
    })

    # Keep only required columns and continue working on the same DataFrame
    df = df[["Date", "Close", "High", "Low", "Volume"]]

    # Returns and Moving Averages
    df.loc[:, "return_1"] = df["Close"].pct_change()
    df.loc[:, "ma_5"] = df["Close"].rolling(5).mean()
    df.loc[:, "ma_10"] = df["Close"].rolling(10).mean()
    df.loc[:, "ma_diff"] = df["ma_5"] - df["ma_10"]

    # RSI
    delta = df["Close"].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain, index=df.index).rolling(14).mean()
    avg_loss = pd.Series(loss, index=df.index).rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df.loc[:, "RSI_14"] = 100 - (100 / (1 + rs))

    # ROC
    df.loc[:, "ROC_10"] = df["Close"].pct_change(10)

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df.loc[:, "MACD"] = ema12 - ema26
    df.loc[:, "MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    ma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df.loc[:, "BB_upper"] = ma20 + (2 * std20)
    df.loc[:, "BB_lower"] = ma20 - (2 * std20)
    df.loc[:, "BB_width"] = df["BB_upper"] - df["BB_lower"]

    # Volatility
    df.loc[:, "volatility_20"] = df["return_1"].rolling(20).std()

    # Stochastic Oscillator
    low14 = df["Low"].rolling(14).min()
    high14 = df["High"].rolling(14).max()
    df.loc[:, "%K"] = (df["Close"] - low14) * 100 / (high14 - low14)
    df.loc[:, "%D"] = df["%K"].rolling(3).mean()

    # Drop unused raw columns
    df = df.dropna().reset_index(drop=True)
    df = df.drop(columns=["High", "Low", "Volume", "return_1"], errors="ignore")

    # Signals
    df.loc[:, "signal"] = np.where(df["ma_5"] > df["ma_10"], 1,
                                   np.where(df["ma_5"] < df["ma_10"], -1, 0))

    return df