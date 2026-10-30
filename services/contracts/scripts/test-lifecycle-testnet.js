const fs = require('fs');
const path = require('path');
const { ethers } = require('ethers');
const {
  providerForTestnet, accountFromEnv, artifact, deploymentManifest, saveManifest,
  explorer, EXPECTED_CHAIN_ID,
} = require('./chain-utils');

const batchId = process.argv[2];
if (!batchId) throw new Error('Pass the confirmed API batch ID as the first argument.');

async function main() {
  const { provider } = await providerForTestnet();
  const manifest = deploymentManifest();
  if (manifest.chainId !== EXPECTED_CHAIN_ID) throw new Error('Deployment manifest does not target Maculatus.');
  const artifactJson = artifact();
  if (await provider.getCode(manifest.contractAddress) === '0x') throw new Error('No contract code at the configured deployment address.');
  const registrar = accountFromEnv('X1_REGISTRAR_PRIVATE_KEY').connect(provider);
  const reviewer = accountFromEnv('X1_REVIEWER_PRIVATE_KEY').connect(provider);
  if (registrar.address.toLowerCase() === reviewer.address.toLowerCase()) throw new Error('Registrar and reviewer must be separate signers.');
  const registrarContract = new ethers.Contract(manifest.contractAddress, artifactJson.abi, registrar);
  const reviewerContract = new ethers.Contract(manifest.contractAddress, artifactJson.abi, reviewer);
  const key = ethers.keccak256(ethers.toUtf8Bytes(batchId));
  const item = await registrarContract.getCreditBatch(key);
  if (Number(item.state) !== 1) throw new Error('The selected batch must be active before the lifecycle test.');
  if (!(await registrarContract.hasRole(await registrarContract.ORACLE_ROLE(), registrar.address))) throw new Error('Registrar oracle role was not verified.');
  if (!(await reviewerContract.hasRole(await reviewerContract.VERIFIER_ROLE(), reviewer.address))) throw new Error('Reviewer verifier role was not verified.');

  const resultPath = path.resolve(__dirname, '../../../data/x1-testnet-lifecycle.json');
  const previousRun = fs.existsSync(resultPath) ? JSON.parse(fs.readFileSync(resultPath, 'utf8')) : null;
  const alreadyCompleted = previousRun?.batchId === batchId && previousRun.actions?.length === 5;
  const actions = alreadyCompleted ? previousRun.actions : [];
  const record = (action, tx, receipt) => {
    actions.push({ action, transactionHash: tx.hash, blockNumber: receipt.blockNumber, explorerUrl: `${explorer}/tx/${tx.hash}` });
    fs.mkdirSync(path.dirname(resultPath), { recursive: true });
    fs.writeFileSync(resultPath, `${JSON.stringify({ network: 'X1 EcoChain Testnet (Maculatus)', chainId: EXPECTED_CHAIN_ID, contractAddress: manifest.contractAddress, batchId, actions }, null, 2)}\n`, 'utf8');
  };
  async function send(action, signerContract, methodName, args) {
    const signer = await signerContract.runner.getAddress();
    const method = signerContract[methodName];
    const gas = await method.estimateGas(...args, { from: signer });
    const fee = await provider.getFeeData();
    if (!fee.gasPrice) throw new Error(`No gas price available for ${action}.`);
    const maximum = gas * 125n / 100n * fee.gasPrice;
    const balance = await provider.getBalance(signer);
    console.log(JSON.stringify({ operation: action, signer, estimatedMaximumX1T: ethers.formatEther(maximum), balanceX1T: ethers.formatEther(balance) }));
    if (balance < maximum) throw new Error(`Insufficient signer balance for ${action}; no transaction sent.`);
    const tx = await method(...args, { gasLimit: gas * 125n / 100n, gasPrice: fee.gasPrice });
    const receipt = await tx.wait(1);
    if (!receipt || receipt.status !== 1) throw new Error(`${action} transaction reverted: ${tx.hash}`);
    record(action, tx, receipt);
  }

  // A call-only duplicate attempt consumes no funds and must revert.
  let duplicateRejected = false;
  try { await registrarContract.registerCreditBatch.staticCall(key, item.projectId, registrar.address, item.quantityKg, item.evidenceHash); } catch { duplicateRejected = true; }
  if (!duplicateRejected) throw new Error('Duplicate issuance unexpectedly passed the read-only contract call.');

  const transferKg = 1000n;
  const retireKg = 500n;
  if (!alreadyCompleted) {
    await send('Transfer 1000 kg to reviewer', registrarContract, 'transfer', [key, reviewer.address, transferKg]);
    await send('Retire 500 kg from reviewer balance', reviewerContract, 'retire', [key, retireKg, ethers.keccak256(ethers.toUtf8Bytes(`QA-RETIRE-${batchId}`))]);
    await send('Mark batch at risk', registrarContract, 'markAtRisk', [key, ethers.keccak256(ethers.toUtf8Bytes(`SYNTHETIC-RISK-${batchId}`))]);
    await send('Open reviewer workflow', registrarContract, 'openReview', [key, ethers.keccak256(ethers.toUtf8Bytes(`SYNTHETIC-REVIEW-${batchId}`))]);
    await send('Reviewer rejects synthetic reversal signal', reviewerContract, 'recordReviewDecision', [key, 2, ethers.keccak256(ethers.toUtf8Bytes(`REJECT-SYNTHETIC-SIGNAL-${batchId}`))]);
  }

  const current = await registrarContract.getCreditBatch(key);
  const registrarBalance = await registrarContract.availableOf(key, registrar.address);
  const reviewerBalance = await registrarContract.availableOf(key, reviewer.address);
  const history = await registrarContract.getBatchHistory(key);
  if (Number(current.state) !== 1 || current.retiredKg !== retireKg || registrarBalance !== item.quantityKg - transferKg || reviewerBalance !== transferKg - retireKg || history.length < 6) {
    throw new Error('Post-action contract state or lifecycle history did not match the expected values.');
  }
  manifest.lifecycleDemo = { batchId, duplicateIssuanceRejected: true, historyLength: history.length, actions };
  saveManifest(manifest);
  console.log(JSON.stringify({ status: 'confirmed', duplicateIssuanceRejected: true, batchId, state: 'Active', totalQuantityKg: current.quantityKg.toString(), retiredKg: current.retiredKg.toString(), registrarBalanceKg: registrarBalance.toString(), reviewerBalanceKg: reviewerBalance.toString(), historyLength: history.length, actions, resultFile: 'data/x1-testnet-lifecycle.json' }, null, 2));
}

main().catch((error) => { console.error(`Testnet lifecycle check stopped: ${error.message}`); process.exitCode = 1; });
