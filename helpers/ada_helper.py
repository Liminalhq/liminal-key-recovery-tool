from pycardano import TransactionOutput, VerificationKeyWitness, Transaction, TransactionBuilder, VerificationKey, TransactionBody, Network, blake2b, TRANSACTION_HASH_SIZE, RawEncoder
from pycardano.backend.blockfrost import BlockFrostChainContext
import eddsa_sign

blockfrost_api_key=""


def build_unsigned_transaction(from_address: str, to_address: str, amount: int) -> bytes:
    ctx = BlockFrostChainContext(project_id=blockfrost_api_key, network=Network.MAINNET)
    utxos = ctx.utxos(from_address)
    builder = TransactionBuilder(ctx)
    for utxo in utxos:
        builder.add_input(utxo)
    builder.add_output(TransactionOutput.from_primitive([to_address, amount]))
    return builder.build(from_address, merge_change=True).to_cbor()


def build_signing_payload(unsigned_txn: bytes) -> bytes:
    return blake2b(unsigned_txn, TRANSACTION_HASH_SIZE, encoder=RawEncoder)


def sign_transaction_payload(private_key: bytes, payload: bytes) -> bytes:  
    return eddsa_sign.eddsa_sign(private_key, payload)


def build_signed_transaction(unsigned_txn: bytes, signature: bytes, public_key: bytes) -> bytes:
    ctx = BlockFrostChainContext(project_id=blockfrost_api_key, network=Network.MAINNET)
    witness_set = TransactionBuilder(ctx).build_witness_set()
    witness_set.vkey_witnesses = []
    witness_set.vkey_witnesses.append(
        VerificationKeyWitness(VerificationKey(public_key, "PaymentVerificationKeyShelley_ed25519", "Payment Verification Key"), signature)
    )
    return Transaction(TransactionBody.from_cbor(unsigned_txn), witness_set, valid=True).to_cbor()


def broadcast_transaction(signed_txn: bytes) -> str:
    return BlockFrostChainContext(project_id=blockfrost_api_key, network=Network.MAINNET).submit_tx(signed_txn)


def withdraw(public_key: bytes, private_key: bytes, from_address: str, to_address: str, amount: int):
    unsigned_txn: bytes = build_unsigned_transaction(from_address, to_address, amount)
    signing_payload: bytes = build_signing_payload(unsigned_txn)
    signature: bytes = sign_transaction_payload(private_key, signing_payload)
    signed_txn: bytes = build_signed_transaction(unsigned_txn, signature, public_key)
    tx_id = broadcast_transaction(signed_txn)
    print(f'Transaction ID: {tx_id}')
    return tx_id


def parse_unsgined_tx_body(cbor_tx_body_hex: str):
    tx_body = TransactionBody.from_cbor(cbor_tx_body_hex)
    print("unsigned tx body", tx_body)


def parse_signed_tx(cbor_tx_hex: str):
    tx = Transaction.from_cbor(cbor_tx_hex)
    print("signed tx", tx)
    

public_key=bytes.fromhex("")
private_key=bytes.fromhex("")
from_address=""
to_address=""
amount=0 # lovelace

# withdraw(public_key, private_key, from_address, to_address, amount)

unsigned_txn = build_unsigned_transaction(from_address, to_address, amount)
print("unsigned_txn", unsigned_txn.hex())

signing_payload = build_signing_payload(unsigned_txn)
print("signing_payload", signing_payload.hex())

signature = sign_transaction_payload(private_key, signing_payload)
print("signature", signature.hex())

signed_txn = build_signed_transaction(unsigned_txn, signature, public_key)
print("signed_txn", signed_txn.hex())

tx_id = broadcast_transaction(signed_txn)
print(f'txn_hash: {tx_id}')
