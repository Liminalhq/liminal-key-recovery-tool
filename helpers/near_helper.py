import hashlib
from typing import Union
import base58
from near_api.transactions import (
    Transaction, PublicKey, create_transfer_action, Signature, SignedTransaction, tx_schema
)
from near_api.providers import JsonProvider
from near_api.serializer import BinarySerializer
import eddsa_sign

rpc_url="https://rpc.mainnet.near.org"


def build_unsigned_transaction(from_address: str, to_address: str, amount: int) -> Transaction:
    account_id = from_address
    public_key = bytes.fromhex(account_id)
    public_key_b58 = base58.b58encode(public_key).decode()

    provider = JsonProvider(rpc_url)
    nonce = provider.get_access_key(account_id, public_key_b58)["nonce"]+1
    block_hash = provider.get_status()['sync_info']['latest_block_hash']
    block_hash = base58.b58decode(block_hash.encode('utf8'))

    tx = Transaction()
    tx.signerId = account_id
    tx.publicKey = PublicKey()
    tx.publicKey.keyType = 0
    tx.publicKey.data = public_key
    tx.nonce = nonce
    tx.receiverId = to_address
    tx.actions = [create_transfer_action(amount)]
    tx.blockHash = block_hash

    return tx


def build_signing_payload(unsigned_txn: Union[Transaction, bytes]) -> bytes:
    if isinstance(unsigned_txn, Transaction):
        unsigned_txn = BinarySerializer(tx_schema).serialize(unsigned_txn)

    return hashlib.sha256(unsigned_txn).digest()


def sign_transaction_payload(private_key: bytes, payload: bytes) -> bytes:
    return eddsa_sign.eddsa_sign(private_key, payload)


def build_signed_transaction(unsigned_txn: Transaction, signature: bytes) -> bytes:
    signed_tx = SignedTransaction()
    signed_tx.transaction = unsigned_txn
    signed_tx.signature = Signature()
    signed_tx.signature.keyType = 0
    signed_tx.signature.data = signature

    return BinarySerializer(tx_schema).serialize(signed_tx)


def broadcast_transaction(signed_txn: bytes) -> dict:
    provider = JsonProvider(rpc_url)
    return provider.send_tx(signed_txn)


def withdraw(public_key: bytes, private_key: bytes, to_address: str, amount: float):
    unsigned_txn: Transaction = build_unsigned_transaction(public_key.hex(), to_address, amount)
    signing_payload: bytes = build_signing_payload(unsigned_txn)
    signature: bytes = sign_transaction_payload(private_key, signing_payload)
    signed_txn: bytes = build_signed_transaction(unsigned_txn, signature)
    tx_id = broadcast_transaction(signed_txn)
    print(f'Transaction ID: {tx_id}')
    return tx_id


public_key=bytes.fromhex("")
private_key=bytes.fromhex("")
to_address=""
amount=0 # yocto

# withdraw(public_key, private_key, to_address, amount)

from_address = public_key.hex()
print("sending from", from_address)

# note: step 1 to 4 need to be done in the same session as `unsigned_txn` from `step 1` is an object that needs to be passed as it is in `step 4`

# step 1
unsigned_txn: Transaction = build_unsigned_transaction(from_address, to_address, amount)
print("unsigned_txn", unsigned_txn)

# step 2
signing_payload: bytes = build_signing_payload(unsigned_txn)
print("signing_payload", signing_payload.hex())

# step 3
signature: bytes = sign_transaction_payload(private_key, signing_payload)
print("signature", signature.hex())

# step 4
signed_txn: bytes = build_signed_transaction(unsigned_txn, signature)
print("signed_txn", signed_txn.hex())

tx_id = broadcast_transaction(signed_txn)
print(f'txn_hash: {tx_id}')
