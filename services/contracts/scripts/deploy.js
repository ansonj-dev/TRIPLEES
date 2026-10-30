const hre = require('hardhat');

async function main() {
  const Registry = await hre.ethers.getContractFactory('VericarbRegistry');
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  console.log(`VericarbRegistry deployed at ${await registry.getAddress()} on chain ${hre.network.config.chainId}`);
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
