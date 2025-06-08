from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import pandas_ta as ta
from tensorflow.keras.models import load_model
from pathlib import Path
from datetime import datetime, timedelta
import os
import traceback

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Dezactivează warningurile TensorFlow

app = FastAPI()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"

BUY_LINK = "https://dexscreener.com/solana/3uamdkk3c9t1eabzhbpg1fzakrf32zam3pgb6yvhvn7e"

class PredictionRequest(BaseModel):
    user_wallet: str
    symbol: str
    days: int

# Dicționar simplu pentru free predictions per wallet
user_free_predictions = {}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_index():
    return FileResponse(STATIC_DIR / "index.html")

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def predict(symbol: str, wallet: str, days: int):
    symbol = symbol.lower()
    wallet = wallet.lower()

    model_path = MODELS_DIR / f"{symbol}_lstm_model.keras"
    scaler_path = SCALERS_DIR / f"{symbol}_lstm_scaler.save"
    data_path = BASE_DIR / f"{symbol}.csv"

    if not model_path.exists() or not scaler_path.exists() or not data_path.exists():
        raise HTTPException(status_code=404, detail="Missing model, scaler or data files for symbol.")

    if wallet not in user_free_predictions:
        user_free_predictions[wallet] = 5

    if user_free_predictions[wallet] <= 0:
        return {
            "symbol": symbol,
            "days": days,
            "prediction": [],
            "free_predictions_left": 0,
            "message": "You've reached your free prediction limit. Upgrade for more predictions!",
            "buy_link": BUY_LINK
        }

    try:
        model = load_model(model_path)
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

        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df.dropna().reset_index(drop=True)

        df['sma_10'] = df['price'].rolling(window=10).mean()
        df['sma_50'] = df['price'].rolling(window=50).mean()
        df['rsi_14'] = compute_rsi(df['price'], 14)

        macd = ta.macd(df['price'], fast=12, slow=26, signal=9)
        df['macd_hist'] = macd['MACDh_12_26_9']

        df['volatility'] = df['price'].pct_change().rolling(window=20).std()
        df = df.dropna().reset_index(drop=True)

        features = ['price', 'sma_10', 'sma_50', 'rsi_14', 'macd_hist', 'volatility']
        data = df[features].values
        scaled_data = scaler.transform(data)

        lookback = 30
        if len(scaled_data) < lookback:
            return JSONResponse(status_code=400, content={"error": f"Not enough data. Need {lookback} days, but only have {len(scaled_data)}"})

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

            real_price = None
            df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
            real_row = df[df['timestamp_dt'] == pred_date]
            if not real_row.empty:
                real_price = float(real_row.iloc[0]['price'])

            predictions.append({
                "timestamp": pred_date,
                "Predicted_Price": round(predicted_price, 2),
                "Real_Price": round(real_price, 2) if real_price else None
            })

        user_free_predictions[wallet] -= 1

        return {
            "symbol": symbol,
            "days": days,
            "prediction": predictions,
            "free_predictions_left": user_free_predictions[wallet],
            "message": None,
            "buy_link": None if user_free_predictions[wallet] > 0 else BUY_LINK
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-lstm")
def predict_lstm_endpoint(request: PredictionRequest):
    try:
        result = predict(request.symbol, request.user_wallet, request.days)
        return JSONResponse(content={"prediction": result})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})