import os
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import resample
from binance.client import Client
from sklearn.model_selection import GridSearchCV


api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)


klines = client.get_historical_klines(
    "BTCUSDT", 
    Client.KLINE_INTERVAL_1MINUTE, 
    "30 day ago UTC"
)

df = pd.DataFrame(klines, columns=[
    "timestamp","Open","High","Low","Close","Volume",
    "Close_time","Quote_asset_volume","Number_of_trades",
    "Taker_buy_base","Taker_buy_quote","Ignore"
])

# Keep only required fields
df["Close"]  = df["Close"].astype(float)
df["High"]   = df["High"].astype(float)
df["Low"]    = df["Low"].astype(float)
df["Volume"] = df["Volume"].astype(float)
df["Date"]   = pd.to_datetime(df["timestamp"], unit="ms")

df = df[["Date","Close","High","Low","Volume"]]


df["return_1"] = df["Close"].pct_change()
df["ma_5"]     = df["Close"].rolling(5).mean()
df["ma_10"]    = df["Close"].rolling(10).mean()
df["ma_diff"]  = df["ma_5"] - df["ma_10"]

# --- RSI (14)
delta     = df["Close"].diff()
gain      = np.where(delta > 0, delta, 0)
loss      = np.where(delta < 0, -delta, 0)
avg_gain  = pd.Series(gain).rolling(14).mean()
avg_loss  = pd.Series(loss).rolling(14).mean()
rs        = avg_gain / (avg_loss + 1e-9)
df["RSI_14"] = 100 - (100 / (1 + rs))


ema12 = df["Close"].ewm(span=12, adjust=False).mean()
ema26 = df["Close"].ewm(span=26, adjust=False).mean()
df["MACD"]        = ema12 - ema26
df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()


ma20      = df["Close"].rolling(20).mean()
std20     = df["Close"].rolling(20).std()
df["BB_upper"] = ma20 + (2 * std20)
df["BB_lower"] = ma20 - (2 * std20)
df["BB_width"] = df["BB_upper"] - df["BB_lower"]

df["volatility_20"] = df["return_1"].rolling(20).std()

df.dropna(inplace=True)

df["signal"] = 0
df.loc[df["return_1"] >  0.00007, "signal"] =  1   # BUY
df.loc[df["return_1"] < -0.00007, "signal"] = -1   # SELL

print("\n📊 Original signal distribution:")
print(df["signal"].value_counts(normalize=True))


feature_cols = [
    "return_1","ma_5","ma_10","ma_diff",
    "RSI_14","MACD","MACD_signal",
    "BB_upper","BB_lower","BB_width",
    "volatility_20"
]

df.to_csv("features.csv", index=False)

X = df[feature_cols]
y = df["signal"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=True, random_state=42
)

print("\n📊 Train label distribution:")
print(y_train.value_counts(normalize=True))

print("\n📊 Test label distribution:")
print(y_test.value_counts(normalize=True))

pipeline = Pipeline([
    ("classifier", RandomForestClassifier())
])

param_grid = {
    "classifier__n_estimators": [300, 600, 900],
    "classifier__max_depth": [None, 10, 20, 30, 40],
    "classifier__min_samples_split": [2, 5, 10, 13, 17]
}

model = GridSearchCV(pipeline, param_grid, cv=2, n_jobs=-1)
model.fit(X_train, y_train)

print("\n✅ Training Complete")
print("Test Accuracy:", model.score(X_test, y_test))
print("Predictions distribution on test set:")
print(pd.Series(model.predict(X_test)).value_counts(normalize=True))


joblib.dump(model, "ml_model.pkl")
print("\n💾 Model saved as ml_model.pkl")

# Also save model with feature column names
feature_columns = X_train.columns.tolist()
joblib.dump((model, feature_columns), "model.pkl")
print("💾 Model + features saved as model.pkl")
