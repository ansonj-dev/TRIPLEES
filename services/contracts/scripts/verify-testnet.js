const { ethers } = require('ethers');
const { providerForTestnet, artifact, deploymentManifest, explorer, EXPECTED_CHAIN_ID } = require('./chain-utils');

async function main() {
  const { provider, blockNumber } = await providerForTestnet();
  const manifest = deploymentManifest();
  if (manifest.chainId !== EXPECTED_CHAIN_ID) throw new Error('Deployment manifest chain ID does not match Maculatus.');
  const code = await provider.getCode(manifest.contractAddress);
  if (code === '0x') throw new Error('Configured deployment has no runtime bytecode on Maculatus.');
  const artifactJson = artifact();
  const contract = new ethers.Contract(manifest.contractAddress, artifactJson.abi, provider);
  const checks = [];
  const deployerKey = process.env.X1_DEPLOYER_PRIVATE_KEY;
  if (deployerKey) {
    const deployerAddress = new ethers.Wallet(deployerKey).address;
    for (const [label, getter] of [['deployer issuer removed', 'ISSUER_ROLE'], ['deployer oracle removed', 'ORACLE_ROLE'], ['deployer verifier removed', 'VERIFIER_ROLE']]) {
      checks.push({ role: label, address: deployerAddress, configured: true, valid: !(await contract.hasRole(await contract[getter](), deployerAddress)) });
    }
  }
  for (const [label, envName, getter] of [
    ['registrar issuer', 'X1_REGISTRAR_PRIVATE_KEY', 'ISSUER_ROLE'],
    ['registrar oracle', 'X1_REGISTRAR_PRIVATE_KEY', 'ORACLE_ROLE'],
    ['reviewer verifier', 'X1_REVIEWER_PRIVATE_KEY', 'VERIFIER_ROLE'],
  ]) {
    const key = process.env[envName];
    if (!key) { checks.push({ role: label, configured: false, valid: null }); continue; }
    const address = new ethers.Wallet(key).address;
    checks.push({ role: label, address, configured: true, valid: await contract.hasRole(await contract[getter](), address) });
  }
  console.log(JSON.stringify({
    network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID,
    latestBlock: blockNumber, contractAddress: manifest.contractAddress,
    runtimeBytecodeHash: ethers.keccak256(code), deploymentTransaction: manifest.deploymentTxHash,
    explorerContractUrl: `${explorer}/address/${manifest.contractAddress}`,
    explorerDeploymentUrl: `${explorer}/tx/${manifest.deploymentTxHash}`,
    verifiedOnExplorer: manifest.verifiedOnExplorer === true,
    roleChecks: checks,
  }, null, 2));
  if (checks.some((check) => check.configured && !check.valid)) process.exitCode = 1;
}

main().catch((error) => { console.error(`Deployment verification failed: ${error.message}`); process.exitCode = 1; });
