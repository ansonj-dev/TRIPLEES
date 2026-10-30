const { providerForTestnet, accountFromEnv, describeWallet, explorer, EXPECTED_CHAIN_ID } = require('./chain-utils');

async function main() {
  const { provider, blockNumber } = await providerForTestnet();
  const checks = [];
  for (const [label, variable] of [['deployer', 'X1_DEPLOYER_PRIVATE_KEY'], ['registrar', 'X1_REGISTRAR_PRIVATE_KEY'], ['reviewer', 'X1_REVIEWER_PRIVATE_KEY']]) {
    if (!process.env[variable]) { checks.push({ role: label, configured: false }); continue; }
    try { checks.push({ configured: true, ...(await describeWallet(provider, label, accountFromEnv(variable))) }); }
    catch (error) { checks.push({ role: label, configured: true, valid: false, error: error.message }); }
  }
  console.log(JSON.stringify({ network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID, rpcConnected: true, latestBlock: blockNumber, nativeCurrency: process.env.X1_TESTNET_NATIVE_CURRENCY || 'X1T', explorer, wallets: checks }, null, 2));
  if (checks.some((wallet) => wallet.configured && wallet.valid === false)) process.exitCode = 1;
}

main().catch((error) => { console.error(`Network check failed: ${error.message}`); process.exitCode = 1; });
