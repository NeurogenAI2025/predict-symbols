from solana.keypair import Keypair

# array-ul cu cheia privată (32 sau 64 bytes)
secret_key_array = [62,0,88,59,116,171,38,148,192,23,144,163,103,48,193,96,184,49,202,13,174,96,158,173,34,227,217,215,235,64,147,171,44,213,237,100,245,121,23,58,68,250,75,142,127,87,1]

# convertim lista în bytes
secret_key_bytes = bytes(secret_key_array)

# cream Keypair-ul walletului
OWNER_WALLET = Keypair.from_secret_key(secret_key_bytes)

print("Adresa publică a walletului owner este:", OWNER_WALLET.public_key)

