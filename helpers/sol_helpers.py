import base58
import math
from typing import List, Union

from helpers import eddsa_sign

from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.rpc.types import RPCResponse
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solders.signature import Signature

from spl.token.instructions import transfer_checked, TransferCheckedParams

BIP_44_CONSTANT = 44
SOL_ASSET_NUM = 501
CHANGE = 0
ADDR_INDEX = 0
SOL_DECIMALS = 1e9

URL = "https://api.mainnet-beta.solana.com"


def withdraw(priv, pub, to_address, amount) -> RPCResponse:
    solana_client = Client(URL)
    from_address = PublicKey(pub)
    receiver = PublicKey(address_to_public_key(to_address))
    blockhash = get_blockhash()
    txn = Transaction().add(transfer(TransferParams(from_pubkey=from_address, to_pubkey=receiver, lamports=amount)))
    txn.recent_blockhash = blockhash
    txn.fee_payer = from_address
    signature = Signature(eddsa_sign.eddsa_sign(priv, txn.serialize_message()))
    txn.add_signature(from_address, signature)
    encoded_serialized_txn = txn.serialize()
    response = solana_client.send_raw_transaction(encoded_serialized_txn)
    print(f'Response is: {response}')
    return response


def withdraw_token(priv, transfer_params: TransferCheckedParams) -> RPCResponse:
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
    response = solana_client.get_recent_blockhash()
    try:
        blockhash = response['result']['value']['blockhash']
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
