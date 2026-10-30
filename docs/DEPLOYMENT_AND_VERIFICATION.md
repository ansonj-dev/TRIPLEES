# Deployment and verification runbook

## Confirmed deployment

Deployed to X1 EcoChain Testnet (Maculatus), chain ID `10778`. The contract has runtime bytecode at [0x5BF650b0b46D40794B116c36f75DABAcF5ed9e8b](https://maculatus-scan.x1eco.com/address/0x5BF650b0b46D40794B116c36f75DABAcF5ed9e8b). Deployment transaction: [0x5d5faa4233d59bb941475cd38cd86d08c7ebc32cc93954343372f3be83edab78](https://maculatus-scan.x1eco.com/tx/0x5d5faa4233d59bb941475cd38cd86d08c7ebc32cc93954343372f3be83edab78), block `11860437`, gas used `3,235,252`. Runtime bytecode hash: `0x7332f12254ad8082ac69623231eb488fa9b840b362a8edb1b7fdb87567cb677a`. Explorer source verification was not performed (`verifiedOnExplorer: false`). Address is stored in ignored `.env` and the ignored `data/x1-testnet-deployment.json` manifest.

Role grants were confirmed and read back:

- Registrar issuer: [0x41a5b603bcf3fbe01cfa98c5d5e8d48746a724483ad4bb22a1448efb5bdb7bed](https://maculatus-scan.x1eco.com/tx/0x41a5b603bcf3fbe01cfa98c5d5e8d48746a724483ad4bb22a1448efb5bdb7bed)
- Registrar oracle: [0x36ed273196cd57ae0220515bd3a5b32e373ce5a6748a23ba9b6fb4154746efa9](https://maculatus-scan.x1eco.com/tx/0x36ed273196cd57ae0220515bd3a5b32e373ce5a6748a23ba9b6fb4154746efa9)
- Reviewer verifier: [0x430946e407d5b3f69d5548ac679b5b9f69d1359fc13bc33e3992604f0c023540](https://maculatus-scan.x1eco.com/tx/0x430946e407d5b3f69d5548ac679b5b9f69d1359fc13bc33e3992604f0c023540)

The deployer retains the admin role but its default issuer, oracle, and verifier permissions were removed to keep operational roles on the registrar and reviewer wallets. The revocations were confirmed at [issuer](https://maculatus-scan.x1eco.com/tx/0x14c0328c2658307fa063d3db2ad486ed7d028b168f1bd734ca2de0598bdc1419), [oracle](https://maculatus-scan.x1eco.com/tx/0x09c8590a094955475aa544805dd6857361705d90c02866ddb1b34b5b68c84c67), and [verifier](https://maculatus-scan.x1eco.com/tx/0x6785e614a119e6b49ba909f5cf070d69894ab29a761162423ce58f4e69202514). The final role verifier confirmed all three removals and the registrar/reviewer grants.

The three configured wallets were independently checked on chain ID 10778 and were distinct. At the most recent check, balances were 99.996533544 X1T (deployer), 99.999022368 X1T (registrar), and 99.999671213 X1T (reviewer). Private keys are not recorded here.

## Confirmed QA transaction flow

The FastAPI flow created fictional project `PRJ-DEMO-2BA6ADD9B8DE`, uploaded a synthetic text fixture, anchored its backend SHA-256, and registered batch `BATCH-DEMO-5F3E8510ADD4` for `1,000,000 kg CO2e` (1,000 tCO2e). Public verification matched the on-chain project/batch/evidence values.

- Project registration: [0x282e48cfdb6edea27d387089a039c2a34d90bc0294261a106a31735a098ef466](https://maculatus-scan.x1eco.com/tx/0x282e48cfdb6edea27d387089a039c2a34d90bc0294261a106a31735a098ef466)
- Evidence SHA-256 anchor: [0xeb8caa2da32179e2b596e3f2fb4e8f9b0c0fe3cd9e349347c5901204b7ebb4f5](https://maculatus-scan.x1eco.com/tx/0xeb8caa2da32179e2b596e3f2fb4e8f9b0c0fe3cd9e349347c5901204b7ebb4f5)
- Batch issuance: [0x0e8d660946a8b5ba1a7b784fafb91d2a62ca1b3fc2fb87a120fae4fc45ced390](https://maculatus-scan.x1eco.com/tx/0x0e8d660946a8b5ba1a7b784fafb91d2a62ca1b3fc2fb87a120fae4fc45ced390)

The separate contract lifecycle harness rejected duplicate issuance using a read-only call, then confirmed a 1,000 kg registrar-to-reviewer transfer, a 500 kg retirement by the reviewer, a synthetic risk mark, review opening, and a reviewer rejection of the synthetic reversal signal. The final on-chain batch remained Active; 500 kg were retired, registrar balance was 999,000 kg, reviewer balance was 500 kg, and six batch history records were present. Transaction links are in [data/x1-testnet-lifecycle.json](../data/x1-testnet-lifecycle.json) (local ignored artifact).

## Preconditions

1. Put three testnet-only private keys in ignored `.env`; do not share them or commit them.
2. From `services/contracts`, run `npm run chain:check`. It checks chain ID, latest block, each key independently, public addresses, and X1T balances without printing keys.
3. Run `npm test` and `npm run compile`.
4. Review deployment and role plans and the estimated gas/cost output.

## Explicit testnet operations

```powershell
npm run chain:deploy:testnet -- --confirm-testnet
npm run chain:configure:testnet -- --confirm-testnet
npm run chain:verify:testnet
npm run chain:test:lifecycle -- <confirmed-batch-id>
```

The confirmation flag is required to broadcast. Deploy saves the confirmed deployment manifest under ignored `data/` and writes the registry address to ignored `.env`. Configure grants issuer/oracle to the registrar and verifier to the distinct reviewer, then reads roles back. Verify checks chain ID, bytecode, and role assignments. No explorer source verification is performed by these commands; do not call source code “verified” there unless a separate explorer verification succeeds.

The API accepts explicit project and evidence actions after configuration. It waits for receipts and verifies contract state. The batch issue path checks the registered project, duplicate batch, receipt, quantity, and signer balance. The lifecycle harness is contract-only; transfer/retirement/risk/reviewer actions in the main application have not yet been wired to those on-chain calls.

## Local routes

- `GET /api/blockchain/network`: public read-only network state.
- `GET /api/blockchain/status`: authenticated network, wallet presence/balances, and confirmed activity.
- `GET /api/blockchain/wallets/{address}/balance`: authenticated testnet balance for a public EVM address.
- `GET /api/blockchain/contracts`: authenticated deployment state.
- `POST /api/projects/{id}/register-chain`: authorized project registration.
- `POST /api/evidence/{id}/anchor`: authorized SHA-256 anchoring.
- `POST /api/batches/{id}/issue`: human-reviewed batch issuance; chain submit occurs only when a registry address is configured.

All three write paths depend on an authorized registrar key. Existing transfer, retirement, risk and reviewer UI workflows remain local-only at this stage.
