const { ethers } = require('ethers');
const { providerForTestnet, accountFromEnv, describeWallet, artifact, saveManifest, saveLocalContractAddress, explorer, EXPECTED_CHAIN_ID } = require('./chain-utils');

async function main() {
  const { provider, blockNumber } = await providerForTestnet();
  const deployer = accountFromEnv('X1_DEPLOYER_PRIVATE_KEY');
  const wallet = await describeWallet(provider, 'deployer', deployer);
  const contractArtifact = artifact();
  const factory = new ethers.ContractFactory(contractArtifact.abi, contractArtifact.bytecode, deployer.connect(provider));
  const deploymentTx = await factory.getDeployTransaction();
  deploymentTx.from = deployer.address;
  const gasEstimate = await provider.estimateGas(deploymentTx);
  const feeData = await provider.getFeeData();
  const gasPrice = feeData.gasPrice;
  if (!gasPrice) throw new Error('RPC did not return a usable gas price. No transaction sent.');
  const maxCost = gasEstimate * 125n / 100n * gasPrice;
  const balance = BigInt(wallet.balanceWei);
  const predictedAddress = ethers.getCreateAddress({ from: deployer.address, nonce: await provider.getTransactionCount(deployer.address, 'pending') });
  console.log(JSON.stringify({
    operation: 'Deploy VericarbRegistry', network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID,
    latestBlock: blockNumber, sender: wallet.address, predictedContractAddress: predictedAddress,
    estimatedGas: gasEstimate.toString(), gasPriceWei: gasPrice.toString(), maxCostWei: maxCost.toString(),
    maxCostX1T: ethers.formatEther(maxCost), balanceX1T: wallet.balanceX1T, explorer,
  }, null, 2));
  if (balance < maxCost) throw new Error('Deployer balance is below the estimated maximum gas cost. No transaction sent.');
  if (!process.argv.includes('--confirm-testnet')) throw new Error('Preflight passed. Add --confirm-testnet to explicitly authorize this testnet deployment.');

  const contract = await factory.deploy({ gasLimit: gasEstimate * 125n / 100n, gasPrice });
  const txHash = contract.deploymentTransaction().hash;
  const receipt = await contract.deploymentTransaction().wait(1);
  if (!receipt || receipt.status !== 1) throw new Error(`Deployment transaction ${txHash} did not produce a successful receipt.`);
  const address = await contract.getAddress();
  const code = await provider.getCode(address);
  if (code === '0x') throw new Error('Deployment receipt succeeded, but no runtime bytecode was found at the contract address.');
  const manifest = {
    network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID,
    rpcUrl: process.env.X1_TESTNET_RPC_URL, explorer, contractAddress: address,
    deployer: deployer.address, deploymentTxHash: txHash, deploymentBlock: receipt.blockNumber,
    deploymentGasUsed: receipt.gasUsed.toString(), runtimeBytecodeHash: ethers.keccak256(code),
    verifiedOnExplorer: false, deployedAt: new Date().toISOString(), roleAssignments: {},
  };
  saveManifest(manifest);
  saveLocalContractAddress(address);
  console.log(JSON.stringify({ status: 'confirmed', contractAddress: address, transactionHash: txHash, explorerUrl: `${explorer}/tx/${txHash}`, manifest: 'data/x1-testnet-deployment.json', verifiedOnExplorer: false }, null, 2));
}

main().catch((error) => { console.error(`Testnet deployment stopped: ${error.message}`); process.exitCode = 1; });
