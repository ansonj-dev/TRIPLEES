const path = require('path');
const fs = require('fs');
const dotenv = require('dotenv');
const { ethers } = require('ethers');

const root = path.resolve(__dirname, '../../..');
dotenv.config({ path: path.join(root, '.env') });
const EXPECTED_CHAIN_ID = 10778;
const explorer = (process.env.X1_TESTNET_EXPLORER_URL || 'https://maculatus-scan.x1eco.com').replace(/\/$/, '');
const manifestPath = path.join(root, 'data', 'x1-testnet-deployment.json');

function settings() {
  const rpc = process.env.X1_TESTNET_RPC_URL;
  const configured = Number(process.env.X1_TESTNET_CHAIN_ID || EXPECTED_CHAIN_ID);
  if (!rpc) throw new Error('X1_TESTNET_RPC_URL is not configured in the ignored project .env.');
  if (configured !== EXPECTED_CHAIN_ID) throw new Error(`Configured chain ID ${configured} does not match verified Maculatus ID ${EXPECTED_CHAIN_ID}.`);
  return { rpc, chainId: configured };
}

async function providerForTestnet() {
  const conf = settings();
  const provider = new ethers.JsonRpcProvider(conf.rpc, conf.chainId, { staticNetwork: true });
  const network = await provider.getNetwork();
  if (Number(network.chainId) !== EXPECTED_CHAIN_ID) throw new Error(`RPC reports chain ID ${network.chainId}; expected ${EXPECTED_CHAIN_ID}. No transaction sent.`);
  const blockNumber = await provider.getBlockNumber();
  if (!Number.isSafeInteger(blockNumber) || blockNumber <= 0) throw new Error('RPC did not return a valid latest block. No transaction sent.');
  return { provider, blockNumber };
}

function accountFromEnv(name) {
  const key = (process.env[name] || '').trim();
  if (!key) throw new Error(`${name} is not configured. Private key values are never displayed.`);
  try { return new ethers.Wallet(key); }
  catch { throw new Error(`${name} is not a valid EVM private key. The key value was not displayed.`); }
}

async function describeWallet(provider, label, wallet) {
  const balance = await provider.getBalance(wallet.address);
  return { role: label, address: wallet.address, balanceWei: balance.toString(), balanceX1T: ethers.formatEther(balance) };
}

function artifact() {
  const artifactPath = path.join(root, 'services', 'contracts', 'artifacts', 'contracts', 'VericarbRegistry.sol', 'VericarbRegistry.json');
  if (!fs.existsSync(artifactPath)) throw new Error('Contract artifact missing. Run npm run compile first.');
  return JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
}

function deploymentManifest() {
  if (!fs.existsSync(manifestPath)) throw new Error('No X1 testnet deployment manifest exists yet.');
  return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
}

function saveManifest(manifest) {
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, { encoding: 'utf8', flag: 'w' });
}

function saveLocalContractAddress(address) {
  const envPath = path.join(root, '.env');
  const raw = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf8') : '';
  const line = `X1_REGISTRY_CONTRACT_ADDRESS=${address}`;
  const updated = /^\s*X1_REGISTRY_CONTRACT_ADDRESS=/m.test(raw)
    ? raw.replace(/^\s*X1_REGISTRY_CONTRACT_ADDRESS=.*$/m, line)
    : `${raw.replace(/\s*$/, '')}\n${line}\n`;
  fs.writeFileSync(envPath, updated, { encoding: 'utf8' });
}

module.exports = { EXPECTED_CHAIN_ID, explorer, manifestPath, settings, providerForTestnet, accountFromEnv, describeWallet, artifact, deploymentManifest, saveManifest, saveLocalContractAddress };
