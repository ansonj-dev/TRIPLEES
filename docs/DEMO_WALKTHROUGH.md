# Demo walkthrough

## Local app

1. Start FastAPI from the repository root and sign in with **Explore the demo workspace**.
2. Confirm the shell badge reports the result of the live X1 RPC check. Open Dashboard → **Blockchain Activity** to inspect chain ID, latest block, deployment state, check time, and confirmed transactions. An RPC connection does not mean a contract is deployed.
3. Create a fictional project, open its passport, and upload a non-sensitive sample file. The API stores the bytes locally and calculates SHA-256.
4. With a deployed contract and registrar configured, register the project and anchor the evidence hash. The UI waits for the API receipt/state read-back before refreshing. The raw file remains off-chain.
5. Create a batch, submit it for a reviewer decision, resolve available local conflict checks, then issue it. When a contract is configured, the API registers the batch and stores the confirmed tx hash; without one it explicitly reports `not_configured`.
6. The current transfer, retirement, risk, and reviewer actions are local audit history only. Treat synthetic observations and seeded data as demo fixtures, not actual climate evidence.

## Live funded demo

Once all three test wallets are configured and independently checked, deploy using `docs/DEPLOYMENT_AND_VERIFICATION.md`. Record the actual deployment, role, project, batch, anchor, and lifecycle hashes from receipts and verify them from the configured explorer. Keep live operations on Maculatus and use small test quantities. Do not fabricate successful transaction links when a step was not run.
