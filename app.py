from fastapi import FastAPI
from owner_secret_key import OWNER_WALLET

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend NRG funcțional"}

@app.get("/owner_wallet")
def owner_wallet():
    return {"owner_pubkey": str(OWNER_WALLET.public_key)}
