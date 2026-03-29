/**
 * BTC Address Generator (Prompt-based)
 * - Accepts xprv, basePath, startIndex, count
 * - Generates P2SH-P2WPKH addresses
 */

const readline = require('readline');
const bitcoin = require('bitcoinjs-lib');
const ecc = require('tiny-secp256k1');
const { default: BIP32Factory } = require('bip32');

const bip32 = BIP32Factory(ecc);

// CLI setup
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

function ask(question) {
  return new Promise((resolve) => rl.question(question, resolve));
}

// ============================================================
// MAIN
// ============================================================
async function main() {
  console.log("=".repeat(60));
  console.log("BTC ADDRESS GENERATOR (PROMPT MODE)");
  console.log("=".repeat(60));

  const xprv = (await ask("Enter xprv/tprv: ")).trim();
  const basePath = (await ask("Enter base derivation path (e.g. m/49/1/0/1153/0/0): ")).trim();
  const startIndex = parseInt(await ask("Enter start index: "), 10);
  const count = parseInt(await ask("Enter number of addresses to generate: "), 10);

  // Basic validation
  if (!xprv || !basePath || isNaN(startIndex) || isNaN(count)) {
    console.log("❌ Invalid input. Please check values.");
    rl.close();
    return;
  }

  // Auto-detect network
  const network = xprv.startsWith('tprv')
    ? bitcoin.networks.testnet
    : bitcoin.networks.bitcoin;

  console.log("\nNetwork:", xprv.startsWith('tprv') ? "Testnet" : "Mainnet");

  let root;
  try {
    root = bip32.fromBase58(xprv, network);
  } catch (e) {
    console.log("❌ Invalid xprv/tprv");
    rl.close();
    return;
  }

  console.log("\n--- GENERATED ADDRESSES ---");

  for (let i = startIndex; i < startIndex + count; i++) {
    try {
      const path = `${basePath}/${i}`;
      const child = root.derivePath(path);

      const { address } = bitcoin.payments.p2sh({
        redeem: bitcoin.payments.p2wpkh({
          pubkey: child.publicKey,
          network,
        }),
        network,
      });

      console.log("\n====================================");
      console.log("Index:", i);
      console.log("Path:", path);
      console.log("Address:", address);
      console.log("Public Key:", child.publicKey.toString('hex'));
      console.log("Private Key (WIF):", child.toWIF());

    } catch (err) {
      console.log(`❌ Error at index ${i}:`, err.message);
    }
  }

  rl.close();
}

main().catch(console.error);