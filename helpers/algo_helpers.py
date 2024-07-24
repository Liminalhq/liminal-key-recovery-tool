from algosdk.v2client import algod
from algosdk import encoding
from algosdk import constants
from algosdk.future.transaction import PaymentTxn, SignedTransaction
import base64
import eddsa_sign

BIP_44_CONSTANT = 44
ALGO_ASSET_NUM = 283
CHANGE = 0
ADDR_INDEX = 0

# change the following settings to your Algorand node's URL and its token
# these settings work with the Algorand Sandbox: https://github.com/algorand/sandbox
algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_client = algod.AlgodClient(algod_token, algod_address)


def build_unsigned_transaction(from_address: str, to_address: str, amount: int) -> bytes:
    params = algod_client.suggested_params()
    txn = PaymentTxn(from_address, params, to_address, amount)
    return base64.b64decode(encoding.msgpack_encode(txn))


def build_signing_payload(unsigned_txn: bytes) -> bytes:
    return constants.txid_prefix + unsigned_txn


def sign_transaction_payload(private_key: bytes, payload: bytes) -> bytes:
    return eddsa_sign.eddsa_sign(private_key, payload)


def build_signed_transaction(unsigned_txn: bytes, signature: bytes) -> bytes:
    txn = encoding.msgpack_decode(base64.b64encode(unsigned_txn))
    return base64.b64decode(encoding.msgpack_encode(SignedTransaction(txn, base64.b64encode(signature).decode())))


def broadcast_transaction(signed_txn: bytes) -> str:
    txn = encoding.msgpack_decode(base64.b64encode(signed_txn))
    return algod_client.send_transaction(txn)


def withdraw(priv: bytes, pub: bytes, to_address: str, amount) -> str:
    from_address = public_key_to_address(pub)
    unsigned_txn: bytes = build_unsigned_transaction(from_address, to_address, amount)
    signing_payload: bytes = build_signing_payload(unsigned_txn)
    signature: bytes = sign_transaction_payload(priv, signing_payload)
    signed_txn: bytes = build_signed_transaction(unsigned_txn, signature)
    tx_id = broadcast_transaction(signed_txn)
    print(f'Transaction ID: {tx_id}')
    return tx_id


def getBalance(addr):
    account_info = algod_client.account_info(addr)
    if account_info is None: return 0
    return account_info.get('amount') / 1e6

def public_key_to_address(public_key: bytes) -> str:
    return encoding.encode_address(public_key)


public_key = bytes.fromhex("")
private_key = bytes.fromhex("")
to_address = ""
amount = 0 # microalgo

# withdraw(private_key, public_key, to_address, amount)

from_address = public_key_to_address(public_key)
print("sending from", from_address)

unsigned_txn: bytes = build_unsigned_transaction(from_address, to_address, amount)
print("unsigned_txn", unsigned_txn.hex())

signing_payload: bytes = build_signing_payload(unsigned_txn)
print("signing_payload", signing_payload.hex())

signature: bytes = sign_transaction_payload(private_key, signing_payload)
print("signature", signature.hex())

signed_txn: bytes = build_signed_transaction(unsigned_txn, signature)
print("signed_txn", signed_txn.hex())

tx_id = broadcast_transaction(signed_txn)
print(f'txn_hash: {tx_id}')
