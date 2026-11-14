import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { Worker } from 'near-workspaces';

const wasmPath = fileURLToPath(new URL('../target/near/triplees_report_registry.wasm', import.meta.url));

test('report registry authorization, immutable versions, views, and reviewer permissions', async (context) => {
  const worker = await Worker.init();
  context.after(async () => worker.tearDown());
  const root = worker.rootAccount;
  const reviewer = await root.createSubAccount('reviewer');
  const unauthorized = await root.createSubAccount('unauthorized');
  const contract = await root.devDeploy(wasmPath);

  await root.call(contract, 'new', { owner_id: root.accountId });
  assert.equal(await contract.view('is_reviewer', { account_id: root.accountId }), true);
  assert.equal(await contract.view('is_reviewer', { account_id: reviewer.accountId }), false);

  const digest = 'ab'.repeat(32);
  const first = {
    investigation_id: 'INV-SANDBOX-1', report_version: 1,
    report_digest: digest, metadata_digest: null,
  };
  await assert.rejects(() => unauthorized.call(contract, 'commit_report', first));

  await root.call(contract, 'grant_reviewer', { account_id: reviewer.accountId });
  assert.equal(await contract.view('is_reviewer', { account_id: reviewer.accountId }), true);
  const committed = await reviewer.call(contract, 'commit_report', first);
  assert.equal(committed.reportDigest, digest);
  assert.equal(committed.submitter, reviewer.accountId);
  assert.ok(committed.committedAtNs > 0);
  assert.equal(await contract.view('verify_report', {
    investigation_id: 'INV-SANDBOX-1', report_version: 1,
  }).then((record) => record.reportDigest), digest);
  assert.equal(await contract.view('verify_report', {
    investigation_id: 'INV-MISSING', report_version: 1,
  }), null);

  await assert.rejects(() => reviewer.call(contract, 'commit_report', { ...first, report_digest: 'not-a-digest' }));
  await assert.rejects(() => reviewer.call(contract, 'commit_report', { ...first, report_digest: 'cd'.repeat(32) }));
  const second = await reviewer.call(contract, 'commit_report', {
    ...first, report_version: 2, report_digest: 'cd'.repeat(32),
  });
  assert.equal(second.reportVersion, 2);
  assert.equal(await contract.view('verify_report', {
    investigation_id: 'INV-SANDBOX-1', report_version: 2,
  }).then((record) => record.reportDigest), 'cd'.repeat(32));

  await root.call(contract, 'revoke_reviewer', { account_id: reviewer.accountId });
  assert.equal(await contract.view('is_reviewer', { account_id: reviewer.accountId }), false);
  await assert.rejects(() => reviewer.call(contract, 'commit_report', {
    ...first, report_version: 3,
  }));
});