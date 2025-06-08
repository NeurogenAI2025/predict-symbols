import os
import json
from dotenv import load_dotenv

# Încarcă variabilele din fișierul .env
load_dotenv()

# Citește variabila ARY din .env și o convertește în listă de numere
try:
    ARY = json.loads(os.getenv("ARY"))
    if not isinstance(ARY, list):
        raise ValueError("ARY trebuie să fie o listă JSON validă.")
except Exception as e:
    raise Exception(f"❌ Eroare la citirea ARY din .env: {e}")

# Opțional: afișare pentru debug
print(f"✅ ARY încărcat cu succes: {ARY}")
print(f"🔢 Număr de elemente: {len(ARY)}")
