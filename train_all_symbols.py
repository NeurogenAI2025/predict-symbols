import requests
import pandas as pd
import numpy as np
import os
import time
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import pandas_ta as ta
import joblib

# Setări directoare
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"

for d in [DATA_DIR, MODELS_DIR, SCALERS_DIR]:
    d.mkdir(exist_ok=True)

# Lista de simboluri CoinGecko (exemplu)
symbols = [
    "bitcoin", "ethereum", "solana", "ripple", "cardano", "dogecoin", "avalanche-2", "polkadot",
    "tron", "litecoin", "chainlink", "uniswap", "stellar", "near", "aptos", "vechain", "filecoin",
    "algorand", "fantom", "the-graph", "tezos", "theta-token", "elrond-erd-2", "eos", "zilliqa",
    "helium", "arbitrum", "optimism", "osmosis", "render-token", "radix", "harmony", "kadena",
    "nervos-network", "iotex", "celo", "flux", "wax", "ravencoin", "metis-token", "enjincoin",
    "injective-protocol", "loopring", "dydx", "terra-luna", "terra-luna-2", "audius", "waves"
]

def download_data_from_coingecko(symbol):
    print(f"\n🔁 Procesare simbol: {symbol}")
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=365&interval=daily"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NRGBot/1.0; +https://nrgai.com)"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        prices = data.get("prices", [])
        if not prices:
            print(f"⚠️  Nu s-au putut obține date pentru {symbol}")
            return None

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms").dt.floor("D")
        df = df.sort_values("timestamp")
        df = df.drop_duplicates(subset="timestamp", keep="last")
        df.to_csv(DATA_DIR / f"{symbol}.csv", index=False)
        print(f"✅ Date salvate pentru {symbol}")
        return df

    except Exception as e:
        print(f"❌ Eroare la {symbol}: {e}")
        return None

def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def train_model(symbol):
    print(f"🔧 Antrenez model pentru {symbol}...")
    csv_path = DATA_DIR / f"{symbol}.csv"
    if not csv_path.exists():
        print(f"⚠️  Fișier CSV lipsă pentru {symbol}")
        return

    df = pd.read_csv(csv_path)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df.dropna(inplace=True)

    # Indicatori tehnici
    df["sma_10"] = df["price"].rolling(window=10).mean()
    df["sma_50"] = df["price"].rolling(window=50).mean()
    df["rsi_14"] = compute_rsi(df["price"], 14)
    macd = ta.macd(df['price'], fast=12, slow=26, signal=9)
    df['macd_hist'] = macd['MACDh_12_26_9']
    df["volatility"] = df["price"].pct_change().rolling(window=20).std()
    df.dropna(inplace=True)

    # Normalizare și pregătire date
    features = ["price", "sma_10", "sma_50", "rsi_14", "macd_hist", "volatility"]
    data = df[features].values
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    lookback = 30
    for i in range(lookback, len(scaled_data)):
        X.append(scaled_data[i - lookback:i])
        y.append(scaled_data[i][0])
    X, y = np.array(X), np.array(y)

    if len(X) == 0:
        print(f"⚠️  Prea puține date pentru {symbol}")
        return

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        Dropout(0.3),
        LSTM(64),
        Dropout(0.3),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
    model.fit(X, y, epochs=50, batch_size=32, callbacks=[early_stop], verbose=0)

    model.save(MODELS_DIR / f"{symbol}_lstm_model.keras")
    joblib.dump(scaler, SCALERS_DIR / f"{symbol}_lstm_scaler.save")
    print(f"✅ Model salvat pentru {symbol}")

def main():
    for symbol in symbols:
        df = download_data_from_coingecko(symbol)
        if df is not None:
            train_model(symbol)
        print("⏳ Pauză 5 secunde...")
        time.sleep(5)

if __name__ == "__main__":
    main()
