const { ethers } = require('ethers');
const { providerForTestnet, accountFromEnv, describeWallet, artifact, deploymentManifest, saveManifest, explorer, EXPECTED_CHAIN_ID } = require('./chain-utils');

async function main() {
  const { provider, blockNumber } = await providerForTestnet();
  const manifest = deploymentManifest();
  if (manifest.chainId !== EXPECTED_CHAIN_ID) throw new Error('Deployment manifest is for a different chain.');
  const deployer = accountFromEnv('X1_DEPLOYER_PRIVATE_KEY');
  const registrar = accountFromEnv('X1_REGISTRAR_PRIVATE_KEY');
  const reviewer = accountFromEnv('X1_REVIEWER_PRIVATE_KEY');
  const wallets = [deployer, registrar, reviewer];
  if (new Set(wallets.map((wallet) => wallet.address.toLowerCase())).size !== 3) throw new Error('Deployer, registrar, and reviewer must be three distinct wallets.');
  const contractArtifact = artifact();
  const contract = new ethers.Contract(manifest.contractAddress, contractArtifact.abi, deployer.connect(provider));
  if (await provider.getCode(manifest.contractAddress) === '0x') throw new Error('No contract bytecode exists at the manifest address.');
  const desired = [
    { label: 'registrar issuer', role: await contract.ISSUER_ROLE(), address: registrar.address, enabled: true },
    { label: 'registrar oracle', role: await contract.ORACLE_ROLE(), address: registrar.address, enabled: true },
    { label: 'reviewer verifier', role: await contract.VERIFIER_ROLE(), address: reviewer.address, enabled: true },
    { label: 'deployer issuer revoked', role: await contract.ISSUER_ROLE(), address: deployer.address, enabled: false },
    { label: 'deployer oracle revoked', role: await contract.ORACLE_ROLE(), address: deployer.address, enabled: false },
    { label: 'deployer verifier revoked', role: await contract.VERIFIER_ROLE(), address: deployer.address, enabled: false },
  ];
  const pending = [];
  for (const item of desired) {
    if (await contract.hasRole(item.role, item.address) === item.enabled) continue;
    const gas = await contract.setRole.estimateGas(item.role, item.address, item.enabled);
    pending.push({ ...item, gas });
  }
  const fee = await provider.getFeeData();
  if (!fee.gasPrice) throw new Error('RPC did not return a usable gas price.');
  const totalGas = pending.reduce((sum, item) => sum + item.gas * 125n / 100n, 0n);
  const estimatedMaximum = totalGas * fee.gasPrice;
  const deployerInfo = await describeWallet(provider, 'deployer / admin', deployer);
  const registrarInfo = await describeWallet(provider, 'registrar', registrar);
  const reviewerInfo = await describeWallet(provider, 'reviewer', reviewer);
  console.log(JSON.stringify({
    network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID, latestBlock: blockNumber,
    contractAddress: manifest.contractAddress, explorerUrl: `${explorer}/address/${manifest.contractAddress}`,
    wallets: [deployerInfo, registrarInfo, reviewerInfo],
    roleChanges: pending.map(({ label, address, enabled, gas }) => ({ label, address, enabled, estimatedGas: gas.toString() })),
    estimatedMaximumGasWei: estimatedMaximum.toString(), estimatedMaximumX1T: ethers.formatEther(estimatedMaximum),
  }, null, 2));
  if (BigInt(deployerInfo.balanceWei) < estimatedMaximum) throw new Error('Deployer balance cannot cover all planned role assignments.');
  if (!process.argv.includes('--confirm-testnet')) throw new Error('Preflight passed. Add --confirm-testnet to explicitly authorize role transactions.');
  const assignments = [];
  for (const item of pending) {
    const tx = await contract.setRole(item.role, item.address, item.enabled, { gasLimit: item.gas * 125n / 100n, gasPrice: fee.gasPrice });
    const receipt = await tx.wait(1);
    if (!receipt || receipt.status !== 1 || (await contract.hasRole(item.role, item.address)) !== item.enabled) throw new Error(`Role update failed for ${item.label}.`);
    assignments.push({ role: item.label, address: item.address, enabled: item.enabled, transactionHash: tx.hash, blockNumber: receipt.blockNumber });
  }
  manifest.roleAssignments = { ...(manifest.roleAssignments || {}), ...Object.fromEntries(assignments.map((item) => [item.role, item])) };
  saveManifest(manifest);
  console.log(JSON.stringify({ status: 'confirmed', roleChanges: assignments }, null, 2));
}

main().catch((error) => { console.error(`Role configuration stopped: ${error.message}`); process.exitCode = 1; });
