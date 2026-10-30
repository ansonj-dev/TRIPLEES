(() => {
  const root = document.getElementById('report-verification');
  const safe = (value = '') => String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const date = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(value)) + ' UTC' : '—';
  const field = (label, value) => `<div class="verify-report-field"><small>${safe(label)}</small><strong>${safe(value || '—')}</strong></div>`;
  async function load() {
    const anchorId = new URLSearchParams(location.search).get('id');
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
  load();
})();
