require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

const testnetKey = process.env.X1_DEPLOYER_PRIVATE_KEY;
const x1Networks = process.env.X1_TESTNET_RPC_URL ? {
  maculatus: {
    url: process.env.X1_TESTNET_RPC_URL,
    chainId: 10778,
    accounts: testnetKey ? [testnetKey] : [],
  },
} : {};

module.exports = {
  solidity: '0.8.24',
  networks: { hardhat: { chainId: 31337 }, ...x1Networks },
  paths: { sources: './contracts', tests: './test', cache: './cache', artifacts: './artifacts' },
};
