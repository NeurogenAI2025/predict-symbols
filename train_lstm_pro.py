import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import pandas_ta as ta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"

# Creează folderele dacă nu există
MODELS_DIR.mkdir(parents=True, exist_ok=True)
SCALERS_DIR.mkdir(parents=True, exist_ok=True)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def prepare_features(df):
    # Asigură că 'close' este numeric
    df['price'] = pd.to_numeric(df['close'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.drop(columns=['col6', 'col7'], errors='ignore')
    df = df.dropna(subset=['price'])

    # Indicatori tehnici
    df['sma_10'] = df['price'].rolling(window=10).mean()
    df['sma_50'] = df['price'].rolling(window=50).mean()
    df['rsi_14'] = compute_rsi(df['price'], 14)

    macd = ta.macd(df['price'])
    df['macd'] = macd['MACD_12_26_9']
    df['macd_signal'] = macd['MACDs_12_26_9']
    df['macd_hist'] = macd['MACDh_12_26_9']

    df['volatility'] = df['price'].pct_change().rolling(window=20).std()
    df = df.dropna().reset_index(drop=True)

    features = ['price', 'sma_10', 'sma_50', 'rsi_14', 'macd_hist', 'volatility']
    return df, features

def create_sequences(data, lookback=30):
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i])
        y.append(data[i][0])  # țintim price (prima coloană)
    return np.array(X), np.array(y)

def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(50))
    model.add(Dropout(0.2))
    model.add(Dense(1))  # Preț viitor
    model.compile(optimizer='adam', loss='mse')
    return model

def train_symbol(symbol):
    print(f"Starting training for {symbol}...")

    data_path = DATA_DIR / f"{symbol}.csv"
    if not data_path.exists():
        print(f"Data file for {symbol} not found: {data_path}")
        return

    df = pd.read_csv(data_path)
    df, features = prepare_features(df)

    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(df[features])

    lookback = 30
    X, y = create_sequences(scaled_features, lookback=lookback)

    model = build_model(input_shape=(X.shape[1], X.shape[2]))
    model.fit(X, y, epochs=15, batch_size=32, verbose=2)

    # Salvează modelul și scalerul
    model_path = MODELS_DIR / f"{symbol}_lstm_model.keras"
    scaler_path = SCALERS_DIR / f"{symbol}_lstm_scaler.save"

    model.save(model_path)
    # Salvăm scalerul ca fișier joblib
    import joblib
    joblib.dump(scaler, scaler_path)

    print(f"Finished training for {symbol} and saved model + scaler.")

if __name__ == "__main__":
    # Lista simbolurilor pentru care antrenăm
    symbols = [
        'usdjpy', 'spell', 'chz', 'near_usd', '1inch', 'bnt', 'bch_usd', 'sushi', 'vet_usd',
        'theta', 'iota', 'solana', 'ada-usd', 'dot_usd', 'vet', 'sol', 'shib', 'okb', 'enj',
        'fil', 'nano', 'uma', 'lrc', 'ftt', 'ust', 'btc', 'poly', 'ont', 'rvn', 'celo', 'matic',
        'bch', 'link', 'srm', 'luna', 'shib_usd', 'lpt', 'bat', 'atom', 'snx', 'chsb', 'dash',
        'flow', 'zec', 'xlm', 'xtz', 'hbar', 'xrp', 'tfuel', 'zrx', 'stx', 'ar', 'apt', 'doge_usd',
        'sand', 'qtum', 'avax', 'waves', 'icp', 'gala', 'arb', 'sol_usd', 'mkr', 'btt', 'twt',
        'gbpusd', 'ltc', 'doge', 'bal', 'algo_usd', 'zil', 'cel', 'ada', 'avax_usd', 'eurusd',
        'eos', 'xlm_usd', 'dcr', 'ftm', 'dgb', 'mdx', 'eth', 'btc_usd', 'husd', 'xrp_usd', 'cvc',
        'crv', 'link_usd', 'glm', 'trx_usd', 'imx', 'axs', 'cake', 'iost', 'kava', 'cro', 'uni',
        'xem', 'nexo', 'tether', 'comp', 'rsr', 'gold', 'ripple', 'rune', 'ltc_usd', 'ocean',
        'ren', 'mana', 'matic_usd', 'aave', 'grt', 'eth_usd', 'trx', 'hnt', 'atom_usd', 'algo',
        'ftm_usd', 'icx', 'yfi', 'one', 'knc', 'near', 'ada_usd', 'ksm', 'dot', 'ankr'
    ]

    for symbol in symbols:
        try:
            train_symbol(symbol)
        except Exception as e:
            print(f"Error training {symbol}: {e}")
