from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.system_program import TransferParams, transfer
from solana.rpc.types import TxOpts
import asyncio
import base64

app = FastAPI()

# Wallet owner - cheie privată în array (importă din fișierul tău owner_secret_key.py)
from owner_secret_key import OWNER_WALLET  # tip Keypair

SOLANA_RPC = "https://api.devnet.solana.com"
OWNER_PUBLIC_KEY = OWNER_WALLET.public_key

# Preț fix NRG în SOL pentru demo
NRG_PRICE_SOL = 0.01  # de ex 0.01 SOL per 1 NRG

class BuyRequest(BaseModel):
    buyer_pubkey: str  # Wallet-ul cumpărătorului
    amount_nrg: int    # Câte tokenuri NRG vrea să cumpere

@app.post("/buy_nrg")
async def buy_nrg(req: BuyRequest):
    buyer_pk = PublicKey(req.buyer_pubkey)
    amount_sol = req.amount_nrg * NRG_PRICE_SOL

    async with AsyncClient(SOLANA_RPC) as client:
        # Verifică dacă buyer a trimis suficient SOL la owner
        # Caută tranzacții recente de transfer SOL de la buyer la owner
        confirmed = False
        resp = await client.get_signatures_for_address(buyer_pk, limit=10)
        if not resp["result"]:
            raise HTTPException(status_code=400, detail="Nu s-au găsit tranzacții recente")

        # Verifică dacă vreo tranzacție e transfer SOL către owner cu suma necesară
        for sig_info in resp["result"]:
            tx_sig = sig_info["signature"]
            tx_resp = await client.get_transaction(tx_sig)
            if not tx_resp["result"]:
                continue
            tx = tx_resp["result"]["transaction"]
            message = tx["message"]
            for instr in message["instructions"]:
                # Aici se poate analiza dacă instrucțiunea e transfer SOL la owner
                # (Pentru demo simplificat, să presupunem că buyer confirmă și continuăm)
                confirmed = True
                break
            if confirmed:
                break
        if not confirmed:
            raise HTTPException(status_code=400, detail="Nu s-a confirmat plata")

        # Trimite tokenii NRG către buyer (simplificat: trimitere SOL înapoi ca demo)
        # În realitate, folosește program token SPL să trimiți token NRG
        tx = Transaction()
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=OWNER_PUBLIC_KEY,
                to_pubkey=buyer_pk,
                lamports=int(amount_sol * 1_000_000_000),  # convert SOL to lamports
            )
        )
        tx.add(transfer_instruction)
        try:
            res = await client.send_transaction(tx, OWNER_WALLET, opts=TxOpts(skip_confirmation=False))
            return {"success": True, "tx_signature": res["result"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
