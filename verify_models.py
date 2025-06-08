from tensorflow.keras.models import load_model
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"
valid_models = []
invalid_models = []

for model_file in MODELS_DIR.glob("*.keras"):
    symbol = model_file.stem.replace("_lstm_model", "")
    try:
        model = load_model(model_file, compile=False)
        valid_models.append(symbol)
    except Exception as e:
        invalid_models.append((symbol, str(e)))

print("\n✅ Modele funcționale:")
for s in sorted(valid_models):
    print("  -", s)

print("\n❌ Modele cu probleme:")
for s, err in invalid_models:
    print(f"  - {s} → {err[:60]}...")

# Poți salva într-un fișier dacă vrei:
with open("valid_symbols.txt", "w") as f:
    f.write("\n".join(valid_models))
