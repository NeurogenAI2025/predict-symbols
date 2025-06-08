import os
import json

from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from solana.rpc.api import Client
from solana.publickey import PublicKey
from pydantic import BaseModel
from tensorflow.keras.models import load_model
from predict_lstm_pro import predict as get_prediction_for_symbol


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
NRG_TOKEN_MINT = PublicKey("CBTuVEM1Z5z5ddfQVEGAAHPN1ckj6j97zHvKtrc78suj")

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
SCALERS_DIR = BASE_DIR / "scalers"
DATA_DIR = BASE_DIR / "data"
STORAGE_FILE = BASE_DIR / "usage.json"

PREDICTION_LIMIT = 5

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

solana_client = Client(SOLANA_RPC)

class PredictRequest(BaseModel):
    wallet: str
    symbol: str
    days: int

class ResetUsageRequest(BaseModel):
    wallet: str
    newLimit: int

def get_available_symbols():
    symbols = []
    for model_file in MODELS_DIR.glob("*_lstm_model.keras"):
        try:
            symbol = model_file.stem.replace("_lstm_model", "")
            symbols.append(symbol)
        except Exception as e:
            print(f"Error processing model file {model_file}: {e}")
            continue
    return sorted(symbols)

def load_usage():
    if not STORAGE_FILE.exists():
        return {}
    try:
        with STORAGE_FILE.open("r") as f:
            data = json.load(f)
        for key, val in data.items():
            if isinstance(val, int):
                data[key] = {"count": val, "limit": PREDICTION_LIMIT}
        return data
    except Exception:
        return {}

def save_usage(data):
    with STORAGE_FILE.open("w") as f:
        json.dump(data, f, indent=2)

def increment_usage(user_id):
    data = load_usage()
    if user_id not in data:
        data[user_id] = {"count": 0, "limit": PREDICTION_LIMIT}
    data[user_id]["count"] += 1
    save_usage(data)
    return max(0, data[user_id]["limit"] - data[user_id]["count"])

def get_remaining_predictions(user_id):
    data = load_usage()
    if user_id not in data:
        return PREDICTION_LIMIT
    return max(0, data[user_id]["limit"] - data[user_id]["count"])

def get_prediction_quota(user_id):
    data = load_usage()
    if user_id not in data:
        return {"used": 0, "remaining": PREDICTION_LIMIT}
    return {
        "used": data[user_id]["count"],
        "remaining": max(0, data[user_id]["limit"] - data[user_id]["count"]),
    }

def check_nrg_payment(wallet_address: str) -> bool:
    try:
        pubkey = PublicKey(wallet_address)
        transactions = solana_client.get_signatures_for_address(pubkey).get("result", [])
        for tx in transactions:
            sig = tx.get("signature")
            if not sig:
                continue
            tx_data = solana_client.get_transaction(sig).get("result")
            if not tx_data:
                continue
            meta = tx_data.get("meta", {})
            post_token_balances = meta.get("postTokenBalances", [])
            for balance in post_token_balances:
                if balance.get("mint") == str(NRG_TOKEN_MINT) and balance.get("owner") == wallet_address:
                    return True
        return False
    except Exception as e:
        print(f"Error checking payment: {e}")
        return False

@app.get("/")
def root():
    return {"status": "Backend NRG FastAPI online"}

@app.get("/symbols")
def get_symbols():
    try:
        symbols = get_available_symbols()
        if not symbols:
            raise HTTPException(status_code=404, detail="No symbols found.")
        return {"symbols": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-lstm")
async def predict_endpoint(request: PredictRequest):
    user_id = request.wallet if request.wallet != "anonymous_user" else "anon"

    if not request.symbol or not request.days:
        raise HTTPException(status_code=400, detail="Missing symbol or days")

    if request.wallet != "anonymous_user" and check_nrg_payment(request.wallet):
        try:
            result = get_prediction_for_symbol(request.symbol, request.wallet, request.days)
            return {"prediction": result, "free_predictions_left": 999, "paid": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    remaining = get_remaining_predictions(user_id)
    if remaining <= 0:
        return {"message": "Free predictions exhausted", "free_predictions_left": 0, "paid": False}

    try:
        result = get_prediction_for_symbol(request.symbol, request.wallet, request.days)
        free_left = increment_usage(user_id)
        quota = get_prediction_quota(user_id)
        return {
            "prediction": result,
            "free_predictions_left": free_left,
            "quota": quota,
            "paid": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/reset-usage")
def reset_usage_endpoint(req: ResetUsageRequest):
    data = load_usage()
    if req.wallet:
        data[req.wallet] = {"count": 0, "limit": req.newLimit}
        save_usage(data)
        return {"message": "Usage reset"}
    raise HTTPException(status_code=400, detail="Missing wallet")
