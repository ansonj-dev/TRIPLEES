const root = document.querySelector('#verify-content');
const safe = (value) => String(value ?? '—').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const field = (name, value) => `<div class="verify-field"><small>${safe(name)}</small><strong>${safe(value || 'Not provided')}</strong></div>`;
const query = new URLSearchParams(location.search);
const batchCode = query.get('batch');

async function loadPublicRecord() {
  if (!batchCode) {
    root.innerHTML = '<section class="verify-state"><h1>Public record lookup</h1><p>Provide a batch code in the URL to view a public-safe record.</p></section>';
    return;
  }
  try {
    const response = await fetch(`/api/public/verify/${encodeURIComponent(batchCode)}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail?.message || 'No matching record was found.');
    const { project, batch } = result;
    const chain = result.chain || {};
    const explorer = chain.explorer_url || 'https://maculatus-scan.x1eco.com';
    root.innerHTML = `<div class="verify-state"><span class="tag">${batch.is_demo ? 'DEMO DATA' : 'PUBLIC RECORD'}</span><h1 style="margin:14px 0 6px">${safe(project.name)}</h1><p>${safe(result.disclaimer)}</p><p><strong>Source coverage:</strong> ${safe(result.source_coverage)}</p></div>
      <section class="verify-state section-space"><h2>Credit record</h2><div class="verify-grid">${field('Batch code', batch.batch_code)}${field('Serial', batch.serial_start)}${field('Project location', `${project.country}, ${project.region}`)}${field('Vintage', `${batch.vintage_start || '—'} to ${batch.vintage_end || '—'}`)}${field('Current state', batch.state)}${field('Batch quantity', `${Number(batch.quantity_kg_co2e).toLocaleString()} kg CO₂e`)}${field('Available balance', `${Number(batch.available_balance_kg).toLocaleString()} kg CO₂e`)}${field('Retirement history', `${Number(batch.retired_balance_kg).toLocaleString()} kg CO₂e`)}${field('Provisional integrity score', `${batch.integrity_score}/100 · not a certification`)}${field('Network', chain.chain_id ? `${chain.network} · ${chain.chain_id}` : 'No confirmed on-chain record')}${field('Project identifier', project.chain_project_id || 'Not registered on-chain')}${field('Contract', chain.contract_address || 'Not deployed')}</div>${chain.contract_address ? `<p class="tiny section-space"><a href="${safe(explorer)}/address/${safe(chain.contract_address)}" target="_blank" rel="noopener">View contract on X1 Explorer ↗</a>${chain.project_tx_hash ? ` · <a href="${safe(explorer)}/tx/${safe(chain.project_tx_hash)}" target="_blank" rel="noopener">Project registration ↗</a>` : ''}${batch.tx_hash ? ` · <a href="${safe(explorer)}/tx/${safe(batch.tx_hash)}" target="_blank" rel="noopener">Batch transaction ↗</a>` : ''}</p>` : ''}<div class="section-space"><h3>Public evidence references</h3>${(result.public_evidence || []).length ? result.public_evidence.map((e) => `<div class="verify-field"><small>${safe(e.evidence_type)} · ${safe(e.review_state)} · SHA-256</small><strong>${safe(e.sha256)}</strong>${e.anchor_tx_hash ? `<small>Anchored on chain ${safe(e.anchor_chain_id)} · <a href="${safe(explorer)}/tx/${safe(e.anchor_tx_hash)}" target="_blank" rel="noopener">View anchor transaction ↗</a></small>` : '<small>Not anchored on-chain</small>'}</div>`).join('') : '<p>No public evidence hash.</p>'}</div></section>
      <section class="verify-state section-space"><h2>Lifecycle history</h2><div class="verify-timeline">${result.events.length ? result.events.map((e) => `<article class="verify-event"><strong>${safe(e.event_type.replaceAll('_', ' '))}${e.is_demo ? ' · DEMO' : ' · CONFIRMED'}</strong><small>${safe(e.created_at)} · ${e.chain_id ? `Chain ${safe(e.chain_id)} · Block ${safe(e.block_number)} · ` : 'Local application record · '}${safe(e.quantity_kg_co2e ? `${Number(e.quantity_kg_co2e).toLocaleString()} kg CO₂e · ` : '')}${e.tx_hash ? `<a href="${safe(explorer)}/tx/${safe(e.tx_hash)}" target="_blank" rel="noopener">View confirmed transaction ↗</a>` : 'No on-chain transaction'}</small></article>`).join('') : '<p>No lifecycle events are available.</p>'}</div></section>
      <p class="tiny muted">This public view excludes original files, private profile data, and internal reviewer notes. A hash identifies file bytes; it does not establish source authenticity.</p>`;
  } catch (error) {
    root.innerHTML = `<section class="verify-state verify-error"><h1>Record unavailable</h1><p>${safe(error.message)}</p><a href="index.html">Return to TRIPLEES</a></section>`;
  }
}
loadPublicRecord();
