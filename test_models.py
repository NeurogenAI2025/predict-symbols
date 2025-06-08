from tensorflow.keras.models import load_model
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"
errors = []

for model_file in MODELS_DIR.glob("*.keras"):
    try:
        print(f"✅ Verific {model_file.name}...")
        model = load_model(model_file, compile=False)
    except Exception as e:
        print(f"❌ Eroare la {model_file.name}: {e}")
        errors.append(model_file.name)

if not errors:
    print("✅ Toate modelele sunt valide.")
else:
    print("❌ Modelele cu probleme:", errors)
