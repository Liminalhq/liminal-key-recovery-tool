/**
 * Solana Signer (Prompt-based)
 * - Accepts raw scalar + public key from user input
 * - Verifies keys
 * - Tests signature
 * - DOES NOT send transaction (sample code commented)
 */

const readline = require("readline");
const { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } = require("@solana/web3.js");
const ed = require("@noble/ed25519");
const { sha512 } = require("@noble/hashes/sha2.js");

// Setup sha512
ed.hashes.sha512 = (msg) => sha512(msg);

// Helper
const sha512Sync = (...m) => {
  const h = sha512.create();
  m.forEach(msg => h.update(msg));
  return h.digest();
};

// CLI prompt setup
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question) {
  return new Promise((resolve) => rl.question(question, resolve));
}

// ============================================================
// SIGN FUNCTION (same as before)
// ============================================================
function signWithRawScalar(message, scalarLittleEndian, publicKeyBytes) {
  const nonceHash = sha512Sync(scalarLittleEndian, message);

  const L = BigInt("7237005577332262213973186563042994240857116359379907606001950938285454250989");

  let nonceInt = BigInt(0);
  for (let i = 0; i < 64; i++) {
    nonceInt += BigInt(nonceHash[i]) << BigInt(8 * i);
  }
  nonceInt = nonceInt % L;

  const R = ed.Point.BASE.multiply(nonceInt);
  const Rbytes = R.toBytes();

  let scalarInt = BigInt(0);
  for (let i = 0; i < 32; i++) {
    scalarInt += BigInt(scalarLittleEndian[i]) << BigInt(8 * i);
  }

  const kHash = sha512Sync(Rbytes, publicKeyBytes, message);
  let kInt = BigInt(0);
  for (let i = 0; i < 64; i++) {
    kInt += BigInt(kHash[i]) << BigInt(8 * i);
  }
  kInt = kInt % L;

  const S = (nonceInt + kInt * scalarInt) % L;

  const Sbytes = new Uint8Array(32);
  let sTemp = S;
  for (let i = 0; i < 32; i++) {
    Sbytes[i] = Number(sTemp & BigInt(0xff));
    sTemp >>= BigInt(8);
  }

  const signature = new Uint8Array(64);
  signature.set(Rbytes, 0);
  signature.set(Sbytes, 32);

  return signature;
}

// ============================================================
// MAIN
// ============================================================
async function main() {
  console.log("=".repeat(60));
  console.log("SOLANA RECOVERY SIGNER (PROMPT MODE)");
  console.log("=".repeat(60));

  const privateHex = await ask("Enter DERIVED_PRIVATE_KEY_HEX: ");
  const publicHex = await ask("Enter DERIVED_PUBLIC_KEY_HEX: ");

  const scalarBigEndian = Buffer.from(privateHex.trim(), "hex");
  const scalarLittleEndian = Buffer.from(scalarBigEndian).reverse();

  const publicKeyBytes = Buffer.from(publicHex.trim(), "hex");
  const walletAddress = new PublicKey(publicKeyBytes);

  console.log("\n--- OUTPUT ---");
  console.log("Wallet Address:", walletAddress.toBase58());
  console.log("Public Key Hex:", publicHex);

  // ============================================================
  // KEY VERIFICATION
  // ============================================================
  const scalarBigInt = BigInt("0x" + scalarLittleEndian.toString("hex").match(/../g).reverse().join(""));
  const computedPoint = ed.Point.BASE.multiply(scalarBigInt);
  const computedPubBytes = computedPoint.toBytes();

  const keyMatch = Buffer.from(computedPubBytes).equals(publicKeyBytes);

  console.log("Key Verification:", keyMatch ? "✅ Passed" : "❌ Failed");

  if (!keyMatch) {
    rl.close();
    return;
  }

  // ============================================================
  // TEST SIGNATURE
  // ============================================================
  const testMessage = Buffer.from("Hello Solana from Liminal!");
  const testSig = signWithRawScalar(testMessage, scalarLittleEndian, publicKeyBytes);

  const isValid = await ed.verify(testSig, testMessage, publicKeyBytes);

  console.log("Test Signature Verification:", isValid ? "✅ Passed" : "❌ Failed");

  // ============================================================
  // SAMPLE TRANSACTION CODE (COMMENTED OUT)
  // ============================================================

  /*
  const RPC_URL = "https://api.devnet.solana.com";
  const connection = new Connection(RPC_URL, "confirmed");

  const balance = await connection.getBalance(walletAddress);
  console.log("Balance:", balance / LAMPORTS_PER_SOL, "SOL");

  const RECIPIENT = "REPLACE_WITH_ADDRESS";
  const AMOUNT_SOL = 0.001;

  const recipient = new PublicKey(RECIPIENT);

  const transaction = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey: walletAddress,
      toPubkey: recipient,
      lamports: Math.round(AMOUNT_SOL * LAMPORTS_PER_SOL),
    })
  );

  const { blockhash } = await connection.getLatestBlockhash();
  transaction.recentBlockhash = blockhash;
  transaction.feePayer = walletAddress;

  const message = transaction.serializeMessage();
  const signature = signWithRawScalar(message, scalarLittleEndian, publicKeyBytes);

  transaction.addSignature(walletAddress, Buffer.from(signature));

  const rawTx = transaction.serialize();
  const txId = await connection.sendRawTransaction(rawTx);

  console.log("Transaction sent:", txId);
  */

  rl.close();
}

main().catch(console.error);