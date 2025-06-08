import os
import time
import pandas as pd
from pathlib import Path
from train_all_symbols import (
    train_model,
    download_data_from_coingecko,
    DATA_DIR,
    MODELS_DIR
)

# Simbolurile cu probleme (din testul tău anterior)
corrupt_symbols = [
    'dot_usd', 'doge', 'trx_usd', 'link', 'avax_usd', 'xlm_usd', 'matic_usd', 'atom',
    'near_usd', 'vet_usd', 'fil', 'algo', 'usdjpy', 'bch_usd', 'ltc_usd', 'matic', 'vet',
    'link_usd', 'doge_usd', 'shib_usd', 'eurusd', 'ltc', 'ftm_usd', 'tether', 'algo_usd',
    'xrp', 'dot', 'avax', 'eth_usd', 'gbpusd', 'atom_usd', 'icx', 'sol_usd', 'ada_usd',
    'xrp_usd', 'trx', 'btc_usd', 'icp'
]

def is_valid_csv(symbol: str) -> bool:
    csv_path = DATA_DIR / f"{symbol}.csv"
    if not csv_path.exists():
        return False
    try:
        df = pd.read_csv(csv_path)
        if 'price' not in df.columns:
            return False
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df.dropna(inplace=True)
        return len(df) >= 60  # minim 60 rânduri utile
    except Exception:
        return False

def main():
    for symbol in corrupt_symbols:
        model_path = MODELS_DIR / f"{symbol}_lstm_model.keras"
        csv_path = DATA_DIR / f"{symbol}.csv"

        # Șterge modelul corupt
        if model_path.exists():
            print(f"🗑 Șterg model corupt: {model_path.name}")
            model_path.unlink()

        # Verifică datele existente
        if not is_valid_csv(symbol):
            print(f"📉 Date lipsă sau invalide pentru {symbol}. Reîncarc de pe CoinGecko...")
            df = download_data_from_coingecko(symbol)
            if df is None or len(df) < 60:
                print(f"❌ Nu pot folosi {symbol}. Lipsesc datele valide.")
                continue
            print(f"✅ Date OK pentru {symbol}, continuăm cu antrenarea...")

        else:
            print(f"✅ Fișier CSV pentru {symbol} este valid.")

        # Antrenează modelul
        train_model(symbol)
        print("⏳ Pauză 5 secunde...")
        time.sleep(5)

    print("\n✅ Finalizat. Modelele valide au fost reantrenate.")

if __name__ == "__main__":
    main()

