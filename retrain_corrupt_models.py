import os
from pathlib import Path
from train_all_symbols import train_model

MODELS_DIR = Path(__file__).parent / "models"

# Modelele corupte detectate
corrupt_models = [
    'dot_usd', 'doge', 'trx_usd', 'link', 'avax_usd', 'xlm_usd', 'matic_usd', 'atom',
    'near_usd', 'vet_usd', 'fil', 'algo', 'usdjpy', 'bch_usd', 'ltc_usd', 'matic', 'vet',
    'link_usd', 'doge_usd', 'shib_usd', 'eurusd', 'ltc', 'ftm_usd', 'tether', 'algo_usd',
    'xrp', 'dot', 'avax', 'eth_usd', 'gbpusd', 'atom_usd', 'icx', 'sol_usd', 'ada_usd',
    'xrp_usd', 'trx', 'btc_usd', 'icp'
]

for symbol in corrupt_models:
    model_path = MODELS_DIR / f"{symbol}_lstm_model.keras"
    if model_path.exists():
        print(f"🗑 Șterg model corupt: {model_path.name}")
        model_path.unlink()

    print(f"🔁 Re-antrenez modelul pentru: {symbol}")
    train_model(symbol)

print("✅ Modelele corupte au fost reantrenate.")
