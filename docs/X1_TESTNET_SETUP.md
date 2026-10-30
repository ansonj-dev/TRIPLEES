# X1 EcoChain Maculatus setup

## Network verification

The official X1 developer portal identifies Maculatus as the testnet and links its faucet and explorer: [X1 developer portal](https://dev.x1ecochain.com/). The [Maculatus explorer](https://maculatus-scan.x1eco.com/) identifies the network as X1 EcoChain Testnet; its [API documentation](https://maculatus-scan.x1eco.com/api-docs) provides explorer API reference. The official [X1 site](https://x1ecochain.com/) describes EVM compatibility.

The application also queried the configured RPC directly using `eth_chainId` and `eth_blockNumber`. On 2026-10-25 UTC, `https://maculatus-rpc.x1eco.com` returned chain ID `0x2a1a` (10778); the latest health check returned block `11859271`. The Python API and Hardhat check both connected and reported 10778. Block height changes continuously; rerun `npm run chain:check` for current status.

| Setting | Value |
|---|---|
| Network | X1 EcoChain Testnet (Maculatus) |
| Chain ID | `10778` |
| RPC | `https://maculatus-rpc.x1eco.com` |
| Explorer | `https://maculatus-scan.x1eco.com` |
| Native test token | `X1T` (verified from live explorer/RPC response) |
| Transaction link | `{explorer}/tx/{transactionHash}` |
| Address link | `{explorer}/address/{address}` |

The official portal links to the explorer and faucet. The RPC hostname and chain ID were verified with a live JSON-RPC response; the portal page does not publish an explicit chain ID. The live RPC check is the network identity guard used before transactions.

## Local configuration

Copy `.env.example` to ignored `.env`. Public network defaults are prefilled; keep all private key values local. Set three independent testnet-only keys:

```dotenv
X1_DEPLOYER_PRIVATE_KEY=
X1_REGISTRAR_PRIVATE_KEY=
X1_REVIEWER_PRIVATE_KEY=
```

The three local wallet keys are configured, independently checked, and were used for the testnet deployment, role grants, and a small fictional lifecycle test. Current addresses, latest balances, role receipts, and transaction links are in `DEPLOYMENT_AND_VERIFICATION.md`. The keys remain only in ignored `.env`; never paste or commit them.

The API settings are `X1_TESTNET_RPC_URL`, `X1_TESTNET_CHAIN_ID`, `X1_TESTNET_EXPLORER_URL`, `X1_TESTNET_NATIVE_CURRENCY`, and `X1_REGISTRY_CONTRACT_ADDRESS`. A chain mismatch blocks signing. The optional `X1_REPORT_ANCHOR_CONTRACT_ADDRESS` points to a separate report-commitment contract; it does not replace the existing registry. See [Report Anchoring](REPORT_ANCHORING.md) for its distinct reviewer flow and deployment approval gate.
