from fastapi import HTTPException
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import os
import traceback
import json

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"
DATA_DIR = BASE_DIR / "data"
PREDICTIONS_DIR = BASE_DIR / "predictions"
PURCHASED_FILE = BASE_DIR / "purchased.json"

PREDICTIONS_DIR.mkdir(exist_ok=True)
wallet_usage = defaultdict(lambda: {'used': 0, 'limit': 5})

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def save_predictions_to_csv(symbol: str, predictions: list):
    df = pd.DataFrame(predictions)
    df["timestamp"] = df["timestamp"].astype(str)
    df.to_csv(PREDICTIONS_DIR / f"{symbol}_predictions.csv", index=False)

def save_to_purchased(wallet: str, symbol: str, predictions: list):
    data = {}
    if PURCHASED_FILE.exists():
        with open(PURCHASED_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {}

    if wallet not in data:
        data[wallet] = {}
    data[wallet][symbol] = predictions

    with open(PURCHASED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def predict(symbol: str, wallet: str, days: int):
    symbol = symbol.lower()
    wallet = wallet.lower()

    model_path = MODELS_DIR / f"{symbol}_lstm_model.keras"
    scaler_path = SCALERS_DIR / f"{symbol}_lstm_scaler.save"
    data_path = DATA_DIR / f"{symbol}.csv"

    if not model_path.exists() or not scaler_path.exists() or not data_path.exists():
        raise HTTPException(status_code=404, detail="Missing model, scaler or data files for symbol.")

    try:
        model = load_model(model_path, compile=False)
        scaler = joblib.load(scaler_path)
        df = pd.read_csv(data_path)

        if 'price' not in df.columns:
            if 'close' in df.columns:
                df['price'] = df['close']
            elif 'Close' in df.columns:
                df['price'] = df['Close']
            else:
                raise HTTPException(status_code=400, detail="'price' column not found in data.")

        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.date_range(end=datetime.today(), periods=len(df)).astype(str)

        df['sma_10'] = df['price'].rolling(window=10).mean()
        df['sma_50'] = df['price'].rolling(window=50).mean()
        df['rsi_14'] = compute_rsi(df['price'], 14)
        df['macd_hist'] = df['price'].ewm(span=12).mean() - df['price'].ewm(span=26).mean()
        df['volatility'] = df['price'].pct_change().rolling(window=20).std()

        df = df.dropna().reset_index(drop=True)
        features = ["price", "sma_10", "sma_50", "rsi_14", "macd_hist", "volatility"]
        data = df[features].values
        scaled_data = scaler.transform(data)

        lookback = 30
        if len(scaled_data) < lookback:
            raise HTTPException(status_code=400, detail=f"Not enough data. Need {lookback} rows.")

        last_sequence = scaled_data[-lookback:]
        predictions = []

        for i in range(days):
            input_seq = np.reshape(last_sequence, (1, lookback, len(features)))
            pred_scaled = model.predict(input_seq, verbose=0)[0][0]

            last_day = last_sequence[-1].copy()
            last_day[0] = pred_scaled
            inv_scaled = scaler.inverse_transform([last_day])[0]
            predicted_price = inv_scaled[0]

            new_scaled_row = last_sequence[-1].copy()
            new_scaled_row[0] = pred_scaled
            last_sequence = np.vstack([last_sequence[1:], new_scaled_row])

            pred_date = (datetime.today() + timedelta(days=i+1)).strftime("%Y-%m-%d")
            predictions.append({"timestamp": pred_date, "Predicted_Price": round(predicted_price, 2)})

        if wallet != "anonymous_user":
            save_to_purchased(wallet, symbol, predictions)

        else:
            wallet_usage[wallet]['used'] += 1

        save_predictions_to_csv(symbol, predictions)

        return {
            "prediction": predictions,
            "wallet": wallet,
            "free_predictions_left": wallet_usage[wallet]['limit'] - wallet_usage[wallet]['used']
            if wallet == "anonymous_user" else 999
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
