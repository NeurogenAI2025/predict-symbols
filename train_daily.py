# train_daily.py
import os
import pandas as pd
from datetime import datetime
from train_all_symbols import download_data_from_coingecko, train_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SYMBOLS = [
    "algorand", "aptos", "arbitrum", "audius", "avalanche-2", "bitcoin", "cardano",
    "celo", "chainlink", "dogecoin", "dydx", "elrond-erd-2", "enjincoin", "eos", "ethereum",
    "fantom", "filecoin", "flux", "harmony", "helium", "injective-protocol", "iotex", "kadena",
    "litecoin", "loopring", "metis-token", "near", "nervos-network", "optimism", "osmosis",
    "polkadot", "radix", "ravencoin", "render-token", "ripple", "solana", "stellar",
    "terra-luna-2", "terra-luna", "tezos", "the-graph", "theta-token", "tron", "uniswap",
    "vechain", "waves", "wax", "zilliqa"
]

def needs_update(symbol):
    path = os.path.join(DATA_DIR, f"{symbol}.csv")
    if not os.path.exists(path):
        return True
    try:
        df = pd.read_csv(path)
        last_date = pd.to_datetime(df["timestamp"]).max().date()
        return last_date < datetime.today().date()
    except Exception:
        return True

def main():
    updated = 0
    for symbol in SYMBOLS:
        if needs_update(symbol):
            print(f"🔁 Actualizez: {symbol}")
            df = download_data_from_coingecko(symbol)
            if df is not None:
                train_model(symbol)
                updated += 1
    print(f"✅ Total simboluri actualizate: {updated}")

if __name__ == "__main__":
    main()
print(f"🏁 Script terminat la: {datetime.now()}")

