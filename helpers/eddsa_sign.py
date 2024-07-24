import ed25519_utils
import secrets
import hashlib
import hmac


def _ed25519_serialize(p):
    if (p[0] & 1):
        return (p[1] + 2**255).to_bytes(32, byteorder="little")
    else:
        return (p[1]).to_bytes(32, byteorder="little")

def _hash_for_derive(pubkey, chaincode, child_num):
    ctx = hmac.new(chaincode, digestmod = hashlib.sha512)
    ctx.update(_ed25519_serialize(pubkey))
    ctx.update(b'\0')
    ctx.update(child_num.to_bytes(4, byteorder="big"))
    return ctx.digest()

def _derive_next_key_level(pubkey, privkey, chaincode, child_num):
    hash = _hash_for_derive(pubkey, chaincode, child_num)
    derived_chaincode = hash[32:]
    exp = int.from_bytes(hash[:32], byteorder="big")
    tmp_point = ed25519_utils.scalarmult(ed25519_utils.B, exp)
    derived_pubkey = ed25519_utils.edwards(pubkey, tmp_point)
    derived_privkey = (privkey + exp) % ed25519_utils.l
    return (derived_pubkey, derived_privkey, derived_chaincode)

def eddsa_sign(private_key, message):
    if type(message) == str:
        message = message.encode('utf-8')
    privkey = private_key
    if type(private_key) != int:
        privkey = int.from_bytes(private_key, byteorder='big')
    seed = secrets.token_bytes(32)
    sha = hashlib.sha512()
    sha.update(seed)
    sha.update(privkey.to_bytes(32, byteorder="little"))
    sha.update(message)
    nonce = int.from_bytes(sha.digest(), byteorder="little") % ed25519_utils.l
    R = ed25519_utils.scalarmult(ed25519_utils.B, nonce)
    A = ed25519_utils.scalarmult(ed25519_utils.B, privkey)
    sha = hashlib.sha512()
    sha.update(_ed25519_serialize(R))
    sha.update(_ed25519_serialize(A))
    sha.update(message)
    hram = int.from_bytes(sha.digest(), byteorder='little') % ed25519_utils.l
    s = (hram * privkey + nonce) % ed25519_utils.l
    return _ed25519_serialize(R) + s.to_bytes(32, byteorder="little")

def private_key_to_public_key(private_key):
    return _ed25519_serialize(ed25519_utils.scalarmult(ed25519_utils.B, private_key))