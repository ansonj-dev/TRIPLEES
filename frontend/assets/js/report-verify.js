(() => {
  const root = document.getElementById('report-verification');
  const safe = (value = '') => String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const date = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(value)) + ' UTC' : '—';
  const field = (label, value) => `<div class="verify-report-field"><small>${safe(label)}</small><strong>${safe(value || '—')}</strong></div>`;
  async function load() {
    const params = new URLSearchParams(location.search);
    const nearId = params.get('near');
    if (nearId) { await loadNearCommitment(nearId); return; }
    const anchorId = params.get('id');
    if (!anchorId) { root.innerHTML = '<div class="callout warning"><h1>Missing commitment reference</h1><p>Open the public verification link supplied with the report.</p></div>'; return; }
    try {
      const response = await fetch(`/api/public/report-anchors/${encodeURIComponent(anchorId)}`);
      const result = await response.json();
      if (!response.ok) throw new Error(result.error?.message || result.detail?.message || 'No public report commitment matches this reference.');
      const verified = result.verified_on_chain === true;
      const pending = result.status !== 'confirmed';
      const mismatch = result.status === 'confirmed' && result.verified_on_chain === false;
      const heading = verified ? 'Digest verified on X1' : mismatch ? 'Digest does not match the X1 record' : pending ? 'Approval recorded; not yet anchored' : 'On-chain verification unavailable';
      const txLink = result.transaction_hash ? `<a class="btn btn-sm" href="${safe(result.explorer_url)}/tx/${encodeURIComponent(result.transaction_hash)}" target="_blank" rel="noopener noreferrer">Open transaction on X1 ↗</a>` : '';
      const contractLink = result.contract_address ? `<a class="table-action" href="${safe(result.explorer_url)}/address/${encodeURIComponent(result.contract_address)}" target="_blank" rel="noopener noreferrer">View contract ↗</a>` : '';
      root.innerHTML = `<p class="eyebrow">TRIPLEES · PUBLIC REPORT COMMITMENT</p><h1>${heading}</h1><p class="callout ${verified ? 'info' : 'warning'}">${verified ? 'The contract record matches this report version and SHA-256 digest.' : mismatch ? 'The on-chain key exists but its stored hash or version does not match this commitment.' : pending ? 'This reference has a reviewer-approved digest, but no confirmed blockchain record is available yet.' : 'The service could not confirm a matching on-chain record. Check the network and contract details.'}</p><div class="verify-report-grid">${field('Commitment status', result.status.replaceAll('_', ' '))}${field('Network', result.network)}${field('Chain ID', result.chain_id)}${field('Report version', result.report_version)}${field('Digest algorithm', result.canonicalization)}${field('Anchored at (UTC)', date(result.anchored_at))}${field('SHA-256 digest', result.sha256)}</div><div class="verify-report-links">${txLink}${contractLink}</div><p class="tiny muted">This page does not disclose report contents, findings, project details, reviewer identity, or approval reason. A blockchain digest proves that a hash was recorded; it does not prove that the report is accurate or certify a project or credits.</p>`;
    } catch (error) {
      root.innerHTML = `<div class="callout warning"><h1>Could not verify this commitment</h1><p>${safe(error.message)}</p></div>`;
    }
  }
  async function loadNearCommitment(commitmentId) {
    try {
      const response = await fetch(`/api/public/near/commitments/${encodeURIComponent(commitmentId)}`);
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail?.message || 'No public NEAR commitment matches this reference.');
      const verified = result.status === 'confirmed' && result.verified_on_chain === true;
      const mismatch = result.status === 'confirmed' && result.verified_on_chain === false;
      const title = verified ? 'Digest verified on NEAR testnet' : mismatch ? 'Digest does not match the NEAR record' : result.status === 'pending' ? 'NEAR commitment is pending' : 'NEAR verification unavailable';
      const txLink = result.transaction_hash ? `<a class="btn btn-sm" href="${safe(result.explorer_url)}/transactions/${encodeURIComponent(result.transaction_hash)}" target="_blank" rel="noopener noreferrer">Open transaction on NEAR ↗</a>` : '';
      root.innerHTML = `<p class="eyebrow">TRIPLEES · NEAR TESTNET REPORT COMMITMENT</p><h1>${title}</h1><p class="callout ${verified ? 'info' : 'warning'}">${verified ? 'The stored report digest, submitter, and report version match the public contract view.' : mismatch ? 'A commitment exists, but its contract state does not match the published digest metadata.' : 'No confirmed contract state is available yet. A pending transaction is not shown as verified.'}</p><div class="verify-report-grid">${field('Commitment status', result.status)}${field('Network', 'NEAR Testnet')}${field('Report version', result.report_version)}${field('Canonicalization', result.canonicalization)}${field('NEAR account', result.near_account_id)}${field('Contract ID', result.contract_id)}${field('SHA-256 digest', result.sha256)}${field('Transaction hash', result.transaction_hash)}</div><div class="verify-report-links">${txLink}</div><section class="near-public-check"><h2>Check a report copy</h2><p>Select the JSON report downloaded from TRIPLEES. Its contents are used only to calculate the digest and are not stored.</p><div class="field"><label for="near-report-file">Report JSON file</label><input id="near-report-file" type="file" accept=".json,application/json"></div><button id="near-report-verify" class="btn btn-primary" type="button">Verify report copy</button><div id="near-report-result" aria-live="polite"></div></section><p class="tiny muted">A matching digest proves file integrity relative to the committed digest. It does not prove that environmental claims are true or certify a project or credits.</p>`;
      document.getElementById('near-report-verify').addEventListener('click', () => verifyNearReportCopy(commitmentId));
    } catch (error) {
      root.innerHTML = `<div class="callout warning"><h1>Could not verify this NEAR commitment</h1><p>${safe(error.message)}</p></div>`;
    }
  }
  async function verifyNearReportCopy(commitmentId) {
    const input = document.getElementById('near-report-file');
    const output = document.getElementById('near-report-result');
    const file = input?.files?.[0];
    if (!file) { output.innerHTML = '<p class="callout warning">Choose a report JSON file first.</p>'; return; }
    if (file.size > 2_000_000) { output.innerHTML = '<p class="callout warning">The report JSON file exceeds the 2 MB verification limit.</p>'; return; }
    const button = document.getElementById('near-report-verify');
    button.disabled = true;
    button.textContent = 'Verifying…';
    try {
      const report = JSON.parse(await file.text());
      const response = await fetch(`/api/public/near/commitments/${encodeURIComponent(commitmentId)}/verify`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ report }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail?.message || 'The supplied report could not be verified.');
      const verified = result.result === 'VERIFIED';
      const message = verified ? 'VERIFIED: supplied report digest matches the NEAR testnet commitment.' : result.result === 'UNAVAILABLE' ? 'The report digest was calculated, but the NEAR contract could not be reached.' : 'MISMATCH: supplied report digest does not match the NEAR testnet commitment.';
      output.innerHTML = `<p class="callout ${verified ? 'info' : 'warning'}" role="status">${safe(message)}</p><div class="verify-report-grid">${field('Calculated SHA-256', result.report_digest)}${field('Digest match', result.digest_matches ? 'Yes' : 'No')}${field('Contract state match', result.verified_on_chain === null ? 'Unavailable' : result.verified_on_chain ? 'Yes' : 'No')}</div><p class="tiny muted">${safe(result.integrity_note)}</p>`;
    } catch (error) {
      output.innerHTML = `<p class="callout warning" role="alert">${safe(error.message || 'The report file is not valid JSON.')}</p>`;
    } finally {
      button.disabled = false;
      button.textContent = 'Verify report copy';
    }
  }
  load();
})();
