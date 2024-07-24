import base58
import math
from typing import List, Union

import eddsa_sign

from solana.rpc.api import Client
from solders.pubkey import Pubkey as PublicKey
from solders.rpc.responses import SendTransactionResp
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solders.signature import Signature

from spl.token.instructions import transfer_checked, TransferCheckedParams

BIP_44_CONSTANT = 44
SOL_ASSET_NUM = 501
CHANGE = 0
ADDR_INDEX = 0
SOL_DECIMALS = 1e9

URL = "https://api.mainnet-beta.solana.com"


def build_unsigned_transaction(from_address: str, to_address: str, amount: int) -> bytes:
    from_address = PublicKey(address_to_public_key(from_address))
    to_address = PublicKey(address_to_public_key(to_address))
    blockhash = get_blockhash()

    txn = Transaction()
    txn.add(transfer(TransferParams(from_pubkey=from_address, to_pubkey=to_address, lamports=amount)))
    txn.recent_blockhash = blockhash
    # fee_payer and from_address should be same to build correct signed transaction in build_signed_transaction function
    txn.fee_payer = from_address
    return txn.serialize(verify_signatures=False)


def build_signing_payload(unsigned_txn: bytes) -> bytes:
    return Transaction.deserialize(unsigned_txn).serialize_message()


def sign_transaction_payload(private_key: bytes, payload: bytes) -> bytes:
    return eddsa_sign.eddsa_sign(private_key, payload)


def build_signed_transaction(unsigned_txn: bytes, signature: bytes) -> bytes:
    txn = Transaction.deserialize(unsigned_txn)
    txn.add_signature(txn.fee_payer, Signature(signature))
    return txn.serialize()


def broadcast_transaction(signed_txn: bytes) -> SendTransactionResp:
    solana_client = Client(URL)
    return solana_client.send_raw_transaction(signed_txn)


def withdraw(priv: bytes, pub: bytes, to_address: str, amount: int) -> SendTransactionResp:
    from_address = public_key_to_address(pub)
    unsigned_txn: bytes = build_unsigned_transaction(from_address, to_address, amount)
    signing_payload: bytes = build_signing_payload(unsigned_txn)
    signature: bytes = sign_transaction_payload(priv, signing_payload)
    signed_txn: bytes = build_signed_transaction(unsigned_txn, signature)
    response = broadcast_transaction(signed_txn)
    print(f'Transaction ID: {response.value}')
    return response


def withdraw_token(priv, transfer_params: TransferCheckedParams) -> SendTransactionResp:
    solana_client = Client(URL)
    blockhash = get_blockhash()
    txn = Transaction().add(transfer_checked(transfer_params))
    txn.recent_blockhash = blockhash
    txn.fee_payer = transfer_params.owner
    signature = Signature(eddsa_sign.eddsa_sign(priv, txn.serialize_message()))
    txn.add_signature(transfer_params.owner, signature)
    encoded_serialized_txn = txn.serialize()
    response = solana_client.send_raw_transaction(encoded_serialized_txn)
    print(f'Response is: {response}')
    return response


def get_blockhash():
    solana_client = Client(URL)
    response = solana_client.get_latest_blockhash()
    try:
        blockhash = response.value.blockhash
    except KeyError as err:
        print(f'falied to retrieve blockhash and fee, with error {err}')
        raise KeyError
    return blockhash


def get_balance(addr: Union[bytearray, bytes, int, str, List[int]]) -> str:
    solana_client = Client(URL)
    balance_response = solana_client.get_balance(PublicKey(addr))
    try:
        balance = balance_response['result']['value']
        return f'Balance is: {balance} lamports'
    except KeyError as e:
        print(f'falied to retrieve balance for {addr}, with error {e}')


def public_key_to_address(public_key: bytes) -> bytes:
    return base58.b58encode(public_key)


def address_to_public_key(address: bytes) -> bytes:
    return base58.b58decode(address)

def sol_to_lamports(amount: float) -> int:
    return int(math.floor(amount * SOL_DECIMALS))


public_key=bytes.fromhex("")
private_key=bytes.fromhex("")
to_address=""
amount=0 # lamports

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

response = broadcast_transaction(signed_txn)
print(f'txn_hash: {response.value}')
