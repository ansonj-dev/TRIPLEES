const fs = require('fs');
const path = require('path');
const { ethers } = require('ethers');
const { providerForTestnet, accountFromEnv, describeWallet, explorer, EXPECTED_CHAIN_ID } = require('./chain-utils');

const root = path.resolve(__dirname, '../../..');

async function main() {
  const { provider, blockNumber } = await providerForTestnet();
  const deployer = accountFromEnv('X1_DEPLOYER_PRIVATE_KEY');
  const reviewer = accountFromEnv('X1_REVIEWER_PRIVATE_KEY');
  if (deployer.address.toLowerCase() === reviewer.address.toLowerCase()) {
    throw new Error('The report anchorer must be a separate reviewer wallet. No transaction sent.');
  }
  const artifactPath = path.join(root, 'services', 'contracts', 'artifacts', 'contracts', 'InvestigationReportAnchorRegistry.sol', 'InvestigationReportAnchorRegistry.json');
  if (!fs.existsSync(artifactPath)) throw new Error('Contract artifact missing. Run npm run compile first.');
  const contractArtifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
  const factory = new ethers.ContractFactory(contractArtifact.abi, contractArtifact.bytecode, deployer.connect(provider));
  const deployTx = await factory.getDeployTransaction();
  deployTx.from = deployer.address;
  const deployGas = await provider.estimateGas(deployTx);
  const feeData = await provider.getFeeData();
  if (!feeData.gasPrice) throw new Error('RPC did not return a usable gas price. No transaction sent.');
  const roleGas = 120000n;
  const estimatedGas = deployGas * 125n / 100n + roleGas;
  const maxCost = estimatedGas * feeData.gasPrice;
  const deployerInfo = await describeWallet(provider, 'deployer / contract admin', deployer);
  console.log(JSON.stringify({
    operation: 'Deploy separate investigation report anchor contract and grant reviewer anchor role',
    network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID,
    latestBlock: blockNumber, deployer: deployerInfo, reviewerAnchoringAddress: reviewer.address,
    estimatedGas: estimatedGas.toString(), gasPriceWei: feeData.gasPrice.toString(),
    estimatedMaximumWei: maxCost.toString(), estimatedMaximumX1T: ethers.formatEther(maxCost), explorer,
  }, null, 2));
  if (BigInt(deployerInfo.balanceWei) < maxCost) throw new Error('Deployer balance is below the estimated maximum gas cost. No transaction sent.');
  if (!process.argv.includes('--confirm-testnet')) {
    throw new Error('Preflight passed. Review the destination and gas estimate, then add --confirm-testnet to explicitly authorize deployment and role assignment.');
  }

  const contract = await factory.deploy({ gasLimit: deployGas * 125n / 100n, gasPrice: feeData.gasPrice });
  const deploymentTx = contract.deploymentTransaction();
  const deploymentReceipt = await deploymentTx.wait(1);
  if (!deploymentReceipt || deploymentReceipt.status !== 1) throw new Error(`Deployment transaction ${deploymentTx.hash} did not confirm.`);
  const address = await contract.getAddress();
  if (await provider.getCode(address) === '0x') throw new Error('Deployment succeeded but runtime bytecode is missing.');
  const role = await contract.ANCHORER_ROLE();
  const grantTx = await contract.setAnchorer(reviewer.address, true, { gasLimit: roleGas / 2n, gasPrice: feeData.gasPrice });
  const grantReceipt = await grantTx.wait(1);
  if (!grantReceipt || grantReceipt.status !== 1 || !(await contract.hasRole(role, reviewer.address))) {
    throw new Error(`Reviewer role assignment ${grantTx.hash} did not confirm.`);
  }
  const revokeTx = await contract.setAnchorer(deployer.address, false, { gasLimit: roleGas / 2n, gasPrice: feeData.gasPrice });
  const revokeReceipt = await revokeTx.wait(1);
  if (!revokeReceipt || revokeReceipt.status !== 1 || await contract.hasRole(role, deployer.address)) {
    throw new Error(`Deployer anchor-role revocation ${revokeTx.hash} did not confirm.`);
  }
  const manifest = {
    network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID,
    contractName: 'InvestigationReportAnchorRegistry', contractAddress: address,
    deployer: deployer.address, reviewerAnchorer: reviewer.address,
    deploymentTransactionHash: deploymentTx.hash, deploymentBlock: deploymentReceipt.blockNumber,
    reviewerRoleTransactionHash: grantTx.hash, reviewerRoleBlock: grantReceipt.blockNumber,
    deployerRoleRevocationTransactionHash: revokeTx.hash, deployerRoleRevocationBlock: revokeReceipt.blockNumber,
    explorerUrl: `${explorer}/address/${address}`, deployedAt: new Date().toISOString(),
  };
  const output = path.join(root, 'data', 'report-anchor-deployment.json');
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({ status: 'confirmed', ...manifest, manifest: 'data/report-anchor-deployment.json', setInEnv: `X1_REPORT_ANCHOR_CONTRACT_ADDRESS=${address}` }, null, 2));
}

main().catch((error) => { console.error(`Report anchor deployment stopped: ${error.message}`); process.exitCode = 1; });
