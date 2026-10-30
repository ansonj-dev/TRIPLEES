/* TRIPLEES local full-stack prototype. The API database is authoritative when connected. */
const STORE_KEY = 'vericarb-local-demo-v1';
const API_TOKEN_KEY = 'vericarb-api-demo-token';
const NAV = [
  { group: 'WORKSPACE' },
  { id: 'dashboard', label: 'Overview', icon: '◫', path: '/dashboard' },
  { id: 'projects', label: 'Projects', icon: '▧', path: '/projects' },
  { group: 'INTELLIGENCE' },
  { id: 'intelligence', label: 'Intelligence Dashboard', icon: '◉', path: '/intelligence' },
  { id: 'investigations', label: 'Investigation Center', icon: '⌕', path: '/investigations' },
  { id: 'agent-activity', label: 'Agent Activity', icon: '⌁', path: '/agent-activity' },
  { id: 'risk-intelligence', label: 'Risk Intelligence', icon: '⚑', path: '/risk-intelligence' },
  { id: 'investigation-reports', label: 'Investigation Reports', icon: '▤', path: '/investigation-reports' },
  { id: 'review-queue', label: 'Review Queue', icon: '✓', path: '/review-queue' },
  { group: 'RECORDS' },
  { id: 'credits', label: 'Carbon Credits', icon: '◈', path: '/credits' },
  { id: 'monitoring', label: 'Monitoring', icon: '⌁', path: '/monitoring' },
  { id: 'evidence', label: 'Evidence', icon: '▤', path: '/evidence' },
  { id: 'verification', label: 'Verification', icon: '✓', path: '/verification' },
  { id: 'conflicts', label: 'Registry Conflicts', icon: '◎', path: '/conflicts' },
  { id: 'marketplace', label: 'Marketplace', icon: '▣', path: '/marketplace', optional: true },
  { group: 'INSIGHTS' },
  { id: 'alerts', label: 'Alerts', icon: '♧', path: '/alerts' },
  { id: 'reports', label: 'Data Exports', icon: '▤', path: '/reports' },
  { id: 'explorer', label: 'Public Explorer', icon: '⌕', path: '/explorer' },
  { id: 'community', label: 'Community', icon: '♧', path: '/community', optional: true },
  { group: 'ACCOUNT' },
  { id: 'settings', label: 'Settings', icon: '⚙', path: '/settings' },
];

const demoProjects = [
  { id: 'DEMO-FOREST-001', name: 'Demo Forest Project ES-001', type: 'Forest conservation', country: 'Spain', region: 'Demo Region', methodology: 'DEMO-FOREST-METHODOLOGY', vintageStart: '2024-01-01', vintageEnd: '2024-12-31', registry: 'DEMO-Registry-A', registryRef: 'DEMO-FOREST-001', description: 'Synthetic baseline for product demonstration only.', status: 'At Risk', demo: true, updatedAt: '2026-01-20T10:00:00Z' },
  { id: 'DEMO-SOIL-002', name: 'Demo Soil Project ES-002', type: 'Soil carbon', country: 'Spain', region: 'Demo Region', methodology: 'DEMO-SOIL-METHODOLOGY', vintageStart: '2024-01-01', vintageEnd: '2024-12-31', registry: 'DEMO-Registry-A', registryRef: 'DEMO-SOIL-002', description: 'Fictional soil project fixture for the local prototype.', status: 'Under Review', demo: true, updatedAt: '2026-01-18T12:00:00Z' },
  { id: 'DEMO-WIND-003', name: 'Demo Wind Project ES-003', type: 'Renewable energy', country: 'Spain', region: 'Demo Region', methodology: 'DEMO-WIND-METHODOLOGY', vintageStart: '2023-01-01', vintageEnd: '2023-12-31', registry: '', registryRef: '', description: 'Synthetic clean-energy project used to demonstrate an evidence-complete workflow.', status: 'Active', demo: true, updatedAt: '2026-01-15T12:00:00Z' },
];

const demoCredits = [
  { id: 'DEMO-BATCH-001', projectId: 'DEMO-FOREST-001', serial: 'DEMO-SERIAL-0001', vintage: '2024', quantityKg: 1000000, availableKg: 1000000, retiredKg: 0, registry: 'DEMO-Registry-A', state: 'At Risk', components: { M: 58, V: 64, C: 35, R: 66, A: 72 }, score: 58, provisional: true, demo: true, updatedAt: '2026-01-20T10:00:00Z' },
  { id: 'DEMO-BATCH-002', projectId: 'DEMO-SOIL-002', serial: 'DEMO-SERIAL-0002', vintage: '2024', quantityKg: 250000, availableKg: 0, retiredKg: 250000, registry: 'DEMO-Registry-A', state: 'Retired', components: { M: 78, V: 74, C: 70, R: 62, A: 70 }, score: 71, provisional: true, demo: true, updatedAt: '2026-01-18T12:00:00Z' },
  { id: 'DEMO-BATCH-003', projectId: 'DEMO-WIND-003', serial: 'DEMO-SERIAL-0003', vintage: '2023', quantityKg: 350000, availableKg: 350000, retiredKg: 0, registry: 'Not connected', state: 'Active', components: { M: 82, V: 78, C: 75, R: 72, A: 72 }, score: 76, provisional: true, demo: true, updatedAt: '2026-01-15T12:00:00Z' },
];

const registryFixture = [
  { source: 'DEMO-Registry-A', projectRef: 'DEMO-FOREST-001', project: 'Demo Forest Project ES-001', serial: 'DEMO-SERIAL-0001', vintage: '2024', methodology: 'DEMO-FOREST-METHODOLOGY', country: 'Spain', quantityKg: 1000000, status: 'active', demo: true },
  { source: 'DEMO-Registry-B', projectRef: 'DEMO-FOREST-ALT-001', project: 'Demo Forest Project ES-001', serial: 'DEMO-SERIAL-0001', vintage: '2024', methodology: 'DEMO-FOREST-METHODOLOGY', country: 'Spain', quantityKg: 1000000, status: 'active', demo: true },
  { source: 'DEMO-Registry-A', projectRef: 'DEMO-SOIL-002', project: 'Demo Soil Project ES-002', serial: 'DEMO-SERIAL-0002', vintage: '2024', methodology: 'DEMO-SOIL-METHODOLOGY', country: 'Spain', quantityKg: 250000, status: 'retired', demo: true },
];

function freshData() {
  return {
    projects: demoProjects.map((x) => ({ ...x })),
    credits: demoCredits.map((x) => ({ ...x })),
    evidence: [
      { id: 'EVD-DEMO-001', projectId: 'DEMO-FOREST-001', name: 'Forest baseline — sample record', kind: 'Document', size: 0, mime: 'application/demo', uploadedAt: '2026-01-20T10:00:00Z', uploadedBy: 'Demo reviewer', hash: '', state: 'Sample only', demo: true, findings: ['Synthetic fixture. No source document is stored.'] },
      { id: 'EVD-DEMO-002', projectId: 'DEMO-WIND-003', name: 'Wind activity summary — sample record', kind: 'Data', size: 0, mime: 'application/demo', uploadedAt: '2026-01-15T12:00:00Z', uploadedBy: 'Demo reviewer', hash: '', state: 'Sample only', demo: true, findings: ['Synthetic fixture. No source document is stored.'] },
    ],
    observations: [{ id: 'OBS-DEMO-001', projectId: 'DEMO-FOREST-001', source: 'TRIPLEES synthetic monitoring fixture', signal: 'Forest cover change', severity: 'High', value: '18% affected area (illustrative)', observedAt: '2026-01-20T10:00:00Z', description: 'Synthetic demonstration event only; not a real satellite observation.', state: 'Needs human review', demo: true }],
    alerts: [{ id: 'ALT-DEMO-001', projectId: 'DEMO-FOREST-001', type: 'Potential disturbance', severity: 'At Risk', explanation: 'A synthetic forest-loss signal was added to demonstrate review handling.', createdAt: '2026-01-20T10:00:00Z', state: 'Open', demo: true, observationId: 'OBS-DEMO-001' }],
    reviews: [{ id: 'REV-DEMO-001', targetId: 'DEMO-BATCH-001', targetType: 'Registry conflict', finding: 'Duplicate serial appears in the available imported sample records.', state: 'Pending', createdAt: '2026-01-20T10:00:00Z', actor: 'Demo reviewer', reason: '', demo: true }],
    importedRecords: registryFixture.map((x) => ({ ...x })),
    events: [
      { id: 'EVT-DEMO-001', targetId: 'DEMO-FOREST-001', type: 'Project created', actor: 'Demo fixture', reason: 'Synthetic project record initialized for the prototype.', at: '2026-01-15T12:00:00Z', demo: true },
      { id: 'EVT-DEMO-002', targetId: 'DEMO-BATCH-001', type: 'Conflict detected', actor: 'Demo fixture', reason: 'Duplicate serial in imported sample data; source coverage is limited to these records.', at: '2026-01-16T12:00:00Z', demo: true },
      { id: 'EVT-DEMO-003', targetId: 'DEMO-FOREST-001', type: 'Monitoring observation added', actor: 'Demo fixture', reason: 'Synthetic observation. Not a live feed.', at: '2026-01-20T10:00:00Z', demo: true },
    ],
    settings: { displayName: 'Jordan Demo', email: 'demo@example.invalid', organization: 'Demo workspace', location: '', theme: 'System' },
    noticesDismissed: false,
  };
}

function readData() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE_KEY));
    if (saved && Array.isArray(saved.projects) && Array.isArray(saved.credits)) return { ...freshData(), ...saved };
  } catch (error) { console.warn('Could not read local demo workspace.', error); }
  return freshData();
}
let db = readData();
let backendConnected = false;
let blockchainStatus = null;
let aiProviderStatus = null;
let apiToken = localStorage.getItem(API_TOKEN_KEY) || '';
let activeTab = '';
let activeProjectTab = 'Overview';
let selectedProjectFilter = 'All';
let selectedCreditFilter = 'All';
let selectedAlertFilter = 'All';
let selectedMonitoringTab = 'All';
let selectedEvidenceTab = 'All';
let assessmentResult = null;
const intelligenceState = {
  dashboard: { loading: false, loaded: false, error: '', investigations: [], findings: [], reviewQueue: null, aiHealth: null, usage: null },
  center: { loading: false, loaded: false, error: '', investigations: [] },
  activity: { loading: false, loaded: false, loadedId: '', error: '', investigations: [], selectedId: '', detail: null, agents: null, audit: null },
  risk: { loading: false, loaded: false, error: '', findings: [] },
  reports: { loading: false, loaded: false, loadedId: '', loadingReport: false, error: '', reportError: '', investigations: [], selectedId: '', version: null, report: null },
  review: { loading: false, loaded: false, error: '', items: [], history: [] },
};
let riskFilters = { query: '', severity: 'All', status: 'All' };

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const niceDate = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : '—';
const niceDateTime = (value) => value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—';
const formatTonnes = (kg) => `${(Number(kg || 0) / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} tCO₂e`;
const formatKg = (kg) => `${Number(kg || 0).toLocaleString()} kg CO₂e`;
const id = (prefix) => `${prefix}-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
const save = () => { if (!backendConnected) localStorage.setItem(STORE_KEY, JSON.stringify(db)); };
async function apiRequest(path, options = {}, retryAuth = true) {
  const headers = new Headers(options.headers || {});
  let body = options.body;
  if (body && !(body instanceof FormData) && typeof body !== 'string') { headers.set('Content-Type', 'application/json'); body = JSON.stringify(body); }
  if (!path.startsWith('/api/auth/') && apiToken) headers.set('Authorization', `Bearer ${apiToken}`);
  let response = await fetch(path, { ...options, headers, body });
  if (response.status === 401 && retryAuth && !path.startsWith('/api/auth/')) {
    apiToken = '';
    localStorage.removeItem(API_TOKEN_KEY);
    throw new Error('Your local session expired. Sign in again to continue.');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.error?.message || data.detail?.message || data.detail || data.error?.code || `Request failed (${response.status})`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}
async function signInToDemoAPI() {
  const result = await apiRequest('/api/auth/demo', { method: 'POST' }, false);
  apiToken = result.access_token;
  localStorage.setItem(API_TOKEN_KEY, apiToken);
  return result.user;
}
function mapApiWorkspace(payload) {
  return {
    projects: payload.projects.map((p) => ({ id: p.id, name: p.name, type: ({forest:'Forest conservation',soil:'Soil carbon',renewable:'Renewable energy'}[p.project_type] || p.project_type), country: p.country, region: p.region, methodology: p.methodology_id || '', vintageStart: p.vintage_start || '', vintageEnd: p.vintage_end || '', registry: p.registry_name || '', registryRef: p.registry_project_ref || '', description: p.baseline_summary || '', status: p.status, demo: p.is_demo, updatedAt: p.updated_at, chainProjectId: p.chain_project_id, chainId: p.chain_id, contractAddress: p.contract_address, txHash: p.tx_hash })),
    credits: payload.batches.map((c) => ({ id: c.id, projectId: c.project_id, serial: c.serial_start, vintage: (c.vintage_start || '').slice(0,4) || 'Unknown', quantityKg: c.quantity_kg_co2e, availableKg: c.available_balance_kg, retiredKg: c.retired_balance_kg, transferredKg: c.transferred_balance_kg, registry: c.registry_name || 'Not connected', state: c.state, score: c.score, components: c.score_components, provisional: true, demo: c.is_demo, updatedAt: c.updated_at })),
    evidence: payload.evidence.map((e) => ({ id: e.id, projectId: e.project_id, name: e.filename, kind: ({document:'Document',image:'Image',data:'Data',link:'Link'}[e.evidence_type] || 'Document'), size: e.size_bytes, mime: e.content_type, uploadedAt: e.created_at, uploadedBy: e.uploaded_by, hash: e.sha256, state: e.review_state, demo: e.is_demo, anchorChainId: e.anchor_chain_id, anchorContractAddress: e.anchor_contract_address, anchorTxHash: e.anchor_tx_hash, anchorBlockNumber: e.anchor_block_number, findings: [] })),
    observations: payload.observations.map((o) => ({ id: o.id, projectId: o.project_id, source: o.source_name, signal: o.signal_type, severity: o.severity[0].toUpperCase()+o.severity.slice(1), value: o.affected_area_percent == null ? '—' : `${o.affected_area_percent}% affected area`, observedAt: o.observed_at, description: o.payload?.description || 'No description supplied.', state: o.review_state, demo: o.is_synthetic })),
    alerts: payload.alerts.map((a) => ({ id: a.id, projectId: a.project_id, observationId: a.observation_id, type: a.type, severity: a.severity, explanation: a.explanation, createdAt: a.created_at, state: a.state, demo: a.demo, reviewer: a.reviewer, reviewDecision: a.decision })),
    reviews: payload.reviews.map((r) => ({ id: r.id, targetId: r.target_id, targetType: r.target_type, finding: r.finding, state: r.state, reason: r.reason, actor: r.actor, createdAt: r.created_at, decidedAt: r.decided_at, demo: r.demo })),
    importedRecords: payload.imported_records.map((r) => ({ source: r.source, projectRef: r.projectRef, project: r.project, serial: r.serial, vintage: r.vintage, methodology: r.methodology, country: r.country, quantityKg: r.quantityKg, status: r.status, demo: r.demo })),
    events: payload.events.map((e) => ({ id: e.id, targetId: e.targetId, projectId: e.project_id, creditBatchId: e.credit_batch_id, type: e.type, actor: e.actor, reason: e.reason, at: e.at, demo: e.demo })),
    settings: payload.settings,
    noticesDismissed: localStorage.getItem('vericarb-notice-dismissed') === 'true',
    assessments: payload.assessments,
  };
}
async function refreshBackend(shouldRender = true) {
  const payload = await apiRequest('/api/demo/bootstrap');
  db = mapApiWorkspace(payload);
  backendConnected = true;
  try { blockchainStatus = await apiRequest('/api/blockchain/status'); } catch { blockchainStatus = null; }
  // This endpoint reports configuration only; it does not send an inference request.
  try { aiProviderStatus = await apiRequest('/api/ai/health'); } catch { aiProviderStatus = null; }
  if (shouldRender) renderShell();
  return payload;
}
async function initializeBackend() {
  if (!apiToken) { window.location.replace('auth.html'); return; }
  try {
    await apiRequest('/api/me');
    await refreshBackend();
  } catch (error) {
    backendConnected = false;
    console.warn('TRIPLEES API unavailable or the local session expired.', error);
    localStorage.removeItem(API_TOKEN_KEY);
    window.location.replace('auth.html');
  }
}
const projectFor = (projectId) => db.projects.find((p) => p.id === projectId);
const creditsFor = (projectId) => db.credits.filter((c) => c.projectId === projectId);
const currentPath = () => (location.hash.replace(/^#/, '') || '/dashboard');
const statusClass = (status = '') => `status-${String(status).toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
const statusTag = (status) => `<span class="status ${statusClass(status)}">${escapeHtml(status)}</span>`;
const recordLabel = (demo = true) => demo ? `<span class="tag">DEMO DATA</span>` : '';
const navigationIcons = { dashboard: 'layout-dashboard', projects: 'trees', intelligence: 'chart-no-axes-combined', investigations: 'scan-search', 'agent-activity': 'activity', 'risk-intelligence': 'shield-alert', 'investigation-reports': 'file-check-2', 'review-queue': 'clipboard-check', credits: 'layers', monitoring: 'activity', evidence: 'files', verification: 'badge-check', conflicts: 'git-compare-arrows', marketplace: 'store', alerts: 'bell', reports: 'download', explorer: 'scan-search', community: 'users', settings: 'settings' };
const uiIcon = (name, fallback = '') => window.lucide ? `<i data-lucide="${name}" aria-hidden="true"></i>` : fallback;
const renderNav = () => {
  $('#side-nav').innerHTML = NAV.map((item) => item.group ? `<div class="nav-group-label">${item.group}</div>` : `<a class="nav-link" data-nav="${item.id}" href="#${item.path}" title="${escapeHtml(item.label)}"><span class="nav-icon" aria-hidden="true">${uiIcon(navigationIcons[item.id], item.icon)}</span><span>${escapeHtml(item.label)}</span>${item.optional ? '<span class="nav-optional">Future</span>' : ''}</a>`).join('');
};

function routeInfo() {
  const parts = currentPath().split('/').filter(Boolean);
  return { page: parts[0] || 'dashboard', id: parts[1] || '' };
}
function go(path) { location.hash = `#${path}`; closeSidebar(); }
function closeSidebar() { document.body.classList.remove('sidebar-open'); }
function recordEvent(targetId, type, reason, actor = 'Jordan Demo') {
  db.events.unshift({ id: id('EVT'), targetId, type, reason, actor, at: new Date().toISOString(), demo: true });
  save();
}
function recomputeScore(credit) {
  const c = credit.components || { M: 50, V: 50, C: 50, R: 50, A: 50 };
  credit.score = Math.round(0.25 * c.M + 0.20 * c.V + 0.20 * c.C + 0.25 * c.R + 0.10 * c.A);
  credit.provisional = true;
  credit.updatedAt = new Date().toISOString();
}
function toast(message, error = false) {
  const node = document.createElement('div'); node.className = `toast${error ? ' error' : ''}`; node.textContent = message; $('#toast-root').appendChild(node); setTimeout(() => node.remove(), 3200);
}
function prepareDataViews(content) {
  $$('.tabs', content).filter((tabs) => Array.from(tabs.children).every((child) => child.tagName === 'SPAN')).forEach((tabs) => tabs.remove());
  $$('.data-table', content).forEach((table) => {
    const headers = Array.from(table.querySelectorAll('thead th'));
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const numericHeaders = /^(tracked credits|quantity|available|score|vintage)$/i;
    headers.forEach((header, column) => {
      header.scope = 'col';
      const numeric = numericHeaders.test(header.textContent.trim());
      header.classList.toggle('numeric-cell', numeric);
      rows.forEach((row) => {
        const cell = row.cells[column];
        if (cell && cell.colSpan === 1) {
          cell.dataset.label = header.textContent.trim() || 'Actions';
          cell.classList.toggle('numeric-cell', numeric);
        }
      });
    });
    const count = rows.filter((row) => row.cells.length > 1).length;
    const caption = table.createCaption();
    caption.className = 'data-table-caption';
    caption.textContent = `${count.toLocaleString()} ${count === 1 ? 'record' : 'records'}`;
    const wrapper = table.closest('.data-table-wrap');
    if (wrapper) {
      wrapper.tabIndex = 0;
      wrapper.setAttribute('role', 'region');
      wrapper.setAttribute('aria-label', `${content.querySelector('h1')?.textContent || 'Workspace'} records`);
    }
  });
  $$('input[type="search"]', content).forEach((input) => { input.spellcheck = false; });
  $$('.tabs button', content).forEach((button) => button.setAttribute('aria-pressed', String(button.classList.contains('active'))));
}
function renderShell() {
  if (!backendConnected) {
    $('#page-content').setAttribute('aria-busy', 'true');
    $('#page-content').innerHTML = '<div class="workspace-loading" role="status"><span class="loading-indicator" aria-hidden="true"></span><h1>Loading workspace…</h1><p>Fetching your project records and connection status.</p></div>';
    if (window.lucide) window.lucide.createIcons();
    return;
  }
  const { page, id: objectId } = routeInfo();
  const link = NAV.find((x) => x.id === page);
  $$('.nav-link').forEach((x) => x.classList.toggle('active', x.dataset.nav === page || (page === 'project' && x.dataset.nav === 'projects') || (page === 'verify' && x.dataset.nav === 'explorer') || (page === 'credit' && x.dataset.nav === 'credits')));
  const title = link?.label || (page === 'project' ? 'Project Passport' : page === 'credit' ? 'Credit Passport' : page === 'verify' ? 'Public Verification' : 'Workspace');
  $('#breadcrumbs').innerHTML = `<span>Workspace</span><b>/</b><strong>${escapeHtml(title)}${objectId ? ` · ${escapeHtml(objectId)}` : ''}</strong>`;
  const chainBadge = $('#blockchain-badge');
  if (chainBadge) {
    const network = blockchainStatus?.network;
    const connected = network?.state === 'x1_testnet_connected';
    chainBadge.classList.toggle('chain-online', !!connected);
    chainBadge.title = network?.error || (connected ? `X1 Maculatus · block ${network.latest_block ?? '—'} · contract ${network.contract_deployed ? 'verified' : 'not configured'}` : 'X1 Maculatus RPC unavailable or not configured');
    chainBadge.innerHTML = `<i></i> ${connected ? (network.contract_deployed ? 'X1 LIVE' : 'X1 RPC') : 'X1 OFFLINE'}`;
  }
  const sideImpact = $('#side-impact');
  if (sideImpact) sideImpact.textContent = `${formatTonnes(db.credits.reduce((sum, c) => sum + c.retiredKg, 0))}`;
  if (db.settings?.displayName) {
    const name = db.settings.displayName;
    $('.account-button b').textContent = name;
    $('.account-button small').textContent = db.settings.role || 'Workspace member';
    const sidebarUser = $('.sidebar-user');
    if (sidebarUser) {
      sidebarUser.querySelector('b').textContent = name;
      sidebarUser.querySelector('small').textContent = db.settings.role || 'Workspace member';
    }
  }
  const openAlerts = db.alerts.filter((a) => a.state === 'Open').length;
  const count = $('#alert-count'); count.textContent = openAlerts; count.hidden = openAlerts === 0;
  $('.demo-notice').classList.toggle('notice-dismissed', db.noticesDismissed);
  const content = $('#page-content');
  content.removeAttribute('aria-busy');
  content.innerHTML = renderPage(page, objectId);
  prepareDataViews(content);
  $$('.nav-link').forEach((link) => { if (link.classList.contains('active')) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current'); });
  if (window.lucide) window.lucide.createIcons();
  content.focus({ preventScroll: true });
  if (['intelligence', 'investigations', 'agent-activity', 'risk-intelligence', 'investigation-reports', 'review-queue'].includes(page)) loadIntelligencePage(page, objectId);
}
function renderPage(page, objectId) {
  const pages = { dashboard: dashboardPage, projects: projectsPage, new: newProjectPage, project: projectPage, credits: creditsPage, credit: creditPage, monitoring: monitoringPage, evidence: evidencePage, verification: verificationPage, conflicts: conflictsPage, alerts: alertsPage, reports: reportsPage, intelligence: intelligenceDashboardPage, investigations: investigationCenterPage, 'agent-activity': agentActivityPage, 'risk-intelligence': riskIntelligencePage, 'investigation-reports': investigationReportsPage, 'review-queue': findingReviewPage, explorer: explorerPage, verify: publicVerifyPage, marketplace: marketplacePage, community: communityPage, settings: settingsPage };
  return (pages[page] || notFoundPage)(objectId);
}
function pageHeader(title, subtitle, action = '') {
  return `<div class="page-head"><div><p class="eyebrow">TRIPLEES WORKSPACE</p><h1>${title}</h1><p>${subtitle}</p></div><div class="page-actions">${action}</div></div>`;
}
function cardTitle(title, subtitle = '', action = '') {
  return `<div class="card-title"><div><h2>${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ''}</div>${action}</div>`;
}
function intelStateFor(page) {
  return ({ intelligence: intelligenceState.dashboard, investigations: intelligenceState.center,
    'agent-activity': intelligenceState.activity, 'risk-intelligence': intelligenceState.risk,
    'investigation-reports': intelligenceState.reports, 'review-queue': intelligenceState.review })[page];
}
async function loadIntelligencePage(page, objectId = '') {
  const state = intelStateFor(page);
  if (!state || state.loading) return;
  const selectionPage = page === 'agent-activity' || page === 'investigation-reports';
  const requestedId = objectId || state.selectedId || '';
  if (state.loaded && (!selectionPage || state.loadedId === requestedId)) return;
  state.loaded = false;
  state.loading = true; state.error = '';
  renderShell();
  try {
    if (!backendConnected) throw new Error('Investigation screens require the authenticated TRIPLEES API connection.');
    if (page === 'intelligence') {
      const [investigations, findings, aiHealth, usage] = await Promise.all([
        apiRequest('/api/investigations?limit=200'), apiRequest('/api/findings?limit=200'),
        apiRequest('/api/ai/health'), apiRequest('/api/ai/usage?limit=200'),
      ]);
      state.investigations = investigations.items || []; state.findings = findings.items || [];
      state.aiHealth = aiHealth; state.usage = usage;
      try { state.reviewQueue = await apiRequest('/api/findings/review-queue?limit=200'); } catch { state.reviewQueue = null; }
    } else if (page === 'investigations') {
      const result = await apiRequest('/api/investigations?limit=200'); state.investigations = result.items || [];
    } else if (page === 'agent-activity') {
      const result = await apiRequest('/api/investigations?limit=200'); state.investigations = result.items || [];
      const selected = objectId || state.selectedId || state.investigations[0]?.id || '';
      state.selectedId = selected;
      if (selected) {
        const [detail, agents, audit] = await Promise.all([
          apiRequest(`/api/investigations/${encodeURIComponent(selected)}`),
          apiRequest(`/api/investigations/${encodeURIComponent(selected)}/agents`),
          apiRequest(`/api/investigations/${encodeURIComponent(selected)}/audit`),
        ]);
        state.detail = detail; state.agents = agents; state.audit = audit.items || [];
      } else { state.detail = null; state.agents = null; state.audit = []; }
      state.loadedId = selected;
    } else if (page === 'risk-intelligence') {
      const result = await apiRequest('/api/findings?limit=200'); state.findings = result.items || [];
    } else if (page === 'investigation-reports') {
      const result = await apiRequest('/api/investigations?limit=200'); state.investigations = result.items || [];
      const selected = objectId || state.selectedId || state.investigations[0]?.id || '';
      state.selectedId = selected;
      if (selected) {
        try { state.report = await apiRequest(`/api/investigations/${encodeURIComponent(selected)}/report`); state.version = state.report.version; }
        catch (error) { state.report = null; state.reportError = error.message; }
      }
      state.loadedId = selected;
    } else if (page === 'review-queue') {
      const [queue, allFindings] = await Promise.all([
        apiRequest('/api/findings/review-queue?limit=200'), apiRequest('/api/findings?limit=200'),
      ]);
      state.items = queue.items || []; state.history = (allFindings.items || []).filter((item) => item.review_decision);
    }
    state.loaded = true;
  } catch (error) { state.error = error.message || 'Could not load investigation data.'; state.loaded = true; }
  finally {
    state.loading = false;
    if (routeInfo().page === page) renderShell();
  }
}
function refreshIntelligencePage(page = routeInfo().page) {
  const state = intelStateFor(page); if (!state) return;
  state.loaded = false; state.error = ''; state.loading = false;
  renderShell();
}
function intelLoadMessage(state) {
  if (state.loading || !state.loaded) return `<div class="workspace-loading" role="status"><span class="loading-indicator" aria-hidden="true"></span><h2>Loading investigation data…</h2><p>Fetching saved records from the API.</p></div>`;
  if (state.error) return `<div class="callout danger" role="alert"><strong>Could not load this view.</strong><p>${escapeHtml(state.error)}</p><button class="btn btn-sm" data-action="refresh-intelligence">Try again</button></div>`;
  return '';
}
function intelRefreshButton() { return `<button class="btn" data-action="refresh-intelligence">${uiIcon('refresh-cw', '↻')} Refresh</button>`; }
function investigationLink(row, label = '') { return `<a href="#/agent-activity/${encodeURIComponent(row.id)}">${escapeHtml(label || row.title)}</a>`; }
function investigationStatus(row) { return statusTag(row.status.replaceAll('_', ' ')); }
function intelligenceDashboardPage() {
  const state = intelligenceState.dashboard; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Intelligence Dashboard', 'Investigation activity, evidence-backed findings, and human review status.', intelRefreshButton())}${loading}`;
  const unresolved = state.findings.filter((finding) => ['unresolved', 'requires_human_review'].includes(finding.status)).length;
  const active = state.investigations.filter((row) => ['queued', 'running', 'retry_wait', 'cancel_requested'].includes(row.status)).length;
  const severityCount = ['critical', 'high', 'medium', 'low', 'info'].map((severity) => [severity, state.findings.filter((item) => item.severity === severity).length]);
  const recent = state.investigations.slice(0, 6);
  const reviewCount = state.reviewQueue?.total ?? (['reviewer', 'admin'].includes(db.settings?.role) ? 0 : null);
  const usage = state.usage?.summary || {};
  return `${pageHeader('Intelligence Dashboard', 'Investigation activity, evidence-backed findings, and human review status.', `<a class="btn btn-primary" href="#/investigations">＋ New investigation</a>${intelRefreshButton()}`)}
    <div class="metric-grid intel-metrics">${metricCard('Investigations', state.investigations.length, `${active} active`, '⌕')}${metricCard('Unresolved findings', unresolved, 'Require reviewer attention', '⚑')}${metricCard('Review queue', reviewCount == null ? 'Role restricted' : reviewCount, 'Authorized reviewers only', '✓')}${metricCard('Model tokens', Number(usage.input_tokens || 0) + Number(usage.output_tokens || 0), 'From saved usage records', '◉')}</div>
    <div class="two-col section-space"><section class="card card-pad">${cardTitle('Findings by severity', `${state.findings.length} saved finding records`)}<div class="severity-bars">${severityCount.map(([severity, count]) => `<div class="severity-row"><span>${severityTag(severity)}</span><span class="severity-track"><i class="severity-${severity}" style="width:${state.findings.length ? Math.max(2, count / state.findings.length * 100) : 0}%"></i></span><strong>${count}</strong></div>`).join('')}</div><p class="tiny muted section-space">Counts describe persisted findings, not a calibrated portfolio risk score.</p></section>
    <section class="card card-pad">${cardTitle('AI provider configuration', 'The health check does not send an inference request')}<div class="detail-fields"><div class="detail-field"><small>Provider</small><strong>${escapeHtml(state.aiHealth?.provider === 'nebius_token_factory' ? 'Nebius Token Factory' : state.aiHealth?.provider || 'Nebius Token Factory')}</strong></div><div class="detail-field"><small>Configuration</small><strong>${state.aiHealth?.configured ? 'Configured' : 'Not configured'}</strong></div><div class="detail-field"><small>Model</small><strong>${escapeHtml(state.aiHealth?.model || 'Not available')}</strong></div><div class="detail-field"><small>Known cost</small><strong>${usage.cost_estimate_complete ? `$${Number(usage.known_cost_usd || 0).toFixed(6)}` : 'Rates not fully configured'}</strong></div></div><p class="tiny muted section-space">${Number(usage.requests || 0)} saved model request(s) · ${Number(usage.input_tokens || 0).toLocaleString()} input / ${Number(usage.output_tokens || 0).toLocaleString()} output tokens.</p></section></div>
    <section class="card card-pad section-space">${cardTitle('Recent investigations', 'Statuses reflect agent execution and configured data coverage', `<a class="table-action" href="#/investigations">Open investigation center →</a>`)}${recent.length ? `<div class="intel-list">${recent.map((row) => `<article class="intel-list-row"><div><strong>${investigationLink(row)}</strong><small>${escapeHtml(row.project_id)} · ${niceDateTime(row.created_at)}</small></div>${investigationStatus(row)}</article>`).join('')}</div>` : emptyMini('No investigations yet.', 'Create one to run the scoped agent workflow.')}</section>
    ${state.error ? `<p class="callout warning">Some optional dashboard data is unavailable: ${escapeHtml(state.error)}</p>` : ''}`;
}
function severityTag(value) { return `<span class="severity-pill severity-${escapeHtml(value)}">${escapeHtml(value)}</span>`; }
function investigationCenterPage() {
  const state = intelligenceState.center; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Investigation Center', 'Choose project evidence and a scope for a reviewable agent run.', intelRefreshButton())}${loading}`;
  const projectId = $('#intel-project-select')?.value || db.projects[0]?.id || '';
  const evidence = db.evidence.filter((item) => item.projectId === projectId);
  return `${pageHeader('Investigation Center', 'Choose project evidence and a scope for a reviewable agent run.', intelRefreshButton())}
    ${!db.projects.length ? `<div class="empty-state"><h2>Add a project first</h2><p>Investigations are attached to a project record.</p><a class="btn btn-primary" href="#/new">Create project</a></div>` : `<div class="split-layout"><section class="card card-pad">${cardTitle('Set investigation scope', 'The worker saves each agent result and the final report')}<form id="investigation-form" class="form-grid">
      <div class="field full"><label for="intel-project-select">Project *</label><select id="intel-project-select" name="project_id" required>${db.projects.map((project) => `<option value="${escapeHtml(project.id)}" ${project.id === projectId ? 'selected' : ''}>${escapeHtml(project.name)} · ${escapeHtml(project.id)}</option>`).join('')}</select></div>
      <div class="field full"><label for="intel-title">Investigation title *</label><input id="intel-title" name="title" required minlength="2" maxlength="240" placeholder="e.g. Review monitoring and registry consistency"></div>
      <div class="field full"><label for="intel-scope">Question and scope *</label><textarea id="intel-scope" name="scope" required minlength="5" maxlength="8000" placeholder="Describe what the agents should examine and what is outside scope."></textarea><small class="hint">The agents analyze only project-scoped records. Findings remain advisory until an authorized human reviews them.</small></div>
      <fieldset class="field full intel-evidence"><legend>Select evidence files</legend>${evidence.length ? evidence.map((item) => `<label class="check-row"><input type="checkbox" name="evidence_ids" value="${escapeHtml(item.id)}"><span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.kind)} · SHA-256 ${escapeHtml((item.hash || '').slice(0, 16))}${item.hash ? '…' : 'not recorded'}</small></span></label>`).join('') : `<p class="small muted">No uploaded evidence files are available for this project. The run can still inspect imported records and monitoring observations.</p>`}</fieldset>
      <fieldset class="field full intel-consent"><legend>Optional external services</legend><label class="check-row"><input type="checkbox" name="external_ai_authorized"><span><strong>Allow configured Nebius AI analysis for this run</strong><small>Selected project excerpts may be sent to the configured model. Unchecked by default; the health check does not send data.</small></span></label><label class="check-row"><input type="checkbox" name="public_research_authorized"><span><strong>Allow public-source research for this run</strong><small>Requires a research provider. No provider is configured by default.</small></span></label></fieldset>
      <div class="form-footer"><button class="btn btn-primary" type="submit">Create and queue investigation</button></div>
    </form></section><aside class="card card-pad">${cardTitle('What the workflow does')}<div class="timeline-list"><div class="timeline-entry"><strong>Evidence Analyst</strong><small>Reviews selected extraction records and claim candidates.</small></div><div class="timeline-entry"><strong>Integrity and Monitoring Analysts</strong><small>Compare project-scoped imported rows and observations.</small></div><div class="timeline-entry"><strong>Research and Independent Review</strong><small>Research needs a configured provider; the review agent checks traceability and overclaim language.</small></div><div class="timeline-entry"><strong>Report and human review</strong><small>Findings, sources, limitations and decisions are versioned and auditable.</small></div></div><div class="callout warning section-space">A finding is not proof of fraud, environmental damage, project validity, or credit certification.</div></aside></div>`}
    <section class="card card-pad section-space">${cardTitle('Existing investigations', `${state.investigations.length} visible to this account`)}${state.investigations.length ? `<div class="intel-list">${state.investigations.map((row) => `<article class="intel-list-row"><div><strong>${investigationLink(row)}</strong><small>${escapeHtml(row.project_id)} · ${escapeHtml(row.scope.slice(0, 180))}</small></div><div>${investigationStatus(row)} <a class="table-action" href="#/agent-activity/${encodeURIComponent(row.id)}">Activity</a> <a class="table-action" href="#/investigation-reports/${encodeURIComponent(row.id)}">Report</a></div></article>`).join('')}</div>` : emptyMini('No saved investigations.', 'Use the form above to create the first investigation.')}</section>`;
}
function agentActivityPage(objectId = '') {
  const state = intelligenceState.activity; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Agent Activity', 'Inspect safe execution progress, outputs, retries, and audit events.', intelRefreshButton())}${loading}`;
  if (!state.detail) return `${pageHeader('Agent Activity', 'Inspect safe execution progress, outputs, retries, and audit events.', intelRefreshButton())}${emptyMini('No investigations found.', 'Create an investigation to see persisted agent activity.')}`;
  const row = state.detail; const executions = row.executions || [];
  const actions = row.status === 'queued' || row.status === 'running' || row.status === 'retry_wait' || row.status === 'cancel_requested'
    ? `<button class="btn btn-danger" data-action="cancel-investigation" data-id="${escapeHtml(row.id)}">Request cancellation</button>`
    : ['failed', 'partial'].includes(row.status) ? `<button class="btn btn-primary" data-action="retry-investigation" data-id="${escapeHtml(row.id)}">Retry incomplete agents</button>`
      : ['draft', 'completed_with_limitations'].includes(row.status) ? `<button class="btn btn-primary" data-action="run-investigation" data-id="${escapeHtml(row.id)}">Queue run</button>` : '';
  return `${pageHeader('Agent Activity', 'Inspect safe execution progress, outputs, retries, and audit events.', `${actions}${intelRefreshButton()}`)}
    <section class="card card-pad"><div class="toolbar"><label class="field"><span class="sr-only">Select investigation</span><select id="intel-activity-select" aria-label="Select investigation">${state.investigations.map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === row.id ? 'selected' : ''}>${escapeHtml(item.title)} · ${escapeHtml(item.id)}</option>`).join('')}</select></label>${investigationStatus(row)}<span class="small muted">Attempt ${row.attempt_count || 0}</span></div><h2>${escapeHtml(row.title)}</h2><p class="small">${escapeHtml(row.scope)}</p><div class="detail-fields">${detailField('Project', row.project_id)}${detailField('Created', niceDateTime(row.created_at))}${detailField('Started', niceDateTime(row.started_at))}${detailField('Completed', niceDateTime(row.completed_at))}</div>${row.failure_summary ? `<div class="callout warning section-space">${escapeHtml(row.failure_summary)}</div>` : ''}</section>
    <section class="card card-pad section-space">${cardTitle('Agent executions', 'Task summaries and structured outputs only; hidden reasoning is not shown')}${executions.length ? `<div class="agent-execution-list">${executions.map((execution) => `<article class="agent-execution"><div class="agent-execution-head"><div><h3>${escapeHtml(execution.agent_key.replaceAll('_', ' '))}</h3><p>${escapeHtml(execution.task_summary)}</p></div>${statusTag(execution.status.replaceAll('_', ' '))}</div><small>${niceDateTime(execution.started_at)}${execution.completed_at ? ` · ${niceDateTime(execution.completed_at)}` : ''} · Attempt ${execution.attempt_number}</small>${execution.error_code ? `<p class="callout warning section-space">Safe error code: <code>${escapeHtml(execution.error_code)}</code></p>` : ''}${execution.output ? `<div class="agent-output section-space"><strong>${escapeHtml(execution.output.summary)}</strong>${execution.output.findings?.length ? `<ul>${execution.output.findings.slice(0, 5).map((finding) => `<li>${severityTag(finding.severity)} ${escapeHtml(finding.title)}</li>`).join('')}</ul>` : ''}${execution.output.limitations?.length ? `<details><summary>Limitations (${execution.output.limitations.length})</summary><ul>${execution.output.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></details>` : ''}</div>` : ''}</article>`).join('')}</div>` : emptyMini('No agent executions yet.', 'Queue this investigation to start the worker.')}</section>
    <section class="card card-pad section-space">${cardTitle('Audit history', 'Persistent lifecycle events')}<div class="timeline-list">${(state.audit || []).slice().reverse().map((event) => `<div class="timeline-entry"><strong>${escapeHtml(event.event_type.replaceAll('_', ' '))}</strong><small>${niceDateTime(event.created_at)}${event.details?.agent_key ? ` · ${escapeHtml(event.details.agent_key)}` : ''}${event.details?.status ? ` · ${escapeHtml(event.details.status)}` : ''}</small></div>`).join('') || '<p class="small muted">No audit events are available.</p>'}</div></section>`;
}
function findingCard(finding, { review = false } = {}) {
  const refs = [...(finding.evidence || []).map((source) => `<span class="citation-chip">Evidence · ${escapeHtml(source.title)} · ${escapeHtml((source.sha256 || '').slice(0, 12))}</span>`), ...(finding.sources || []).map((source) => source.url ? `<a class="citation-chip" href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)} ↗</a>` : `<span class="citation-chip">${escapeHtml(source.kind.replaceAll('_', ' '))} · ${escapeHtml(source.title)} · ${escapeHtml(source.id)}</span>`)];
  const actions = review && ['reviewer', 'admin'].includes(db.settings?.role) ? `<div class="alert-actions"><button class="btn btn-sm btn-soft" data-action="finding-review" data-id="${escapeHtml(finding.id)}" data-decision="confirmed">Confirm finding</button><button class="btn btn-sm" data-action="finding-review" data-id="${escapeHtml(finding.id)}" data-decision="needs_more_evidence">Request more evidence</button><button class="btn btn-sm btn-danger" data-action="finding-review" data-id="${escapeHtml(finding.id)}" data-decision="rejected">Reject finding</button></div>` : '';
  return `<article class="finding-card"><div class="finding-card-head"><div>${severityTag(finding.severity)} <span class="tag">${escapeHtml(finding.category.replaceAll('_', ' '))}</span> ${statusTag(finding.status.replaceAll('_', ' '))}</div><small>${escapeHtml(finding.investigation_title || finding.investigation_id || '')} · ${niceDateTime(finding.created_at)}</small></div><h3>${escapeHtml(finding.title)}</h3><p>${escapeHtml(finding.description)}</p>${finding.claim ? `<p><strong>Claim:</strong> ${escapeHtml(finding.claim)}</p>` : ''}${finding.observed_value ? `<p><strong>Observed value:</strong> ${escapeHtml(finding.observed_value)}</p>` : ''}<div class="finding-meta"><span>Basis: ${escapeHtml(finding.basis.replaceAll('_', ' '))}</span><span>Agent confidence estimate: ${Math.round(Number(finding.confidence) * 100)}%</span></div><p class="tiny muted">Confidence is an estimate, not a calibrated probability.</p>${finding.recommendation ? `<div class="callout info">Recommendation: ${escapeHtml(finding.recommendation)}</div>` : ''}<div class="citation-list">${refs.join('') || `<span class="callout warning">No material citation is attached. This finding remains ${escapeHtml(finding.status.replaceAll('_', ' '))}.</span>`}</div>${finding.review_decision ? `<div class="review-result"><strong>Latest reviewer decision: ${escapeHtml(finding.review_decision.replaceAll('_', ' '))}</strong><p>${escapeHtml(finding.review_reason || '')}</p><small>${escapeHtml(finding.reviewer_id || '')} · ${niceDateTime(finding.reviewed_at)}</small></div>` : ''}${actions}</article>`;
}
function riskIntelligencePage() {
  const state = intelligenceState.risk; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Risk Intelligence', 'Filter source-linked findings and keep uncertainty visible.', intelRefreshButton())}${loading}`;
  const query = riskFilters.query.toLowerCase().trim();
  const findings = state.findings.filter((item) => (riskFilters.severity === 'All' || item.severity === riskFilters.severity.toLowerCase())
    && (riskFilters.status === 'All' || item.status === riskFilters.status)
    && (!query || `${item.title} ${item.description} ${item.category} ${item.project_id}`.toLowerCase().includes(query)));
  const severities = ['critical', 'high', 'medium', 'low', 'info'];
  return `${pageHeader('Risk Intelligence', 'Inspect findings by severity, category, citations, and reviewer status.', intelRefreshButton())}
    <div class="callout warning">Signals and agent findings are not proof of fraud, environmental damage, invalid credits, or certification. Review source records before making decisions.</div>
    <section class="card card-pad section-space"><div class="toolbar"><label class="field"><span class="sr-only">Search findings</span><input id="risk-search" type="search" value="${escapeHtml(riskFilters.query)}" placeholder="Search findings, claims, or project IDs" aria-label="Search findings"></label><label class="field"><span class="sr-only">Severity</span><select id="risk-severity" aria-label="Filter by severity"><option>All</option>${severities.map((value) => `<option value="${value}" ${riskFilters.severity.toLowerCase() === value ? 'selected' : ''}>${value[0].toUpperCase() + value.slice(1)}</option>`).join('')}</select></label><label class="field"><span class="sr-only">Finding status</span><select id="risk-status" aria-label="Filter by finding status"><option>All</option>${['requires_human_review', 'hypothesis', 'unresolved'].map((value) => `<option value="${value}" ${riskFilters.status === value ? 'selected' : ''}>${value.replaceAll('_', ' ')}</option>`).join('')}</select></label><span class="tag">${findings.length} / ${state.findings.length} FINDINGS</span></div><div id="risk-findings-list" class="finding-list">${findings.map((item) => findingCard(item)).join('') || emptyMini('No findings match these filters.', state.findings.length ? 'Change the filters to see other records.' : 'Completed investigations will appear here.')}</div></section>`;
}
async function selectInvestigationReport(investigationId, version = null) {
  const state = intelligenceState.reports; state.selectedId = investigationId; state.loadedId = investigationId; state.version = version; state.loadingReport = true; state.report = null; state.reportError = '';
  renderShell();
  try {
    const suffix = version ? `?version=${encodeURIComponent(version)}` : '';
    state.report = await apiRequest(`/api/investigations/${encodeURIComponent(investigationId)}/report${suffix}`);
    state.version = state.report.version; state.loaded = true;
  } catch (error) { state.reportError = error.message; }
  finally { state.loadingReport = false; if (routeInfo().page === 'investigation-reports') renderShell(); }
}
function investigationReportsPage(objectId = '') {
  const state = intelligenceState.reports; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Investigation Reports', 'Read versioned reports with citations, uncertainty, and human review history.', intelRefreshButton())}${loading}`;
  const selected = objectId || state.selectedId || state.investigations[0]?.id || '';
  const report = state.report;
  const versions = report?.available_versions || [];
  const actions = report ? `<button class="btn" data-action="download-investigation-report">Download JSON</button><button class="btn" data-action="print-investigation-report">Print report</button>` : '';
  return `${pageHeader('Investigation Reports', 'Read versioned reports with citations, uncertainty, and human review history.', `${actions}${intelRefreshButton()}`)}
    <section class="card card-pad"><div class="toolbar"><label class="field"><span class="sr-only">Investigation</span><select id="intel-report-select" aria-label="Select investigation">${state.investigations.map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === selected ? 'selected' : ''}>${escapeHtml(item.title)} · ${escapeHtml(item.id)}</option>`).join('')}</select></label>${report ? `<label class="field"><span class="sr-only">Report version</span><select id="intel-report-version" aria-label="Select report version">${versions.map((version) => `<option value="${version}" ${version === report.version ? 'selected' : ''}>Version ${version}</option>`).join('')}</select></label>` : ''}</div>${state.loadingReport ? `<div class="workspace-loading" role="status"><span class="loading-indicator"></span><p>Loading report version…</p></div>` : state.reportError ? `<div class="callout info">${escapeHtml(state.reportError)} ${selected ? 'This investigation may still be running.' : ''}</div>` : ''}</section>
    ${report ? investigationReportContent(report) : state.investigations.length ? '' : emptyMini('No investigations yet.', 'Create an investigation before viewing reports.')}`;
}
function investigationReportContent(report) {
  const content = report.content || {}; const inv = content.investigation || {};
  return `<article class="report-document section-space" id="investigation-report-document"><header class="report-document-head"><div><p class="eyebrow">TRIPLEES INVESTIGATION REPORT · VERSION ${report.version}</p><h2>${escapeHtml(inv.title || 'Investigation report')}</h2><p>${escapeHtml(inv.project_name || inv.project_id || '')} · ${escapeHtml(report.status.replaceAll('_', ' '))} · ${niceDateTime(report.created_at)}</p></div><span class="tag">${escapeHtml(report.anchor?.status ? report.anchor.status.replaceAll('_', ' ').toUpperCase() : 'NOT ANCHORED TO X1')}</span></header>
    <div class="report-summary"><h3>Executive summary</h3><p>${escapeHtml(report.summary)}</p><p><strong>Scope:</strong> ${escapeHtml(inv.scope || 'Not recorded')}</p><p><strong>Method:</strong> Structured outputs from the configured agents and supplied project records. No independent external facts are implied.</p></div>
    ${reportAnchorPanel(report)}
    <section class="section-space">${cardTitle(`Findings (${content.findings?.length || 0})`, 'Severity, citations, confidence, and reviewer state')}${content.findings?.length ? `<div class="finding-list">${content.findings.map((finding) => findingCard(finding)).join('')}</div>` : emptyMini('No findings saved.', 'Agent outputs did not contain structured findings.')}</section>
    <div class="two-col section-space"><section class="card card-pad">${cardTitle('Agent execution summary')}<div class="timeline-list">${(content.agents || []).map((agent) => `<div class="timeline-entry"><strong>${escapeHtml(agent.agent_key.replaceAll('_', ' '))} · ${escapeHtml(agent.status.replaceAll('_', ' '))}</strong><small>${niceDateTime(agent.started_at)}${agent.error_code ? ` · ${escapeHtml(agent.error_code)}` : ''}</small></div>`).join('') || '<p class="small muted">No executions recorded.</p>'}</div></section><section class="card card-pad">${cardTitle('Source references', `${content.sources?.length || 0} public source(s)`)}<div class="source-list">${(content.sources || []).map((source) => `<a class="source-row" href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer"><span class="source-status"></span><span><strong>${escapeHtml(source.title)}</strong><small>${escapeHtml(source.publisher || source.domain || '')} · Retrieved ${niceDateTime(source.retrieved_at)}</small></span><span>Open ↗</span></a>`).join('') || '<p class="small muted">No public source references were collected.</p>'}</div></section></div>
    <section class="card card-pad section-space">${cardTitle(`Limitations and unresolved questions (${content.limitations?.length || 0})`)}${content.limitations?.length ? `<ul class="limitation-list">${content.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : '<p class="small">No additional limitations were recorded by the agents.</p>'}<p class="tiny muted">${escapeHtml(content.confidence_note || 'Confidence is an estimate, not a calibrated probability.')}</p><p class="tiny muted">${escapeHtml(content.human_review_note || '')}</p></section>
    <footer class="report-document-foot"><span>Report version ${report.version} · ${escapeHtml(report.status.replaceAll('_', ' '))}</span><span>Report contents remain off-chain.</span></footer></article>`;
}
function reportAnchorPanel(report) {
  const anchor = report.anchor; const digest = report.commitment?.sha256 || '';
  const reviewer = ['reviewer', 'admin'].includes(db.settings?.role);
  const network = blockchainStatus?.network || {};
  const signerReady = blockchainStatus?.wallets?.some((wallet) => wallet.role === 'reviewer' && wallet.configured && wallet.address);
  const destinationReady = network.report_anchor_contract_deployed && signerReady;
  const shareLink = anchor?.id ? `<a class="btn btn-sm" href="/report-verify.html?id=${encodeURIComponent(anchor.id)}" target="_blank" rel="noopener noreferrer">Public verification view ↗</a>` : '';
  let action = '';
  if (!anchor && reviewer) action = `<button class="btn btn-primary" data-action="approve-report-anchor" data-id="${escapeHtml(report.id)}" data-investigation-id="${escapeHtml(report.investigation_id)}">Approve digest for anchoring</button>`;
  else if (!anchor) action = '<p class="tiny muted">A reviewer must approve the digest before X1 submission can be prepared.</p>';
  else if (anchor.status === 'approved' && reviewer) action = `<button class="btn btn-primary" data-action="submit-report-anchor" data-id="${escapeHtml(anchor.id)}" ${destinationReady ? '' : 'disabled title="Configure the separate report-anchor contract and reviewer signer first"'}>Submit digest to X1</button>${!destinationReady ? '<small class="muted">X1 report contract and reviewer signer are not both configured.</small>' : ''}`;
  else if (['submitting', 'submitted', 'submission_unknown'].includes(anchor.status) && reviewer) action = `<button class="btn" data-action="reconcile-report-anchor" data-id="${escapeHtml(anchor.id)}">Check transaction status</button>`;
  else if (anchor.status === 'failed' && reviewer) action = `<button class="btn btn-primary" data-action="submit-report-anchor" data-id="${escapeHtml(anchor.id)}" ${destinationReady ? '' : 'disabled'}>Confirm and retry X1 submission</button>`;
  const tx = anchor?.transaction_hash ? `<p class="tiny">Transaction <a target="_blank" rel="noopener noreferrer" href="${escapeHtml(networkExplorer())}/tx/${encodeURIComponent(anchor.transaction_hash)}">${escapeHtml(anchor.transaction_hash)} ↗</a> · block ${anchor.block_number ?? 'pending'}</p>` : '';
  return `<section class="report-anchor-panel"><div><p class="eyebrow">REPORT COMMITMENT</p><h3>SHA-256 digest · version ${report.version}</h3><p class="report-digest"><code>${escapeHtml(digest)}</code><button class="table-action" data-action="copy" data-copy="${escapeHtml(digest)}">Copy digest</button></p><small>Canonicalization: ${escapeHtml(report.commitment?.canonicalization || 'Not available')}. Only this digest and a random reference are submitted; report contents stay off-chain.</small></div><div class="report-anchor-actions">${action}${shareLink}</div>${anchor ? `<p class="tiny">Approval: ${escapeHtml(anchor.approved_by || '')} · ${niceDateTime(anchor.approved_at)} · ${escapeHtml(anchor.approval_reason || '')}</p>${anchor.failure_summary ? `<p class="callout warning">${escapeHtml(anchor.failure_summary)}</p>` : ''}${tx}` : ''}<p class="tiny muted">An X1 anchor proves that a digest was recorded. It does not establish report accuracy, project validity, or credit certification.</p></section>`;
}
function findingReviewPage() {
  const state = intelligenceState.review; const loading = intelLoadMessage(state);
  if (loading) return `${pageHeader('Review Queue', 'Authorized reviewers can record a decision with a reason and preserve its report version.', intelRefreshButton())}${loading}`;
  if (!['reviewer', 'admin'].includes(db.settings?.role)) return `${pageHeader('Review Queue', 'Authorized reviewers can record a decision with a reason and preserve its report version.', '')}<div class="callout warning">This account does not have the reviewer role. Findings remain readable in Risk Intelligence, but decisions are restricted.</div>`;
  return `${pageHeader('Review Queue', 'Inspect citations before deciding. Each decision requires a reason and creates a new report version.', intelRefreshButton())}
    <div class="callout warning">A reviewer decision records a human assessment of a finding. It does not certify credits or establish an environmental or legal fact.</div>
    <section class="card card-pad section-space">${cardTitle('Awaiting review', `${state.items.length} finding(s)`, '<span class="tag">REVIEWER ACCESS</span>')}${state.items.length ? `<div class="finding-list">${state.items.map((item) => findingCard(item, { review: true })).join('')}</div>` : emptyMini('Review queue is clear.', 'New findings from completed investigations will appear here.')}</section>
    <section class="card card-pad section-space">${cardTitle('Recent human decisions', `${state.history.length} reviewed finding(s)`)}${state.history.length ? `<div class="finding-list">${state.history.slice(0, 30).map((item) => findingCard(item)).join('')}</div>` : emptyMini('No decisions recorded yet.', 'Reviewer actions remain attached to their finding and report versions.')}</section>`;
}
function projectCard(project) {
  const src = project.type.toLowerCase().includes('wind') ? 'https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=250&q=70' : 'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=250&q=70';
  const qty = db.credits.filter((c) => c.projectId === project.id).reduce((sum, c) => sum + c.quantityKg, 0);
  return `<article class="project-mini"><img class="project-thumb" src="${src}" alt="" loading="lazy"><div class="project-mini-main"><h3>${escapeHtml(project.name)}</h3><p>${escapeHtml(project.country)}, ${escapeHtml(project.region)} · ${escapeHtml(project.type)}</p><div class="project-mini-meta"><span class="chip">${formatTonnes(qty)} tracked</span>${statusTag(project.status)}${recordLabel(project.demo)}</div></div><a class="table-action" href="#/project/${encodeURIComponent(project.id)}" aria-label="View ${escapeHtml(project.name)}">View</a></article>`;
}
function dashboardPage() {
  const owned = db.credits.reduce((sum, c) => sum + c.availableKg, 0);
  const retired = db.credits.reduce((sum, c) => sum + c.retiredKg, 0);
  const atRisk = db.credits.filter((c) => c.state === 'At Risk').length;
  const openReviews = db.reviews.filter((r) => r.state === 'Pending').length;
  const pending = db.evidence.filter((e) => e.state === 'Needs human review' || e.state === 'Assessment ready').length;
  return `${pageHeader('Workspace overview', 'Project provenance, credit balances, and the work that needs your attention.', `<a class="btn" href="#/reports">${uiIcon('download', '↓')} Reports</a><a class="btn btn-primary" href="#/new">${uiIcon('plus', '+')} New project</a>`)}
    <section class="workspace-summary"><div class="summary-copy"><span class="summary-kicker">CLIMATE INTEGRITY / DEMO WORKSPACE</span><h2>Portfolio status</h2><p>${atRisk ? `${atRisk} at-risk ${atRisk === 1 ? 'batch needs' : 'batches need'} a closer look.` : 'No at-risk batches in this workspace.'} ${openReviews + pending} items awaiting human review.</p><a href="#/verification" class="summary-action">Open review queue ${uiIcon('arrow-up-right', '↗')}</a></div><div class="summary-image" role="img" aria-label="Forest canopy in the demo workspace"></div></section>
    <div class="metric-grid">
      ${metricCard('My Projects', db.projects.length, 'Synthetic workspace records', '▧')}
      ${metricCard('Credits Owned', formatTonnes(owned), 'Available demo balance', '◈')}
      ${metricCard('Credits Retired', formatTonnes(retired), 'Historical event preserved', '↗')}
      ${metricCard('Open Review Items', openReviews + pending, 'Human review required', '⌁')}
    </div>
    <div class="quick-grid">
      ${quickCard('Register Project', 'Create a database project record', '＋', '/new')}${quickCard('Upload Evidence', 'Store off-chain and hash on the server', '▤', '/evidence')}${quickCard('View Credits', 'Inspect demo batches', '◈', '/credits')}${quickCard('Monitor Impact', 'Review synthetic signals', '⌁', '/monitoring')}
    </div>
    <div class="bottom-grid dashboard-review"><section class="card card-pad">${cardTitle('Needs Attention', 'Current demo workspace actions')}<div class="activity-list">${attentionRows()}</div></section><section class="card card-pad">${cardTitle('Recent Activity', 'Append-only local demo event history')}<div class="activity-list">${db.events.slice(0, 4).map(activityItem).join('') || emptyMini('No activity yet.', 'New actions will be added here.')}</div></section></div>
    <div class="dash-grid">
      <section class="card card-pad">${cardTitle('Your Projects', 'Demo project records', `<a class="table-action" href="#/projects">View all →</a>`)}<div class="project-stack">${db.projects.slice(0, 3).map(projectCard).join('') || emptyMini('No projects yet.', 'Register a project to start a local record.')}</div></section>
      <section class="card card-pad">${cardTitle('Credit balances', 'Available and retired balances from workspace batch records', '<span class="chip">DEMO RECORDS</span>')}<div class="balance-totals">${miniMetric(formatTonnes(owned), 'Available')}${miniMetric(formatTonnes(retired), 'Retired')}${miniMetric(`${atRisk}`, 'At risk batches')}</div>${activityChart()}<div class="chart-legend"><span><i class="legend-dot"></i>Available balance</span><span><i class="legend-dot alt"></i>Retired history</span></div></section>
      <section class="card card-pad project-locations">${cardTitle('Project locations', 'Locations supplied in project records; boundaries are not verified')}<div class="location-list">${db.projects.map((project) => `<a class="location-row" href="#/project/${encodeURIComponent(project.id)}"><span class="location-symbol">${uiIcon('map-pin', '⌖')}</span><span><strong>${escapeHtml(project.name)}</strong><small>${escapeHtml([project.country, project.region].filter(Boolean).join(' / ') || 'Location not supplied')}</small></span>${statusTag(project.status)}</a>`).join('') || emptyMini('No project locations.', 'Locations appear when project records are added.')}</div></section>
    </div>
    ${blockchainActivity()}`;
}
function blockchainActivity() {
  const network = blockchainStatus?.network;
  const transactions = blockchainStatus?.transactions || [];
  const live = network?.state === 'x1_testnet_connected';
  const explorer = network?.explorer_url || 'https://maculatus-scan.x1eco.com';
  return `<section class="card card-pad blockchain-activity">${cardTitle('Blockchain Activity', 'Live network check · on-chain records are distinct from demo database entries', `<a class="btn btn-sm" href="${escapeHtml(explorer)}" target="_blank" rel="noopener">Open X1 Explorer ↗</a>`)}<div class="chain-overview"><div><small>NETWORK</small><strong>${escapeHtml(network?.network_name || 'X1 EcoChain Testnet (Maculatus)')}</strong></div><div><small>CHAIN ID</small><strong>${network?.actual_chain_id ?? network?.expected_chain_id ?? '—'}</strong></div><div><small>RPC</small><strong>${live ? `Connected · block ${network.latest_block ?? '—'}` : escapeHtml(network?.state || 'Checking')}</strong></div><div><small>REGISTRY CONTRACT</small><strong>${network?.contract_deployed ? escapeHtml(network.contract_address) : 'Not deployed/configured'}</strong></div></div>${transactions.length ? `<div class="chain-transactions">${transactions.map((tx) => `<div class="chain-transaction"><span class="status status-confirmed">Confirmed</span><strong>${escapeHtml(tx.action.replaceAll('_',' ').toLowerCase())}</strong><code>${escapeHtml(tx.transaction_hash)}</code><a href="${escapeHtml(tx.explorer_url)}" target="_blank" rel="noopener">View ↗</a></div>`).join('')}</div>` : `<p class="chain-empty">${live ? 'No confirmed TRIPLEES transactions recorded yet.' : escapeHtml(network?.error || 'Waiting for the X1 network check.')}</p>`}<small class="chain-checked">Last checked ${escapeHtml(network?.checked_at || 'not yet checked')}. Demo and local events are not represented as chain transactions.</small></section>`;
}
function metricCard(label, value, foot, icon) { const metricIcons = { 'My Projects': 'trees', 'Credits Owned': 'layers', 'Credits Retired': 'circle-check', 'Open Review Items': 'clipboard-check' }; const displayValue = String(value).endsWith(' tCO₂e') ? `${escapeHtml(String(value).replace(' tCO₂e', ''))}<span class="metric-unit">tCO₂e</span>` : escapeHtml(value); return `<article class="card metric-card"><div class="metric-label"><span>${label}</span><span class="metric-icon">${uiIcon(metricIcons[label] || 'chart-no-axes-combined', icon)}</span></div><div class="metric-value">${displayValue}</div><div class="metric-foot">${foot} · DEMO</div></article>`; }
function miniMetric(value, label) { return `<div class="mini-metric"><strong>${value}</strong><small>${label}</small></div>`; }
function quickCard(title, desc, icon, path) { const icons = { '/new': 'plus', '/evidence': 'upload', '/credits': 'layers', '/monitoring': 'activity', '/marketplace': 'store' }; return `<button class="quick-card" data-route="${path}"><span class="quick-icon">${uiIcon(icons[path], icon)}</span><span><strong>${title}</strong><small>${desc}</small></span>${uiIcon('arrow-up-right')}</button>`; }
function emptyMini(title, copy) { return `<div class="empty-state" style="padding:18px"><h3>${title}</h3><p>${copy}</p></div>`; }
function activityItem(event) { return `<div class="activity-item"><span class="activity-bullet">${event.type.toLowerCase().includes('risk') ? '!' : '✓'}</span><span><strong>${escapeHtml(event.type)} <span class="tag">DEMO</span></strong><small>${escapeHtml(event.targetId)} · ${escapeHtml(event.reason)}</small></span><time class="activity-time">${niceDate(event.at)}</time></div>`; }
function attentionRows() { const rows = [];
  db.alerts.filter((a) => a.state === 'Open').slice(0, 2).forEach((a) => rows.push(`<div class="activity-item"><span class="activity-bullet">!</span><span><strong>${escapeHtml(a.type)} · ${escapeHtml(a.severity)}</strong><small>${escapeHtml(projectFor(a.projectId)?.name || a.projectId)} · human review needed</small></span><a class="table-action" href="#/alerts">Review</a></div>`));
  db.reviews.filter((r) => r.state === 'Pending').slice(0, 2).forEach((r) => rows.push(`<div class="activity-item"><span class="activity-bullet">⌕</span><span><strong>${escapeHtml(r.finding)}</strong><small>${escapeHtml(r.targetId)} · pending reviewer decision</small></span><a class="table-action" href="#/verification">Open</a></div>`));
  return rows.length ? rows.join('') : emptyMini('Nothing needs review.', 'New evidence or observations will appear here.');
}
function activityChart() {
  const batches = db.credits.slice(0, 5);
  const maximum = Math.max(1, ...batches.map((batch) => Number(batch.availableKg || 0) + Number(batch.retiredKg || 0)));
  return `<div class="balance-chart">${batches.map((batch) => `<a class="balance-row" href="#/credit/${encodeURIComponent(batch.id)}"><span class="balance-label"><strong>${escapeHtml(batch.id)}</strong><small>${formatTonnes(batch.availableKg)} available / ${formatTonnes(batch.retiredKg)} retired</small></span><span class="balance-track" aria-hidden="true"><i style="width:${Number(batch.availableKg || 0) / maximum * 100}%"></i><i class="retired" style="width:${Number(batch.retiredKg || 0) / maximum * 100}%"></i></span></a>`).join('') || emptyMini('No batch balances.', 'Balances appear when credit batches are added.')}</div>${db.credits.length > 5 ? '<a class="table-action" href="#/credits">View all batch balances →</a>' : ''}`;
}

function projectsPage() {
  const filtered = db.projects.filter((p) => selectedProjectFilter === 'All' || p.status.toLowerCase().replaceAll(' ', '-') === selectedProjectFilter.toLowerCase().replaceAll(' ', '-'));
  return `${pageHeader('Projects', 'Create and manage climate project records in this local demo workspace.', '<a class="btn btn-primary" href="#/new">＋ New Project</a>')}
    <div class="toolbar"><input id="project-search" type="search" placeholder="Search projects or references…" aria-label="Search projects"><select id="project-filter" aria-label="Filter projects by status">${['All', 'Active', 'At Risk', 'Under Review', 'Draft'].map((x) => `<option${selectedProjectFilter === x ? ' selected' : ''}>${x}</option>`).join('')}</select><span class="tag">${db.projects.length} DEMO RECORDS</span></div>
    <section class="card card-pad"><div class="data-table-wrap"><table class="data-table"><thead><tr><th>PROJECT</th><th>TYPE / LOCATION</th><th>TRACKED CREDITS</th><th>STATUS</th><th>UPDATED</th><th></th></tr></thead><tbody id="project-rows">${filtered.map(projectRow).join('') || `<tr><td colspan="6">${emptyMini('No matching projects.', 'Change the filters or create a new project.')}</td></tr>`}</tbody></table></div></section>
    <section class="card card-pad section-space">${cardTitle('Data coverage', 'Scope of local project records')}<div class="callout info">Project records are stored in the local TRIPLEES database. Project registration does not certify a project or confirm its climate outcome. External registries and geospatial sources are not connected.</div></section>`;
}
function projectRow(project) {
  const total = creditsFor(project.id).reduce((s, c) => s + c.quantityKg, 0);
  return `<tr><td><a href="#/project/${encodeURIComponent(project.id)}"><strong>${escapeHtml(project.name)}</strong><small>${escapeHtml(project.id)} · ${project.demo ? 'DEMO DATA' : 'Local draft'}</small></a></td><td>${escapeHtml(project.type)}<small>${escapeHtml(project.country)}, ${escapeHtml(project.region)}</small></td><td>${formatTonnes(total)}</td><td>${statusTag(project.status)}</td><td>${niceDate(project.updatedAt)}</td><td><a class="table-action" href="#/project/${encodeURIComponent(project.id)}">Open →</a></td></tr>`;
}
function newProjectPage() {
  return `${pageHeader('Register a Project', 'Create a local project record. Registration is not an external certification.', '<a class="btn" href="#/projects">← Projects</a>')}
    <div class="split-layout"><form id="project-form" class="card card-pad"><div class="card-title"><div><h2>Project details</h2><p>Required fields are marked with an asterisk.</p></div><span class="tag">LOCAL DRAFT</span></div><div class="form-grid">
      ${field('project-name', 'Project name *', 'text', 'e.g. Demo Forest Restoration')}
      <div class="field"><label for="project-type">Project type *</label><select id="project-type" name="type" required><option value="">Choose a sector</option><option>Forest conservation</option><option>Reforestation</option><option>Soil carbon</option><option>Renewable energy</option><option>Other</option></select></div>
      ${field('project-country', 'Country *', 'text', 'Country')}${field('project-region', 'Region', 'text', 'Region or area')}
      ${field('project-method', 'Methodology', 'text', 'Methodology identifier')}${field('project-registry', 'Registry of origin', 'text', 'Only if applicable')}
      ${field('project-vintage-start', 'Vintage start', 'date', '')}${field('project-vintage-end', 'Vintage end', 'date', '')}
      ${field('project-registry-ref', 'Registry project reference', 'text', 'Optional external reference')}
      <div class="field full"><label for="project-description">Project description / baseline summary</label><textarea name="description" id="project-description" placeholder="Describe the project and evidence context."></textarea><small class="hint">Avoid entering personal or confidential information in this local demo.</small></div>
    </div><div class="form-footer"><a class="btn" href="#/projects">Cancel</a><button class="btn btn-primary" type="submit">Save local draft</button></div></form>
      <aside class="card card-pad">${cardTitle('Before you begin')}<div class="callout warning">A project record is not a verified or certified climate project. Registry and boundary checks are unavailable until a real integration is configured.</div><div class="section-space"><h3>What happens next?</h3><div class="timeline-list"><div class="timeline-entry"><strong>Local project ID is assigned</strong><small>The API creates a demo identifier.</small></div><div class="timeline-entry"><strong>Add evidence references</strong><small>Files are stored off-chain; the API computes each SHA-256 digest.</small></div><div class="timeline-entry"><strong>Request human review</strong><small>Reviewer decisions are stored in the database with audit history.</small></div></div></div></aside></div>`;
}
function field(idName, label, type = 'text', placeholder = '') { return `<div class="field"><label for="${idName}">${label}</label><input id="${idName}" name="${idName.replace('project-', '')}" type="${type}" ${placeholder ? `placeholder="${placeholder}"` : ''} ${label.endsWith('*') ? 'required' : ''}></div>`; }

function projectPage(projectId) {
  const project = projectFor(decodeURIComponent(projectId));
  if (!project) return notFoundPage();
  const tabs = ['Overview', 'Evidence', 'Monitoring', 'Credits', 'History'];
  const relatedEvidence = db.evidence.filter((e) => e.projectId === project.id);
  const relatedObs = db.observations.filter((e) => e.projectId === project.id);
  const relatedCredits = creditsFor(project.id);
  const chainReady = blockchainStatus?.network?.contract_deployed === true && blockchainStatus?.wallets?.some((wallet) => wallet.role === 'registrar' && wallet.configured && wallet.address);
  const events = db.events.filter((e) => e.targetId === project.id || relatedCredits.some((c) => c.id === e.targetId));
  let content = '';
  if (activeProjectTab === 'Evidence') content = relatedEvidence.map((e) => evidenceRow(e)).join('') || emptyMini('No evidence attached.', 'Use the Evidence page to add a file hash and metadata.');
  else if (activeProjectTab === 'Monitoring') content = relatedObs.map(observationRow).join('') || emptyMini('No observations.', 'Synthetic or configured source observations will appear here.');
  else if (activeProjectTab === 'Credits') content = relatedCredits.map((c) => creditRow(c)).join('') || emptyMini('No credit batches.', 'Batch registration is a separate lifecycle action.');
  else if (activeProjectTab === 'History') content = events.map(activityItem).join('') || emptyMini('No events.', 'Local project history is append-only.');
  else content = `<div class="detail-fields">${detailField('Project ID', project.id)}${detailField('On-chain project ID', project.chainProjectId || 'Not registered on-chain')}${detailField('Chain registration', project.txHash ? `Confirmed · chain ${project.chainId}` : 'Stored in TRIPLEES database only')}${detailField('Contract address', project.contractAddress || 'Not configured')}${detailField('Project type', project.type)}${detailField('Country', project.country)}${detailField('Region', project.region)}${detailField('Methodology', project.methodology || 'Not provided')}${detailField('Vintage', `${project.vintageStart || '—'} to ${project.vintageEnd || '—'}`)}${detailField('Registry', project.registry || 'Not connected')}${detailField('Registry reference', project.registryRef || 'Not provided')}${detailField('Updated', niceDateTime(project.updatedAt))}</div>${project.txHash ? `<p class="small section-space"><a class="table-action" target="_blank" rel="noopener" href="${escapeHtml((networkExplorer() || '') + '/tx/' + project.txHash)}">View confirmed registration transaction ↗</a></p>` : ''}<div class="callout warning section-space">Project registration anchors references and does not verify environmental claims. Conflict checks cover only imported records.</div><div class="section-space"><h3>Description</h3><p class="small">${escapeHtml(project.description || 'No description added.')}</p></div>`;
  const img = project.type.toLowerCase().includes('wind') ? 'https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=350&q=70' : 'https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=350&q=70';
  return `${pageHeader('Carbon Impact Passport', 'A reviewable project record with source coverage and event history.', `<a class="btn" href="#/projects">← All projects</a> <button class="btn btn-primary" data-action="register-project-chain" data-id="${escapeHtml(project.id)}" ${chainReady ? '' : 'disabled title="Requires a deployed X1 registry and configured registrar signer"'}>Register on X1</button>`)}
    <section class="card detail-hero"><img class="detail-image" src="${img}" alt=""/><div class="detail-hero-info"><p class="eyebrow">PROJECT PASSPORT · DEMO RECORD</p><h1>${escapeHtml(project.name)}</h1><p>${escapeHtml(project.country)}, ${escapeHtml(project.region)} · ${escapeHtml(project.type)}</p></div>${statusTag(project.status)}<div class="detail-hero-actions"><button class="btn btn-sm" data-route="/evidence">＋ Add evidence</button><button class="btn btn-sm" data-route="/monitoring">Monitor</button></div></section>
    <section class="card card-pad section-space"><div class="tabs">${tabs.map((t) => `<button class="tab ${t === activeProjectTab ? 'active' : ''}" data-project-tab="${t}">${t}${t === 'Credits' ? ` (${relatedCredits.length})` : ''}</button>`).join('')}</div>${content}</section>`;
}
function detailField(label, value) { return `<div class="detail-field"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong></div>`; }

function creditsPage() {
  const filtered = db.credits.filter((c) => selectedCreditFilter === 'All' || c.state.toLowerCase() === selectedCreditFilter.toLowerCase());
  return `${pageHeader('Carbon Credits', 'Inspect demo credit batches and their available lifecycle history.', '<button class="btn btn-primary" data-action="new-batch">＋ Add demo batch</button>')}
    <section class="card card-pad"><div class="tabs">${['All', 'Active', 'At Risk', 'Retired'].map((t) => `<button class="tab ${t === selectedCreditFilter ? 'active' : ''}" data-credit-filter="${t}">${t} <span class="tag">${tallyCredits(t)}</span></button>`).join('')}</div><div class="callout info" style="margin-bottom:13px">Quantities are stored as integer kg CO₂e. These seeded batches are fictional demo records. Transfer and retirement actions update database balances and append events; no registry or chain transaction occurs.</div><div class="data-table-wrap"><table class="data-table"><thead><tr><th>BATCH / SERIAL</th><th>PROJECT</th><th>VINTAGE</th><th>QUANTITY</th><th>AVAILABLE</th><th>STATE</th><th>SCORE</th><th></th></tr></thead><tbody>${filtered.map(creditTableRow).join('') || `<tr><td colspan="8">${emptyMini('No batches in this view.', 'Choose another status filter.')}</td></tr>`}</tbody></table></div></section>`;
}
function tallyCredits(filter) { return filter === 'All' ? db.credits.length : db.credits.filter((c) => c.state.toLowerCase() === filter.toLowerCase()).length; }
function creditTableRow(c) { const p = projectFor(c.projectId); return `<tr><td><a href="#/credit/${encodeURIComponent(c.id)}"><strong>${escapeHtml(c.id)}</strong><small>${escapeHtml(c.serial)} · DEMO</small></a></td><td>${escapeHtml(p?.name || c.projectId)}<small>${escapeHtml(c.registry || 'Registry not connected')}</small></td><td>${escapeHtml(c.vintage)}</td><td>${formatTonnes(c.quantityKg)}</td><td>${formatTonnes(c.availableKg)}</td><td>${statusTag(c.state)}</td><td><strong>${c.score}/100*</strong><small>${c.provisional ? 'Provisional demo score' : 'Local score'}</small></td><td><a class="table-action" href="#/credit/${encodeURIComponent(c.id)}">Open →</a></td></tr>`; }
function creditRow(c) { return `<div class="file-row"><span class="file-icon">◈</span><span class="file-main"><strong>${escapeHtml(c.id)} · ${escapeHtml(c.serial)}</strong><small>${formatTonnes(c.quantityKg)} · ${escapeHtml(c.vintage)} vintage · DEMO DATA</small></span>${statusTag(c.state)}<a class="table-action" href="#/credit/${encodeURIComponent(c.id)}">Open</a></div>`; }
function creditPage(creditId) {
  const c = db.credits.find((x) => x.id === decodeURIComponent(creditId)); if (!c) return notFoundPage();
  const p = projectFor(c.projectId); const events = db.events.filter((e) => e.targetId === c.id);
  const contractConfigured = Boolean(blockchainStatus?.network?.contract_address);
  const registrarReady = blockchainStatus?.network?.contract_deployed === true && blockchainStatus?.wallets?.some((wallet) => wallet.role === 'registrar' && wallet.configured && wallet.address);
  const lifecycleActions = c.state === 'Draft' ? `<button class="btn btn-primary" data-action="submit-batch" data-id="${escapeHtml(c.id)}">Submit for review</button>` : c.state === 'Verified by Reviewer' && ['issuer', 'admin'].includes(db.settings?.role) ? `<button class="btn btn-primary" data-action="issue-batch" data-id="${escapeHtml(c.id)}" ${contractConfigured && !registrarReady ? 'disabled title="Registrar wallet is not configured"' : ''}>${contractConfigured ? 'Issue on X1' : 'Issue local demo batch'}</button>` : '';
  return `${pageHeader('Credit Batch Passport', 'Lifecycle record, evidence state, and data coverage for one demo batch.', `<a class="btn" href="#/credits">← Credit registry</a> ${lifecycleActions}`)}
    <section class="card detail-hero"><div class="quick-icon" style="width:54px;height:54px;font-size:1.4rem">◈</div><div class="detail-hero-info"><p class="eyebrow">CREDIT BATCH · DEMO DATA</p><h1>${escapeHtml(c.id)}</h1><p>${escapeHtml(p?.name || c.projectId)} · ${escapeHtml(c.serial)}</p></div>${statusTag(c.state)}<div class="detail-hero-actions">${c.availableKg > 0 && c.state === 'Active' && ['issuer', 'admin'].includes(db.settings?.role) ? `<button class="btn btn-sm" data-action="transfer" data-id="${c.id}">Transfer</button><button class="btn btn-sm btn-primary" data-action="retire" data-id="${c.id}">Retire</button>` : ''}</div></section>
    <div class="two-col section-space"><section class="card card-pad">${cardTitle('Batch details', 'Synthetic demo record')}<div class="detail-fields">${detailField('Project', p?.name || c.projectId)}${detailField('Registry reference', c.registry)}${detailField('Vintage', c.vintage)}${detailField('Issued quantity', formatKg(c.quantityKg))}${detailField('Available balance', formatKg(c.availableKg))}${detailField('Transferred (local record)', formatKg(c.transferredKg || 0))}${detailField('Retired history', formatKg(c.retiredKg))}</div></section><section class="card card-pad">${cardTitle('Integrity score', 'Prototype formula · provisional, illustrative')}<div class="score-summary"><div class="score-ring" style="background:conic-gradient(#39b66d 0 ${c.score}%,#e7efe9 ${c.score}% 100%)"><strong>${c.score}</strong></div><div><h3>${c.provisional ? 'Provisional score' : 'Local demo score'}</h3><p>Assumptions and missing data make this score unsuitable for certification decisions.</p><span class="tag">Last updated ${niceDate(c.updatedAt)}</span></div></div>${scoreBars(c)}</section></div>
    <div class="two-col section-space"><section class="card card-pad">${cardTitle('Evidence & source coverage')}<div class="callout warning">Evidence hashes are computed by the API from uploaded file bytes. Registry coverage is limited to imported CSV records. No chain transaction is attached.</div><div class="section-space">${db.evidence.filter((e) => e.projectId === c.projectId).map(evidenceRow).join('') || '<p class="small">No evidence metadata for this project.</p>'}</div></section><section class="card card-pad">${cardTitle('Lifecycle history', 'Events are appended and remain visible')}<div class="timeline-list">${events.map((e) => `<div class="timeline-entry"><strong>${escapeHtml(e.type)} · DEMO</strong><small>${niceDateTime(e.at)} · ${escapeHtml(e.actor)}<br>${escapeHtml(e.reason)}</small></div>`).join('') || '<p class="small">No lifecycle events yet.</p>'}</div></section></div>
    <section class="card card-pad section-space"><div class="callout info">A blockchain hash, registry transaction, or external retirement reference will appear only after a real connected service confirms it. This local action is not sent to a chain.</div><p class="small section-space"><a class="table-action" href="verify.html?batch=${encodeURIComponent(c.id)}">Open public preview →</a> · Public view excludes original evidence files and reviewer notes.</p></section>`;
}
function scoreBars(c) {
  const components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 };
  const vals = { 'Evidence freshness (M)': components.M, 'Verification context (V)': components.V, 'Registry consistency (C)': components.C, 'Monitoring resilience (R)': components.R, 'Authorization records (A)': components.A };
  return `<div class="score-bars section-space">${Object.entries(vals).map(([label, value]) => `<div class="score-row"><span>${label}</span><span class="score-bar"><i style="width:${value}%"></i></span><strong>${value}</strong></div>`).join('')}</div><p class="tiny muted section-space">S = 0.25M + 0.20V + 0.20C + 0.25R + 0.10A. Prototype assumptions; missing data is flagged as provisional.</p>`;
}

function monitoringPage() {
  const observations = db.observations.filter((o) => selectedMonitoringTab === 'All' || (selectedMonitoringTab === 'Risk alerts' ? o.severity === 'High' || o.severity === 'Critical' : `${o.source} ${o.signal}`.toLowerCase().includes(selectedMonitoringTab.toLowerCase())));
  const rows = observations.map(observationRow).join('') || emptyMini(`No ${selectedMonitoringTab.toLowerCase()} observations.`, 'No matching source records are connected in this local demo.');
  const open = db.alerts.filter((a) => a.state === 'Open').length;
  return `${pageHeader('Monitoring', 'Review available environmental observations and risk signals. A signal is not proof of a reversal.', '<button class="btn btn-primary" data-action="disturbance">＋ Trigger demo disturbance</button>')}
    <div class="metric-grid" style="grid-template-columns:repeat(3,1fr)">${metricCard('Observations', db.observations.length, 'Synthetic demo records', '⌖')}${metricCard('Open alerts', open, 'Require human review', '♧')}${metricCard('Live sources', '0', 'No source connected', '◉')}</div>
    <div class="callout warning" style="margin-bottom:13px">Monitoring records in this prototype are synthetic. A disturbance alert is a review signal, not a confirmed environmental reversal. Historical retirement events remain unchanged.</div>
    <section class="card card-pad">${cardTitle('Observations', 'Source and review state are shown for each record', '<span class="tag">DEMO MODE</span>')}<div class="tabs">${['All', 'Satellite', 'IoT', 'Field observations', 'Risk alerts'].map((x) => `<button class="tab ${selectedMonitoringTab === x ? 'active' : ''}" data-monitor-tab="${x}">${x}</button>`).join('')}</div><div class="source-list">${rows}</div></section>`;
}
function observationRow(o) { return `<article class="alert-card ${o.severity === 'Critical' ? 'critical' : ''}"><span class="alert-symbol">⌖</span><div class="alert-card-main"><h3>${escapeHtml(o.signal)} · ${escapeHtml(o.severity)} <span class="tag">${o.demo ? 'DEMO DATA' : 'LOCAL'}</span></h3><p>${escapeHtml(o.description)}</p><small>${escapeHtml(projectFor(o.projectId)?.name || o.projectId)} · ${escapeHtml(o.source)} · ${niceDateTime(o.observedAt)}</small><div class="section-space">${statusTag(o.state)}</div></div></article>`; }

function evidencePage() {
  const kinds = ['All', 'Documents', 'Images', 'Data', 'Links'];
  const evidenceKind = { Documents: 'Document', Images: 'Image', Data: 'Data', Links: 'Link' }[selectedEvidenceTab];
  const filtered = db.evidence.filter((e) => selectedEvidenceTab === 'All' || e.kind === evidenceKind);
  return `${pageHeader('Evidence Library', 'Upload files to local off-chain storage and compute server-side SHA-256 hashes.', '<button class="btn btn-primary" data-action="scroll-upload">＋ Add Evidence</button>')}
    <div class="callout warning" style="margin-bottom:13px">In the local API mode, the original file is stored off-chain on this machine and hashed by the server. Files are not written to a blockchain or sent to an external service. Avoid confidential data in this demo.</div>
    <section class="card card-pad"><div class="field" style="max-width:420px;margin-bottom:13px"><label for="evidence-project">Attach evidence to project</label><select id="evidence-project">${db.projects.map((p) => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('')}</select></div><div class="tabs">${kinds.map((k, i) => `<span class="tab ${i === 0 ? 'active' : ''}">${k}</span>`).join('')}</div><label class="upload-zone" id="upload-zone"><input id="evidence-files" type="file" multiple accept=".pdf,.csv,.json,.png,.jpg,.jpeg,.webp,.txt"><span><strong>Choose files for local evidence storage</strong><small>PDF, CSV, JSON, images, TXT · Maximum 10 MB each · server computes SHA-256</small></span></label><div id="upload-progress" class="section-space" hidden></div></section>
    <section class="card card-pad section-space">${cardTitle('Evidence records', `${filtered.length} records · sample fixtures are synthetic`)}<div class="tabs">${kinds.map((k) => `<button class="tab ${selectedEvidenceTab === k ? 'active' : ''}" data-evidence-tab="${k}">${k}</button>`).join('')}</div><div class="data-table-wrap"><table class="data-table"><thead><tr><th>FILE / RECORD</th><th>PROJECT</th><th>TYPE</th><th>SHA-256</th><th>STATE</th><th>ADDED</th></tr></thead><tbody>${filtered.map(evidenceTableRow).join('') || '<tr><td colspan="6">No evidence metadata for this filter.</td></tr>'}</tbody></table></div></section>`;
}
function networkExplorer() { return blockchainStatus?.network?.explorer_url || 'https://maculatus-scan.x1eco.com'; }
function evidenceRow(e) { const canAnchor = blockchainStatus?.network?.contract_deployed === true && blockchainStatus?.wallets?.some((wallet) => wallet.role === 'registrar' && wallet.configured && wallet.address); const anchored = Boolean(e.anchorTxHash); return `<div class="file-row"><span class="file-icon">${e.kind === 'Image' ? '▧' : e.kind === 'Data' ? '▦' : '▤'}</span><span class="file-main"><strong>${escapeHtml(e.name)}</strong><small>${escapeHtml(projectFor(e.projectId)?.name || e.projectId)} · ${e.demo ? 'Synthetic fixture; no source file' : `${formatBytes(e.size)} · SHA-256 ${e.hash ? escapeHtml(e.hash.slice(0, 16)) + '…' : 'pending'}`}${anchored ? ` · Anchored on X1 · <a target="_blank" rel="noopener" href="${escapeHtml(networkExplorer() + '/tx/' + e.anchorTxHash)}">View tx ↗</a>` : ''}</small></span>${statusTag(anchored ? 'Anchored on X1' : e.state)}${!e.demo ? `<button class="table-action" data-action="assess-evidence" data-id="${e.id}">Assess</button><button class="table-action" data-action="anchor-evidence" data-id="${e.id}" ${canAnchor && !anchored ? '' : 'disabled title="Requires an unanchored evidence record, deployed registry, and configured registrar"'}>${anchored ? 'Anchored' : 'Anchor hash'}</button>` : ''}</div>`; }
function evidenceTableRow(e) { return `<tr><td><strong>${escapeHtml(e.name)}</strong><small>${e.demo ? 'SYNTHETIC FIXTURE' : `${formatBytes(e.size)} · local only`}</small>${e.size > 0 ? `<button class="table-action" data-action="extract-evidence" data-id="${escapeHtml(e.id)}">Extract claims</button>` : ''}</td><td>${escapeHtml(projectFor(e.projectId)?.name || e.projectId)}</td><td>${escapeHtml(e.kind)}</td><td>${e.hash ? `<span class="mono tiny">${escapeHtml(e.hash.slice(0, 16))}…</span><button class="table-action" data-action="copy" data-copy="${e.hash}">Copy</button>` : '<span class="muted">Not computed</span>'}</td><td>${statusTag(e.state)}</td><td>${niceDate(e.uploadedAt)}</td></tr>`; }
function formatBytes(bytes) { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB']; const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 2); return `${(bytes / (1024 ** i)).toFixed(i ? 1 : 0)} ${units[i]}`; }

function verificationPage() {
  const pending = db.reviews.filter((r) => r.state === 'Pending');
  return `${pageHeader('Verification & Review', 'AI-style deterministic checks are advisory. Authorized humans make material decisions.', '')}
    <div class="callout info" style="margin-bottom:13px">No AI provider is configured. Findings below are deterministic prototype rules and do not certify credits. Reviewer decisions are stored in the database with append-only events.</div>
    <div class="split-layout"><section class="card card-pad">${cardTitle('Review queue', `${pending.length} pending item${pending.length === 1 ? '' : 's'}`)}<div class="source-list">${pending.map(reviewCard).join('') || emptyMini('Queue is clear.', 'New evidence conflicts or monitoring alerts will create review items.')}</div></section>
      <section class="card card-pad">${cardTitle('Evidence assessment', 'Select an evidence item to run local deterministic checks')}<div class="field"><label for="assessment-evidence">Evidence record</label><select id="assessment-evidence"><option value="">Choose a record</option>${db.evidence.filter((e) => !e.demo).map((e) => `<option value="${e.id}">${escapeHtml(e.name)}</option>`).join('')}</select></div><button class="btn btn-primary section-space" data-action="run-assessment">Run deterministic assessment</button><div id="assessment-results" class="section-space">${assessmentResult ? assessmentResult : '<div class="empty-state"><div class="empty-icon">✓</div><h3>Assessment results stay advisory</h3><p>Local checks can flag missing metadata and file properties. A human reviewer must decide what happens next.</p></div>'}</div></section></div>
    <section class="card card-pad section-space">${cardTitle('Decision history', 'Reviewer decisions do not overwrite previous states')}<div class="data-table-wrap"><table class="data-table"><thead><tr><th>ITEM</th><th>FINDING</th><th>DECISION</th><th>REVIEWER</th><th>DATE</th></tr></thead><tbody>${db.reviews.filter((r) => r.state !== 'Pending').map((r) => `<tr><td><strong>${escapeHtml(r.targetId)}</strong><small>DEMO DATA</small></td><td>${escapeHtml(r.finding)}</td><td>${statusTag(r.state)}</td><td>${escapeHtml(r.actor)}</td><td>${niceDateTime(r.decidedAt)}</td></tr>`).join('') || '<tr><td colspan="5">No completed reviewer decisions yet.</td></tr>'}</tbody></table></div></section>`;
}
function reviewCard(r) {
  const alert = db.alerts.find((a) => a.id === r.targetId);
  const context = alert?.explanation || (r.targetType === 'Registry conflict' ? 'Potential duplicate in imported demo records. Human review required.' : 'Submitted batch and supporting evidence require an authorized review.');
  const actions = ['reviewer', 'admin'].includes(db.settings?.role) ? `<div class="alert-actions section-space"><button class="btn btn-sm btn-primary" data-action="review-decision" data-id="${r.id}" data-decision="Approved for next step">Approve review step</button><button class="btn btn-sm" data-action="review-decision" data-id="${r.id}" data-decision="More evidence requested">Request evidence</button><button class="btn btn-sm btn-danger" data-action="review-decision" data-id="${r.id}" data-decision="Rejected">Reject evidence</button></div>` : '<p class="tiny muted">Waiting for an authorized reviewer.</p>';
  return `<article class="alert-card"><span class="alert-symbol">⌕</span><div class="alert-card-main"><h3>${escapeHtml(r.finding)}</h3><p>${escapeHtml(context)}</p><small>${escapeHtml(r.targetId)} · ${niceDateTime(r.createdAt)} · DEMO</small>${actions}</div></article>`;
}

function conflictsPage() {
  const groups = new Map(); db.importedRecords.forEach((r) => { const key = String(r.serial || '').toUpperCase().trim(); if (!groups.has(key)) groups.set(key, []); groups.get(key).push(r); });
  const duplicateGroups = [...groups.entries()].filter(([, rows]) => rows.length > 1);
  return `${pageHeader('Registry Conflicts', 'Inspect potential conflicts found in imported or connected records only.', '<button class="btn" data-action="download-template">Download CSV template</button>')}
    <div class="metric-grid" style="grid-template-columns:repeat(3,1fr)">${metricCard('Imported records', db.importedRecords.length, 'Demo CSV records', '▤')}${metricCard('Potential duplicate serials', duplicateGroups.length, 'Exact serial comparison', '◎')}${metricCard('External registries checked', '0', 'No live connections', '⌕')}</div>
    <div class="split-layout"><section class="card card-pad">${cardTitle('Available duplicate checks', 'Exact serial matches in local imported data', `<span class="tag">${db.importedRecords.length} ROWS</span>`)}${duplicateGroups.length ? duplicateGroups.map(([serial, rows]) => `<article class="alert-card"><span class="alert-symbol">!</span><div class="alert-card-main"><h3>Duplicate serial: <span class="mono">${escapeHtml(serial)}</span></h3><p>Found in ${rows.length} imported records across ${[...new Set(rows.map((r) => r.source))].map(escapeHtml).join(', ')}.</p><small>Potential conflict · DEMO CSV · Not a global registry check</small><div class="section-space">${rows.map((r) => `<div class="tiny">${escapeHtml(r.source)} · ${escapeHtml(r.projectRef)} · ${escapeHtml(r.status)}</div>`).join('')}</div></div></article>`).join('') : emptyMini('No exact serial duplicates in available records.', 'This does not mean unconnected registries have been checked.')}</section>
    <section class="card card-pad">${cardTitle('Import registry CSV', 'Source: user-selected local file; coverage remains limited')}<div class="callout warning">CSV rows are stored in the local database. Do not upload private information. Registry import does not confirm coverage beyond the imported rows.</div><label class="upload-zone section-space"><input id="registry-file" type="file" accept=".csv,text/csv"><span><strong>Choose a CSV file</strong><small>Expected headers: source_name, external_project_id, external_project_name, external_serial, vintage_start, vintage_end, methodology_id, country, region, quantity_kg_co2e, status</small></span></label><div id="registry-import-result" class="section-space"></div></section></div>
    <section class="card card-pad section-space">${cardTitle('Imported record coverage')}<div class="data-table-wrap"><table class="data-table"><thead><tr><th>SOURCE</th><th>PROJECT REFERENCE</th><th>SERIAL</th><th>VINTAGE</th><th>QUANTITY</th><th>STATUS</th></tr></thead><tbody>${db.importedRecords.map((r) => `<tr><td><strong>${escapeHtml(r.source)}</strong><small>Imported demo data</small></td><td>${escapeHtml(r.projectRef)}</td><td class="mono">${escapeHtml(r.serial)}</td><td>${escapeHtml(r.vintage || '—')}</td><td>${formatTonnes(r.quantityKg)}</td><td>${escapeHtml(r.status)}</td></tr>`).join('')}</tbody></table></div></section>`;
}

function alertsPage() {
  const filters = ['All', 'At Risk', 'Open', 'Reviewed'];
  const rows = db.alerts.filter((a) => selectedAlertFilter === 'All' || (selectedAlertFilter === 'Open' ? a.state === 'Open' : selectedAlertFilter === 'Reviewed' ? a.state !== 'Open' : a.severity === selectedAlertFilter));
  return `${pageHeader('Alerts', 'Review material events without erasing the original observation or alert.', '')}<div class="tabs">${filters.map((f) => `<button class="tab ${f === selectedAlertFilter ? 'active' : ''}" data-alert-filter="${f}">${f}</button>`).join('')}</div>
    <div class="callout warning" style="margin-bottom:13px">An alert is a signal for human review, not confirmation of reversal. Any reviewer action creates an additional history event.</div><div class="source-list">${rows.map(alertCard).join('') || emptyMini('No alerts for this filter.', 'New monitoring signals will appear here.')}</div>`;
}
function alertCard(a) {
  const project = projectFor(a.projectId);
  const reviewActions = ['reviewer', 'admin'].includes(db.settings?.role) ? `<button class="btn btn-sm btn-primary" data-action="alert-review" data-id="${a.id}" data-decision="Confirm reversal">Confirm reversal</button><button class="btn btn-sm btn-danger" data-action="alert-review" data-id="${a.id}" data-decision="Reject signal">Reject signal</button><button class="btn btn-sm" data-action="alert-review" data-id="${a.id}" data-decision="Request more evidence">Request more evidence</button>` : '<span class="tiny muted">Waiting for an authorized reviewer.</span>';
  return `<article class="alert-card ${a.severity === 'Critical' ? 'critical' : ''}"><span class="alert-symbol">!</span><div class="alert-card-main"><h3>${escapeHtml(a.type)} · ${escapeHtml(a.severity)} <span class="tag">DEMO</span></h3><p>${escapeHtml(a.explanation)}</p><small>${escapeHtml(project?.name || a.projectId)} · ${niceDateTime(a.createdAt)} · Observation ${escapeHtml(a.observationId || 'not linked')}</small><div class="filter-row">${statusTag(a.state)}${a.reviewer ? `<span class="tiny muted">Reviewed by ${escapeHtml(a.reviewer)}</span>` : ''}</div>${a.state === 'Open' ? `<div class="alert-actions">${reviewActions}<a class="btn btn-sm" href="#/project/${encodeURIComponent(a.projectId)}">View project</a></div>` : ''}</div></article>`;
}

function reportsPage() {
  const reports = [
    ['Impact summary', 'Summarize locally stored project and credit records; values are demo-only.', 'impact'],
    ['Project data report', 'Export project metadata and record timestamps.', 'projects'],
    ['Evidence package', 'Export evidence metadata and hashes. Files are not included.', 'evidence'],
    ['Credit lifecycle history', 'Export batch state and append-only local events.', 'events'],
    ['Registry conflict report', 'Export conflicts from imported records only.', 'conflicts'],
    ['Risk & monitoring report', 'Export synthetic observations and review state.', 'monitoring'],
  ];
  return `${pageHeader('Reports', 'Create transparent exports from database records in this workspace.', '')}<div class="callout info" style="margin-bottom:13px">Exports identify demo records and do not claim regulatory compliance. No third-party framework, registry, or chain verification is included.</div><div class="report-grid">${reports.map(([name, copy, type]) => `<article class="card report-card"><span class="quick-icon">▤</span><h3>${name}</h3><p>${copy}</p><button class="btn btn-sm" data-action="export-report" data-type="${type}">Download CSV</button></article>`).join('')}</div>`;
}

function explorerPage() {
  return `${pageHeader('Public Explorer', 'Search demo batch identifiers and inspect a public-safe preview.', '')}<section class="card card-pad"><form id="explorer-form" class="toolbar"><input id="explorer-query" type="search" placeholder="Enter a batch ID or serial number…" aria-label="Batch ID or serial number"><button class="btn btn-primary" type="submit">Search</button><span class="tag">DEMO DATA ONLY</span></form><div id="explorer-results">${db.credits.slice(0, 3).map((c) => `<div class="file-row"><span class="file-icon">◈</span><span class="file-main"><strong>${escapeHtml(c.id)}</strong><small>${escapeHtml(projectFor(c.projectId)?.name || c.projectId)} · ${escapeHtml(c.serial)}</small></span>${statusTag(c.state)}<a class="table-action" href="verify.html?batch=${encodeURIComponent(c.id)}">Public view →</a></div>`).join('')}</div></section><section class="card card-pad section-space">${cardTitle('Privacy boundary')}<div class="callout warning">Public preview excludes original files, personal data, internal reviewer notes, and secrets. It shows only non-sensitive demo metadata. The public record is served by the read-only local API endpoint.</div></section>`;
}
function publicVerifyPage(creditId) {
  const c = db.credits.find((x) => x.id === decodeURIComponent(creditId) || x.serial === decodeURIComponent(creditId));
  if (!c) return `${pageHeader('Public Verification', 'Public-safe project and credit metadata.', '')}<div class="empty-state"><div class="empty-icon">⌕</div><h3>Record not found</h3><p>No matching local demo record was found. The explorer checks only records stored by this local API.</p><a class="btn" href="#/explorer">Back to Explorer</a></div>`;
  const p = projectFor(c.projectId);
  return `${pageHeader('Public Verification', 'A privacy-limited view of a local demo record.', '<a class="btn" href="#/explorer">← Explorer</a>')}<div class="public-banner">DEMO DATA · Not certified · No live registry or blockchain transaction attached</div><div class="two-col"><section class="card card-pad">${cardTitle('Credit identity', 'Public-safe fields')}<div class="detail-fields">${detailField('Batch ID', c.id)}${detailField('Serial', c.serial)}${detailField('Project', p?.name || c.projectId)}${detailField('Project region', `${p?.country || '—'}, ${p?.region || '—'}`)}${detailField('Vintage', c.vintage)}${detailField('Current local state', c.state)}${detailField('Available balance', formatTonnes(c.availableKg))}${detailField('Retirement history', formatTonnes(c.retiredKg))}${detailField('Registry reference', c.registry || 'Not connected')}</div></section><section class="card card-pad">${cardTitle('Integrity context', 'Provisional prototype score')}<div class="score-summary"><div class="score-ring" style="background:conic-gradient(#39b66d 0 ${c.score}%,#e7efe9 ${c.score}% 100%)"><strong>${c.score}</strong></div><div><h3>Not a certification</h3><p>Score formula is an unvalidated prototype assumption and has missing-data flags.</p></div></div>${scoreBars(c)}</section></div><section class="card card-pad section-space">${cardTitle('Public event history', 'Historical events are preserved')}<div class="timeline-list">${db.events.filter((e) => e.targetId === c.id || e.targetId === c.projectId).map((e) => `<div class="timeline-entry"><strong>${escapeHtml(e.type)} · DEMO</strong><small>${niceDateTime(e.at)} · ${escapeHtml(e.reason)}</small></div>`).join('') || '<p class="small">No public event history.</p>'}</div><div class="callout info section-space">Evidence documents and private reviewer notes are not exposed. Registry source coverage is limited to imported demo records.</div></section>`;
}

function marketplacePage() {
  return `${pageHeader('Marketplace', 'Marketplace is a future product area, outside this integrity prototype.', '')}<div class="empty-state coming-soon"><div class="empty-icon">▣</div><h3>Marketplace is not enabled</h3><p>This prototype does not support listing, order books, or credit transactions. You can inspect demo credit provenance in the Credit Registry. No credits are offered for sale here.</p><a class="btn btn-primary" href="#/credits">View demo credit records</a></div>`;
}
function communityPage() {
  return `${pageHeader('Community', 'Educational material and stakeholder engagement preview.', '')}<div class="three-col">${[['Evidence before claims', 'A traceable record helps others inspect sources, dates, and review context.'], ['Signals need reviewers', 'Monitoring flags help direct attention; people assess material findings.'], ['Coverage matters', 'A duplicate check is only as complete as its available sources.']].map(([h, p], i) => `<article class="card card-pad"><span class="quick-icon">${['▤', '⌁', '◎'][i]}</span><h2 class="section-space">${h}</h2><p class="small">${p}</p><span class="tag">EDUCATION PREVIEW</span></article>`).join('')}</div><div class="callout info section-space">No public posting, community messaging, or benefit claims are enabled in this local prototype.</div>`;
}
function settingsPage() {
  const s = db.settings;
  const network = blockchainStatus?.network;
  const ai = aiProviderStatus;
  const wallets = blockchainStatus?.wallets || [];
  const configuredWallets = wallets.filter((wallet) => wallet.configured && wallet.address);
  const walletSummary = configuredWallets.length ? configuredWallets.map((wallet) => `${wallet.role}: ${wallet.address} · ${wallet.balance ?? '—'} ${wallet.currency}`).join(' | ') : 'No signer keys configured; private keys are never returned by the API.';
  const aiState = ai?.configured ? 'Configured' : ai ? 'Not configured' : 'Status unavailable';
  const providerName = ai?.provider === 'nebius_token_factory' ? 'Nebius Token Factory' : ai?.provider || 'Nebius Token Factory';
  return `${pageHeader('Settings', 'Profile and live X1 testnet connection state for this local workspace.', '')}<div class="tabs" aria-label="Settings sections">${['Profile', 'Organization', 'Wallet', 'Security', 'Notifications'].map((t, i) => `<span class="tab ${i === 0 ? 'active' : ''}">${t}</span>`).join('')}</div><div class="two-col"><form id="settings-form" class="card card-pad">${cardTitle('Profile information', 'Stored in the TRIPLEES database')}<div class="form-grid"><div class="field"><label for="settings-name">Display name</label><input id="settings-name" name="name" value="${escapeHtml(s.displayName)}"></div><div class="field"><label for="settings-email">Email</label><input id="settings-email" name="email" type="email" value="${escapeHtml(s.email)}"></div><div class="field"><label for="settings-location">Location</label><input id="settings-location" name="location" value="${escapeHtml(s.location)}"></div><div class="field"><label for="settings-org">Workspace</label><input id="settings-org" name="organization" value="${escapeHtml(s.organization)}"></div></div><div class="form-footer"><button class="btn btn-primary" type="submit">Save profile</button></div><p class="tiny muted">Prototype authentication is enabled. Production identity, account recovery, and session controls are not configured.</p></form><section class="card card-pad">${cardTitle('Connections & availability', 'Network and signer state read from the backend')}<div class="source-list">${sourceRow('API & database', 'Local API using the configured database', 'Local demo')}${sourceRow('X1 EcoChain', `${network?.network_name || 'Maculatus Testnet'} · chain ${network?.actual_chain_id ?? network?.expected_chain_id ?? '—'} · latest block ${network?.latest_block ?? '—'}`, network?.rpc_connected ? 'Connected' : 'Unavailable')}${sourceRow('Registry contract', network?.contract_address || 'No address configured', network?.contract_deployed ? 'Deployed' : 'Not configured')}${sourceRow('Authorized signer wallets', walletSummary, configuredWallets.length ? 'Configured' : 'Not configured')}${sourceRow('AI provider', providerName, aiState)}${sourceRow('AI model', ai?.model || 'No model configured', ai?.configured ? 'Configured' : ai ? 'Not configured' : 'Status unavailable')}${sourceRow('Registry / Satellite / IoT', 'Imported CSV fixtures and synthetic observations only', 'Not connected')}</div><p class="tiny muted">AI health reports configuration only; it makes no inference call. Checked at ${escapeHtml(network?.checked_at || 'not checked')}. No private key is displayed.</p></section></div><section class="card card-pad section-space">${cardTitle('Local demo data')}<p class="small">The local workspace includes synthetic fixtures. Use reset only when you intend to replace current demo records.</p><div class="form-footer">${db.settings?.role === 'admin' ? '<button class="btn btn-danger" data-action="reset-demo">Reset demo workspace</button>' : ''}<button class="btn" data-action="logout">Sign out</button></div></section>`;
}
function sourceRow(title, desc, state) { return `<div class="source-row"><i class="source-status ${state === 'Not configured' || state === 'Not connected' || state === 'Unavailable' ? 'off' : ''}"></i><span><strong>${title}</strong><small>${desc}</small></span><span>${state}</span></div>`; }
function notFoundPage() { return `${pageHeader('Page not found', 'This workspace route is unavailable.', '<a class="btn btn-primary" href="#/dashboard">Return to Dashboard</a>')}<div class="empty-state"><div class="empty-icon">⌕</div><h3>We could not find that page</h3><p>Use the application navigation to open a supported page.</p></div>`; }

function openModal(title, description, body, submitLabel = '') {
  $('#modal-root').innerHTML = `<div class="modal-backdrop" data-action="backdrop"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header class="modal-head"><div><h2 id="modal-title">${title}</h2><p>${description}</p></div><button class="modal-close" data-action="close-modal" aria-label="Close dialog">×</button></header><div class="modal-body">${body}${submitLabel ? `<div class="form-footer"><button class="btn" type="button" data-action="close-modal">Cancel</button><button class="btn btn-primary" type="submit" form="modal-form">${submitLabel}</button></div>` : ''}</div></section></div>`;
  const focusable = $('#modal-root input, #modal-root select, #modal-root textarea, #modal-root button'); focusable?.focus();
}
function modalField(label, name, type = 'text', attrs = '') { return `<div class="field"><label for="modal-${name}">${label}</label><input id="modal-${name}" name="${name}" type="${type}" ${attrs}></div>`; }
function handleAction(actionButton) {
  const action = actionButton.dataset.action;
  if (action === 'refresh-intelligence') { refreshIntelligencePage(); return; }
  if (action === 'finding-review') {
    if (!['reviewer', 'admin'].includes(db.settings?.role)) { toast('Only an authorized reviewer can decide findings.', true); return; }
    showTextPrompt(actionButton.dataset.decision.replaceAll('_', ' '), 'Record the reason for this finding decision. The decision is saved to the audit history and report version.', 'Save decision');
    $('#modal-form').dataset.findingId = actionButton.dataset.id;
    $('#modal-form').dataset.findingDecision = actionButton.dataset.decision;
    return;
  }
  if (action === 'run-investigation' || action === 'retry-investigation' || action === 'cancel-investigation') { updateInvestigation(action, actionButton.dataset.id); return; }
  if (action === 'extract-evidence') { extractEvidence(actionButton.dataset.id); return; }
  if (action === 'download-investigation-report') { downloadInvestigationReport(); return; }
  if (action === 'print-investigation-report') { window.print(); return; }
  if (action === 'approve-report-anchor') {
    const report = intelligenceState.reports.report;
    if (!report || report.id !== actionButton.dataset.id || !['reviewer', 'admin'].includes(db.settings?.role)) { toast('An authorized reviewer must open the report version before approving its digest.', true); return; }
    showTextPrompt('Approve report digest', `Approve version ${report.version} with SHA-256 ${report.commitment?.sha256}. This records approval only; it does not submit a blockchain transaction.`, 'Record approval');
    $('#modal-form').dataset.reportAnchorApprovalId = report.id;
    $('#modal-form').dataset.reportAnchorInvestigationId = report.investigation_id;
    return;
  }
  if (action === 'submit-report-anchor') { showReportAnchorSubmission(actionButton.dataset.id); return; }
  if (action === 'reconcile-report-anchor') { reconcileReportAnchor(actionButton.dataset.id); return; }
  if (action === 'register-project-chain' || action === 'anchor-evidence') { runChainAction(action, actionButton.dataset.id); return; }
  if (action === 'collapse') { document.body.classList.toggle('sidebar-collapsed'); return; }
  if (action === 'open-sidebar') { document.body.classList.add('sidebar-open'); return; }
  if (action === 'close-sidebar') { closeSidebar(); return; }
  if (action === 'dismiss-notice') { db.noticesDismissed = true; localStorage.setItem('vericarb-notice-dismissed', 'true'); save(); $('.demo-notice').classList.add('notice-dismissed'); return; }
  if (action === 'close-modal' || action === 'backdrop') { if (action === 'backdrop' && (!actionButton.matches('.modal-backdrop') || event.target !== actionButton)) return; $('#modal-root').innerHTML = ''; return; }
  if (action === 'account') { go('/settings'); return; }
  if (action === 'logout') { localStorage.removeItem(API_TOKEN_KEY); apiToken = ''; window.location.replace('auth.html'); return; }
  if (action === 'scroll-upload') { $('#evidence-files')?.click(); return; }
  if (action === 'new-batch') { showBatchModal(); return; }
  if (action === 'transfer') { showCreditActionModal(actionButton.dataset.id, 'transfer'); return; }
  if (action === 'retire') { showCreditActionModal(actionButton.dataset.id, 'retire'); return; }
  if (action === 'disturbance') { addDemoDisturbance(); return; }
  if (action === 'submit-batch' || action === 'issue-batch') { showTextPrompt(action === 'submit-batch' ? 'Submit batch for review' : 'Issue local demo batch', 'This action is recorded in the local database. No chain transaction is sent.', 'Continue'); $('#modal-form').dataset.lifecycleAction = action === 'submit-batch' ? 'submit' : 'issue'; $('#modal-form').dataset.lifecycleBatchId = actionButton.dataset.id; return; }
  if (action === 'run-assessment') { runAssessment(); return; }
  if (action === 'review-decision') { reviewDecision(actionButton.dataset.id, actionButton.dataset.decision); return; }
  if (action === 'alert-review') { reviewAlert(actionButton.dataset.id, actionButton.dataset.decision); return; }
  if (action === 'assess-evidence') { go('/verification'); }
  if (action === 'download-template') { downloadCsv('registry_import_template.csv', [['source_name','external_project_id','external_project_name','external_serial','vintage_start','vintage_end','methodology_id','country','region','quantity_kg_co2e','status','source_timestamp','is_demo']]); return; }
  if (action === 'export-report') { exportReport(actionButton.dataset.type); return; }
  if (action === 'reset-demo') { if (confirm('Reset this local TRIPLEES demo workspace and restore its original synthetic fixtures?')) { if (backendConnected) apiRequest('/api/demo/reset', { method: 'POST' }).then(() => { assessmentResult = null; toast('Demo workspace restored.'); return refreshBackend(); }).catch((error) => toast(error.message, true)); else { localStorage.removeItem(STORE_KEY); db = freshData(); assessmentResult = null; save(); toast('Demo workspace restored.'); renderShell(); } } return; }
  if (action === 'copy') { navigator.clipboard?.writeText(actionButton.dataset.copy).then(() => toast('Hash copied.')).catch(() => toast('Clipboard access is unavailable.', true)); return; }
}
function showReportAnchorSubmission(anchorId) {
  const report = intelligenceState.reports.report; const anchor = report?.anchor;
  if (!anchor || anchor.id !== anchorId || !['reviewer', 'admin'].includes(db.settings?.role)) { toast('The approved report anchor is unavailable.', true); return; }
  const network = blockchainStatus?.network || {};
  const address = network.report_anchor_contract_address || 'No report anchor contract configured';
  openModal('Submit report digest to X1', `This sends one irreversible transaction on X1 EcoChain Testnet (Maculatus), chain 10778, to contract ${address}. It includes only SHA-256 ${anchor.sha256}, report version ${report.version}, and a random commitment reference. It does not send report contents.`, `<form id="modal-form" class="form-grid"><div class="field full"><label class="check-row"><input type="checkbox" name="confirm_submission" value="true" required><span><strong>I approve this X1 testnet transaction</strong><small>The configured reviewer signer will pay network gas. The transaction cannot be recalled after confirmation.</small></span></label></div></form><p class="tiny">Digest: <code>${escapeHtml(anchor.sha256)}</code></p>`, 'Submit to X1');
  $('#modal-form').dataset.reportAnchorSubmitId = anchorId;
}
async function reconcileReportAnchor(anchorId) {
  try {
    const result = await apiRequest(`/api/report-anchors/${encodeURIComponent(anchorId)}/reconcile`, { method: 'POST', body: {} });
    toast(result.status === 'confirmed' ? 'On-chain report digest verified.' : 'No confirmed anchor is visible yet.');
    const report = intelligenceState.reports.report;
    if (report) await selectInvestigationReport(report.investigation_id, report.version);
  } catch (error) { toast(error.message, true); }
}
async function updateInvestigation(action, investigationId) {
  const activity = intelligenceState.activity;
  const button = document.querySelector(`[data-action="${action}"][data-id="${CSS.escape(investigationId)}"]`);
  if (button) { button.disabled = true; button.textContent = 'Saving…'; }
  const endpoint = action === 'cancel-investigation' ? 'cancel' : action === 'retry-investigation' ? 'retry' : 'run';
  try {
    await apiRequest(`/api/investigations/${encodeURIComponent(investigationId)}/${endpoint}`, { method: 'POST', body: {} });
    activity.loaded = false; activity.loadedId = '';
    toast(action === 'cancel-investigation' ? 'Cancellation requested and recorded.' : action === 'retry-investigation' ? 'Retry queued.' : 'Investigation queued.');
    await loadIntelligencePage('agent-activity', investigationId);
  } catch (error) {
    toast(error.message, true);
    activity.loaded = false; activity.loadedId = '';
    await loadIntelligencePage('agent-activity', investigationId);
  }
}
function downloadInvestigationReport() {
  const report = intelligenceState.reports.report;
  if (!report) { toast('There is no report to download.', true); return; }
  const safeId = String(report.investigation_id || 'investigation').replace(/[^a-z0-9_-]/gi, '-');
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = `triplees-${safeId}-report-v${report.version}.json`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000); toast('Investigation report JSON downloaded.');
}
async function runChainAction(action, recordId) {
  const button = document.querySelector(`[data-action="${action}"][data-id="${CSS.escape(recordId)}"]`);
  if (button) { button.disabled = true; button.textContent = 'Waiting for confirmation…'; }
  try {
    const path = action === 'register-project-chain' ? `/api/projects/${encodeURIComponent(recordId)}/register-chain` : `/api/evidence/${encodeURIComponent(recordId)}/anchor`;
    const result = await apiRequest(path, { method: 'POST' });
    toast(`Confirmed on X1 · ${result.transaction_hash.slice(0, 12)}…`);
    await refreshBackend();
  } catch (error) {
    toast(error.message, true);
    if (button) { button.disabled = false; button.textContent = action === 'register-project-chain' ? 'Register on X1' : 'Anchor hash'; }
  }
}

function showBatchModal() {
  openModal('Add a demo batch', 'Creates a local draft batch; it does not issue credits or submit a chain transaction.', `<form id="modal-form" class="form-grid"><div class="field full"><label for="modal-project">Project *</label><select id="modal-project" name="projectId" required>${db.projects.map((p) => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('')}</select></div>${modalField('Serial reference *', 'serial', 'text', 'required placeholder="e.g. DEMO-SERIAL-0100"')}${modalField('Quantity (integer kg CO₂e) *', 'quantityKg', 'number', 'required min="1" step="1"')}${modalField('Vintage year', 'vintage', 'number', `min="1900" max="${new Date().getFullYear()}" value="2025"`)}<div class="field"><label for="modal-registry">Registry source reference</label><input id="modal-registry" name="registry" placeholder="Not connected"></div></form><div class="callout warning section-space">Batch remains Draft until a real authorized review and issuance flow is configured.</div>`, 'Save draft');
}
function showCreditActionModal(creditId, action) {
  const c = db.credits.find((x) => x.id === creditId); if (!c) return;
  if (c.state !== 'Active') { toast('Only Active demo batches can be transferred or retired in this prototype.', true); return; }
  const isRetire = action === 'retire';
  openModal(isRetire ? 'Record a demo retirement' : 'Record a demo transfer', `${c.id} · available balance ${formatKg(c.availableKg)}. This action updates the local database; no external registry or chain transaction is sent.`, `<form id="modal-form" class="form-grid">${modalField('Quantity (integer kg CO₂e) *', 'quantityKg', 'number', `required min="1" max="${c.availableKg}" step="1"`)}${!isRetire ? modalField('Recipient reference', 'recipient', 'text', 'placeholder="Optional demo reference"') : ''}<div class="field full"><label for="modal-reason">Reason *</label><textarea id="modal-reason" name="reason" required placeholder="Add a short audit note for this demo action."></textarea></div></form><div class="callout warning section-space">${isRetire ? 'This adds a historical retirement event in the local demo. It is not sent to an external registry and does not reverse any external retirement.' : 'This updates only the local available balance and adds a demo event. No wallet or chain transaction occurs.'}</div>`, isRetire ? 'Record local retirement' : 'Record local transfer');
  $('#modal-form').dataset.creditId = creditId; $('#modal-form').dataset.creditAction = action;
}
function showTextPrompt(title, description, submitLabel, formId = 'modal-form') {
  openModal(title, description, `<form id="${formId}" class="form-grid"><div class="field full"><label for="modal-reason">Reviewer reason *</label><textarea id="modal-reason" name="reason" required minlength="5" maxlength="2000" placeholder="Record a clear reason for this decision."></textarea></div></form>`, submitLabel);
}

async function addDemoDisturbance() {
  const target = db.projects.find((p) => p.id === 'DEMO-FOREST-001') || db.projects[0];
  if (!target) { toast('Add a project first.', true); return; }
  if (backendConnected) {
    try {
      const observation = await apiRequest(`/api/projects/${encodeURIComponent(target.id)}/monitoring-observations`, { method: 'POST', body: { source_name: 'Synthetic demo control', signal_type: 'forest_loss', severity: 'high', affected_area_percent: 18, observed_at: new Date().toISOString(), description: 'Synthetic demonstration event only; not a real satellite or field observation.', is_synthetic: true } });
      await apiRequest(`/api/monitoring-observations/${encodeURIComponent(observation.id)}/evaluate`, { method: 'POST', body: { reason: 'Synthetic demo disturbance triggered for the review workflow.' } });
      await refreshBackend(); toast('Synthetic observation and server-side review alert created.');
    } catch (error) { toast(error.message, true); }
    return;
  }
  const observation = { id: id('OBS-DEMO'), projectId: target.id, source: 'Synthetic demo control', signal: 'Forest disturbance signal', severity: 'High', value: 'Illustrative signal', observedAt: new Date().toISOString(), description: 'Synthetic demonstration event only; not a real satellite or field observation.', state: 'Needs human review', demo: true };
  const alert = { id: id('ALT-DEMO'), projectId: target.id, type: 'Potential disturbance', severity: 'At Risk', explanation: 'A synthetic disturbance signal was created for demonstration. It is not proof of reversal.', createdAt: observation.observedAt, state: 'Open', demo: true, observationId: observation.id };
  db.observations.unshift(observation); db.alerts.unshift(alert); db.reviews.unshift({ id: id('REV-DEMO'), targetId: alert.id, targetType: 'Monitoring alert', finding: 'Synthetic disturbance signal requires human review.', state: 'Pending', createdAt: observation.observedAt, actor: 'Demo reviewer', reason: '', demo: true });
  target.status = 'At Risk'; target.updatedAt = observation.observedAt;
  db.credits.filter((c) => c.projectId === target.id && ['Active', 'At Risk'].includes(c.state)).forEach((c) => { c.state = 'At Risk'; c.components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 }; c.components.R = Math.min(c.components.R, 30); recomputeScore(c); });
  db.events.unshift({ id: id('EVT-DEMO'), targetId: target.id, type: 'Risk warning', actor: 'Synthetic demo control', reason: 'Synthetic observation added; human review required. Not a confirmed reversal.', at: observation.observedAt, demo: true });
  save(); toast('Synthetic monitoring signal and review alert added.'); renderShell();
}

function reviewDecision(reviewId, decision) {
  const review = db.reviews.find((x) => x.id === reviewId); if (!review || review.state !== 'Pending') return;
  showTextPrompt(decision, `${review.finding} · Decision is a reviewer workflow step, not credit certification.`, 'Save decision');
  $('#modal-form').dataset.reviewId = reviewId; $('#modal-form').dataset.reviewDecision = decision;
}
function reviewAlert(alertId, decision) {
  const alert = db.alerts.find((x) => x.id === alertId); if (!alert || alert.state !== 'Open') return;
  showTextPrompt(decision, `${alert.type} · This does not confirm a climate reversal.`, 'Save review');
  $('#modal-form').dataset.alertId = alertId; $('#modal-form').dataset.alertDecision = decision;
}
async function runAssessment() {
  const select = $('#assessment-evidence'); const evidence = db.evidence.find((e) => e.id === select?.value);
  if (!evidence) { toast('Select a non-fixture evidence file first.', true); return; }
  if (backendConnected) {
    try {
      const result = await apiRequest('/api/assessments/evidence-review', { method: 'POST', body: { evidence_id: evidence.id } });
      assessmentResult = `<div class="callout warning"><strong>Deterministic assessment · advisory</strong><ul>${result.findings.map((f) => `<li>${escapeHtml(f.explanation)} ${escapeHtml(f.next_step)}</li>`).join('')}</ul><p>No automatic approval was performed. This assessment is queued for human review.</p></div>`;
      await refreshBackend();
    } catch (error) { toast(error.message, true); }
    return;
  }
  const risk = [];
  if (!evidence.hash) risk.push('No file digest is available.');
  if (evidence.size === 0) risk.push('File size is empty or unknown.');
  if (!evidence.name || evidence.name.startsWith('.')) risk.push('Filename metadata needs human review.');
  risk.push('Source authenticity and document contents have not been independently verified.');
  evidence.findings = risk; evidence.state = 'Assessment ready'; evidence.assessedAt = new Date().toISOString();
  db.credits.filter((c) => c.projectId === evidence.projectId).forEach((c) => { c.components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 }; c.components.M = Math.min(c.components.M, 45); recomputeScore(c); });
  const review = { id: id('REV'), targetId: evidence.id, targetType: 'Evidence assessment', finding: 'Evidence assessment needs human review.', state: 'Pending', createdAt: evidence.assessedAt, actor: 'Deterministic prototype rule', reason: '', demo: true };
  db.reviews.unshift(review); recordEvent(evidence.projectId, 'Assessment created', 'Deterministic local checks only; no AI service configured.'); save();
  assessmentResult = `<div class="callout warning"><strong>Deterministic assessment · advisory</strong><p>Potential findings:</p><ul>${risk.map((x) => `<li>${escapeHtml(x)}</li>`).join('')}</ul><p>No automatic approval was performed. Review item ${escapeHtml(review.id)} is pending.</p></div>`;
  toast('Advisory assessment added to the human review queue.'); renderShell();
}

function parseCsv(text) {
  const rows = []; let row = []; let cell = ''; let quoted = false;
  for (let i = 0; i < text.length; i++) { const ch = text[i]; if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; } else if (ch === '"') quoted = !quoted; else if (ch === ',' && !quoted) { row.push(cell); cell = ''; } else if ((ch === '\n' || ch === '\r') && !quoted) { if (ch === '\r' && text[i + 1] === '\n') i++; row.push(cell); if (row.some((x) => x.trim())) rows.push(row); row = []; cell = ''; } else cell += ch; }
  row.push(cell); if (row.some((x) => x.trim())) rows.push(row);
  const headers = (rows.shift() || []).map((x) => x.trim());
  return rows.map((cells) => Object.fromEntries(headers.map((key, i) => [key, (cells[i] || '').trim()])));
}
function normalizeImported(row) {
  return { source: row.source_name || 'Local CSV import', projectRef: row.external_project_id || '', project: row.external_project_name || '', serial: row.external_serial || '', vintage: (row.vintage_start || '').slice(0, 4), methodology: row.methodology_id || '', country: row.country || '', quantityKg: Math.max(0, Number.parseInt(row.quantity_kg_co2e || '0', 10) || 0), status: row.status || 'unknown', demo: true };
}

function exportReport(type) {
  let rows = [];
  if (type === 'projects') rows = [['project_id','name','type','country','region','status','is_demo'], ...db.projects.map((p) => [p.id,p.name,p.type,p.country,p.region,p.status,'true'])];
  if (type === 'evidence') rows = [['evidence_id','name','project_id','kind','sha256','state','is_demo'], ...db.evidence.map((e) => [e.id,e.name,e.projectId,e.kind,e.hash || '',e.state,'true'])];
  if (type === 'events') rows = [['event_id','target_id','event_type','actor','reason','timestamp_utc','is_demo'], ...db.events.map((e) => [e.id,e.targetId,e.type,e.actor,e.reason,e.at,'true'])];
  if (type === 'monitoring') rows = [['observation_id','project_id','source','signal','severity','observed_at','state','is_demo'], ...db.observations.map((o) => [o.id,o.projectId,o.source,o.signal,o.severity,o.observedAt,o.state,'true'])];
  if (type === 'conflicts') { const groups = new Map(); db.importedRecords.forEach((r) => groups.set(r.serial, [...(groups.get(r.serial) || []), r])); rows = [['serial','source','project_ref','status','is_demo'], ...[...groups.entries()].filter(([, g]) => g.length > 1).flatMap(([serial, g]) => g.map((r) => [serial,r.source,r.projectRef,r.status,'true']))]; }
  if (type === 'impact') rows = [['metric','value','unit','source'], ['projects_tracked',db.projects.length,'records','local demo data'], ['available_credits',db.credits.reduce((s,c)=>s+c.availableKg,0),'kg CO2e','local demo data'], ['retired_credits',db.credits.reduce((s,c)=>s+c.retiredKg,0),'kg CO2e','local demo data']];
  rows.unshift(['Report type', type, 'Generated at UTC', new Date().toISOString(), 'Source', 'Local demo workspace']);
  downloadCsv(`triplees-${type}-demo.csv`, rows);
}
function csvEscape(value) { const text = String(value ?? ''); return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text; }
function downloadCsv(filename, rows) {
  const csv = rows.map((row) => row.map(csvEscape).join(',')).join('\r\n'); const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); toast('CSV export generated from local demo data.');
}

document.addEventListener('click', (event) => {
  const routeEl = event.target.closest('[data-route]');
  if (routeEl) { event.preventDefault(); go(routeEl.dataset.route); return; }
  const navLink = event.target.closest('[data-nav]');
  if (navLink) { closeSidebar(); return; }
  const tab = event.target.closest('[data-project-tab]');
  if (tab) { activeProjectTab = tab.dataset.projectTab; renderShell(); return; }
  const creditFilter = event.target.closest('[data-credit-filter]');
  if (creditFilter) { selectedCreditFilter = creditFilter.dataset.creditFilter; renderShell(); return; }
  const alertFilter = event.target.closest('[data-alert-filter]');
  if (alertFilter) { selectedAlertFilter = alertFilter.dataset.alertFilter; renderShell(); return; }
  const monitorTab = event.target.closest('[data-monitor-tab]');
  if (monitorTab) { selectedMonitoringTab = monitorTab.dataset.monitorTab; renderShell(); return; }
  const evidenceTab = event.target.closest('[data-evidence-tab]');
  if (evidenceTab) { selectedEvidenceTab = evidenceTab.dataset.evidenceTab; renderShell(); return; }
  const staticTab = event.target.closest('[data-static-tab]');
  if (staticTab) { $$('.tab', staticTab.parentElement).forEach((x) => x.classList.toggle('active', x === staticTab)); return; }
  const actionEl = event.target.closest('[data-action]'); if (actionEl) handleAction(actionEl);
});

document.addEventListener('change', async (event) => {
  if (event.target.id === 'project-filter') { selectedProjectFilter = event.target.value; const search = $('#project-search')?.value || ''; renderShell(); if ($('#project-search')) { $('#project-search').value = search; applyProjectSearch(search); } }
  if (event.target.id === 'evidence-files') await handleEvidenceFiles(event.target.files);
  if (event.target.id === 'registry-file') await handleRegistryImport(event.target.files?.[0]);
  if (event.target.id === 'intel-project-select') renderShell();
  if (event.target.id === 'intel-activity-select') go(`/agent-activity/${encodeURIComponent(event.target.value)}`);
  if (event.target.id === 'intel-report-select' && event.target.value) selectInvestigationReport(event.target.value);
  if (event.target.id === 'intel-report-version' && event.target.value) selectInvestigationReport(intelligenceState.reports.selectedId, Number(event.target.value));
  if (event.target.id === 'risk-severity') { riskFilters.severity = event.target.value; renderShell(); }
  if (event.target.id === 'risk-status') { riskFilters.status = event.target.value; renderShell(); }
});

document.addEventListener('input', (event) => {
  if (event.target.id === 'project-search') applyProjectSearch(event.target.value);
  if (event.target.id === 'global-search') updateGlobalSearch(event.target.value);
  if (event.target.id === 'risk-search') {
    riskFilters.query = event.target.value;
    const position = event.target.selectionStart;
    renderShell();
    const replacement = $('#risk-search');
    if (replacement) { replacement.focus(); replacement.setSelectionRange(position, position); }
  }
});
function applyProjectSearch(query) {
  const q = query.toLowerCase().trim();
  const rows = db.projects.filter((p) => (selectedProjectFilter === 'All' || p.status.toLowerCase().replaceAll(' ', '-') === selectedProjectFilter.toLowerCase().replaceAll(' ', '-')) && `${p.name} ${p.id} ${p.country} ${p.region} ${p.registryRef}`.toLowerCase().includes(q));
  const tbody = $('#project-rows');
  if (tbody) {
    tbody.innerHTML = rows.map(projectRow).join('') || `<tr><td colspan="6">${emptyMini('No matching projects.', 'Try another search or status filter.')}</td></tr>`;
    prepareDataViews($('#page-content'));
  }
}
function updateGlobalSearch(query) {
  const root = $('#search-results'); const q = query.toLowerCase().trim(); if (!q) { root.hidden = true; root.innerHTML = ''; return; }
  const matches = [
    ...db.projects.filter((p) => `${p.name} ${p.id} ${p.region}`.toLowerCase().includes(q)).map((p) => ({ title: p.name, hint: `Project · ${p.id}`, path: `/project/${p.id}` })),
    ...db.credits.filter((c) => `${c.id} ${c.serial}`.toLowerCase().includes(q)).map((c) => ({ title: c.id, hint: `Credit batch · ${c.serial}`, path: `/credit/${c.id}` })),
  ].slice(0, 8);
  root.hidden = false; root.innerHTML = matches.map((m) => `<a class="search-result" href="#${m.path}"><strong>${escapeHtml(m.title)}</strong><small style="display:block;color:#7e8b82">${escapeHtml(m.hint)}</small></a>`).join('') || '<div class="search-result">No matching local records.</div>';
}

document.addEventListener('submit', async (event) => {
  event.preventDefault(); const form = event.target;
  if (form.id === 'investigation-form') { submitInvestigation(form); return; }
  if (form.id === 'project-form') { submitProject(form); return; }
  if (form.id === 'modal-form') { submitModal(form); return; }
  if (form.id === 'explorer-form') { searchExplorer($('#explorer-query').value); return; }
  if (form.id === 'settings-form') { saveSettings(form); return; }
});
async function submitInvestigation(form) {
  if (!form.reportValidity()) return;
  if (!backendConnected) { toast('Sign in to the authenticated API before creating an investigation.', true); return; }
  const data = new FormData(form);
  const payload = {
    project_id: String(data.get('project_id')),
    title: String(data.get('title')).trim(),
    scope: String(data.get('scope')).trim(),
    evidence_ids: data.getAll('evidence_ids').map(String),
    external_ai_authorized: data.has('external_ai_authorized'),
    public_research_authorized: data.has('public_research_authorized'),
  };
  const submit = form.querySelector('[type="submit"]'); if (submit) { submit.disabled = true; submit.textContent = 'Creating…'; }
  try {
    const created = await apiRequest('/api/investigations', { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: payload });
    await apiRequest(`/api/investigations/${encodeURIComponent(created.id)}/run`, { method: 'POST', body: {} });
    intelligenceState.center.loaded = false; intelligenceState.activity.loaded = false; intelligenceState.dashboard.loaded = false;
    toast('Investigation created and queued.'); go(`/agent-activity/${encodeURIComponent(created.id)}`);
  } catch (error) {
    toast(error.message, true);
    if (submit) { submit.disabled = false; submit.textContent = 'Create and queue investigation'; }
  }
}
async function submitProject(form) {
  if (!form.reportValidity()) return;
  const data = new FormData(form);
  if (backendConnected) {
    const projectType = String(data.get('type')).toLowerCase().includes('forest') ? 'forest' : String(data.get('type')).toLowerCase().includes('soil') ? 'soil' : String(data.get('type')).toLowerCase().includes('renewable') ? 'renewable' : 'other';
    try { const project = await apiRequest('/api/projects', { method: 'POST', body: { name: data.get('name'), project_type: projectType, country: data.get('country'), region: data.get('region') || 'Not specified', methodology_id: data.get('method') || null, vintage_start: data.get('vintage-start') || null, vintage_end: data.get('vintage-end') || null, registry_name: data.get('registry') || null, registry_project_ref: data.get('registry-ref') || null, baseline_summary: data.get('description') || null } }); await refreshBackend(false); toast(`Draft ${project.id} created in the database.`); go(`/project/${encodeURIComponent(project.id)}`); } catch (error) { toast(error.message, true); }
    return;
  }
  const project = { id: id('DEMO-PROJECT'), name: data.get('name').trim(), type: data.get('type'), country: data.get('country').trim(), region: data.get('region').trim() || 'Not specified', methodology: data.get('method').trim(), countryCode: '', vintageStart: data.get('vintage-start'), vintageEnd: data.get('vintage-end'), registry: data.get('registry').trim() || 'Not connected', registryRef: data.get('registry-ref').trim(), description: data.get('description').trim(), status: 'Draft', demo: true, updatedAt: new Date().toISOString() };
  db.projects.unshift(project); db.events.unshift({ id: id('EVT-DEMO'), targetId: project.id, type: 'Project created', actor: 'Jordan Demo', reason: 'Local project draft created. No external verification performed.', at: project.updatedAt, demo: true }); save(); toast(`Local draft ${project.id} created.`); go(`/project/${encodeURIComponent(project.id)}`);
}
async function submitModal(form) {
  if (!form.reportValidity()) return;
  const data = new FormData(form);
  if (form.dataset.reportAnchorApprovalId) {
    const report = intelligenceState.reports.report;
    try {
      const anchor = await apiRequest(`/api/investigations/${encodeURIComponent(form.dataset.reportAnchorInvestigationId)}/reports/${encodeURIComponent(form.dataset.reportAnchorApprovalId)}/anchor/approve`, { method: 'POST', body: { reason: String(data.get('reason')).trim() } });
      $('#modal-root').innerHTML = '';
      toast('Report digest approval recorded. No blockchain transaction was sent.');
      if (report) await selectInvestigationReport(report.investigation_id, report.version);
      else refreshIntelligencePage('investigation-reports');
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (form.dataset.reportAnchorSubmitId) {
    if (!data.has('confirm_submission')) { toast('Confirm the X1 transaction before submitting.', true); return; }
    const report = intelligenceState.reports.report;
    try {
      const result = await apiRequest(`/api/report-anchors/${encodeURIComponent(form.dataset.reportAnchorSubmitId)}/submit`, { method: 'POST', body: { confirm_submission: true } });
      $('#modal-root').innerHTML = '';
      toast(result.status === 'confirmed' ? 'Report digest anchored and confirmed on X1.' : `X1 anchor status: ${result.status}.`);
      if (report) await selectInvestigationReport(report.investigation_id, report.version);
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (form.dataset.findingId) {
    if (!['reviewer', 'admin'].includes(db.settings?.role)) { toast('Only an authorized reviewer can decide findings.', true); return; }
    try {
      const result = await apiRequest(`/api/findings/${encodeURIComponent(form.dataset.findingId)}/review`, { method: 'POST', body: { decision: form.dataset.findingDecision, reason: String(data.get('reason')).trim() } });
      $('#modal-root').innerHTML = '';
      intelligenceState.review.loaded = false; intelligenceState.risk.loaded = false; intelligenceState.reports.loaded = false; intelligenceState.dashboard.loaded = false;
      toast(`Decision recorded. Report version ${result.report_version} created.`);
      refreshIntelligencePage();
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (form.dataset.lifecycleAction) {
    try {
      const batch = await apiRequest(`/api/batches/${encodeURIComponent(form.dataset.lifecycleBatchId)}/${form.dataset.lifecycleAction}`, { method: 'POST', body: { reason: String(data.get('reason')).trim() } });
      $('#modal-root').innerHTML = '';
      await refreshBackend();
      toast(form.dataset.lifecycleAction === 'submit' ? 'Batch submitted; the reviewer queue has been updated.' : `Batch issuance recorded locally; chain status: ${batch.transaction?.status || 'not configured'}.`);
    } catch (error) { toast(error.message, true); }
    return;
  }
  if (form.dataset.creditAction) {
    const c = db.credits.find((x) => x.id === form.dataset.creditId); const quantity = Number(data.get('quantityKg')); const action = form.dataset.creditAction;
    if (!c || c.state !== 'Active' || !Number.isSafeInteger(quantity) || quantity < 1 || quantity > c.availableKg) { toast('Only an Active batch with sufficient available balance can be changed.', true); return; }
    const reason = String(data.get('reason') || '').trim();
    if (backendConnected) {
      try { await apiRequest(`/api/batches/${encodeURIComponent(c.id)}/${action}`, { method: 'POST', body: action === 'retire' ? { quantity_kg_co2e: quantity, beneficiary: 'Jordan Demo', purpose: reason, reason } : { quantity_kg_co2e: quantity, recipient_ref: data.get('recipient') || 'Demo recipient', reason } }); $('#modal-root').innerHTML = ''; await refreshBackend(); toast(action === 'retire' ? 'Retirement event saved by the local API. No external registry transaction occurred.' : 'Transfer event saved by the local API. No external transaction occurred.'); } catch (error) { toast(error.message, true); }
      return;
    }
    if (action === 'retire') { c.availableKg -= quantity; c.retiredKg += quantity; if (c.availableKg === 0) c.state = 'Retired'; }
    else { c.availableKg -= quantity; c.transferredKg = (c.transferredKg || 0) + quantity; if (c.availableKg === 0) c.state = 'Transferred'; }
    c.updatedAt = new Date().toISOString(); recordEvent(c.id, action === 'retire' ? 'Credit retirement recorded' : 'Credit transfer recorded', `${formatKg(quantity)} · ${reason}${data.get('recipient') ? ` · Recipient: ${data.get('recipient')}` : ''} · Local demo only.`); save(); $('#modal-root').innerHTML = ''; toast(action === 'retire' ? 'Local retirement history recorded.' : 'Local transfer history recorded.'); renderShell(); return;
  }
  if (form.dataset.reviewId) {
    const review = db.reviews.find((x) => x.id === form.dataset.reviewId); if (!review) return;
    if (backendConnected) {
      const reason = String(data.get('reason')).trim();
      const decisionMap = { 'Approved for next step': 'approved', 'More evidence requested': 'needs_more_evidence', 'Rejected': 'rejected' };
      const body = { decision: decisionMap[form.dataset.reviewDecision], reason };
      try {
        if (review.targetType === 'Registry conflict' || review.targetType === 'Credit batch review') await apiRequest(`/api/batches/${encodeURIComponent(review.targetId)}/review`, { method: 'POST', body });
        else await apiRequest(`/api/assessments/${encodeURIComponent(review.targetId)}/review`, { method: 'POST', body });
        $('#modal-root').innerHTML = ''; await refreshBackend(); toast('Human reviewer decision saved to the database and audit history.');
      } catch (error) { toast(error.message, true); }
      return;
    }
    review.state = form.dataset.reviewDecision; review.reason = String(data.get('reason')).trim(); review.actor = 'Jordan Demo'; review.decidedAt = new Date().toISOString();
    if (review.targetType === 'Evidence assessment') { const evidence = db.evidence.find((x) => x.id === review.targetId); if (evidence) { evidence.state = review.state; if (review.state === 'Approved for next step') db.credits.filter((c) => c.projectId === evidence.projectId).forEach((c) => { c.components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 }; c.components.M = Math.max(c.components.M, 60); recomputeScore(c); }); } }
    recordEvent(review.targetId, 'Human review decision', `${review.state}: ${review.reason}`); save(); $('#modal-root').innerHTML = ''; toast('Review decision appended to local history.'); renderShell(); return;
  }
  if (form.dataset.alertId) {
    const alert = db.alerts.find((x) => x.id === form.dataset.alertId); if (!alert) return;
    if (backendConnected) {
      const decisionMap = { 'Confirm reversal': 'alert_confirmed', 'Reject signal': 'alert_rejected', 'Request more evidence': 'needs_more_evidence' };
      try { await apiRequest(`/api/alerts/${encodeURIComponent(alert.id)}/review`, { method: 'POST', body: { decision: decisionMap[form.dataset.alertDecision], reason: String(data.get('reason')).trim() } }); $('#modal-root').innerHTML = ''; await refreshBackend(); toast('Reviewer decision appended; the source observation and historical retirement remain intact.'); } catch (error) { toast(error.message, true); }
      return;
    }
    alert.state = 'Reviewed'; alert.reviewer = 'Jordan Demo'; alert.reviewDecision = form.dataset.alertDecision; alert.reviewReason = String(data.get('reason')).trim(); alert.reviewedAt = new Date().toISOString();
    const review = db.reviews.find((x) => x.targetId === alert.id && x.state === 'Pending'); if (review) { review.state = form.dataset.alertDecision; review.reason = alert.reviewReason; review.actor = 'Jordan Demo'; review.decidedAt = alert.reviewedAt; }
    recordEvent(alert.id, 'Alert reviewed', `${alert.reviewDecision}: ${alert.reviewReason}. Original alert retained; no reversal confirmed.`); save(); $('#modal-root').innerHTML = ''; toast('Review action saved; original alert retained.'); renderShell(); return;
  }
  if (form.querySelector('#modal-project')) {
    const quantityKg = Number(data.get('quantityKg')); const project = projectFor(data.get('projectId')); const serial = String(data.get('serial')).trim();
    if (!Number.isSafeInteger(quantityKg) || quantityKg <= 0 || !serial) { toast('Enter a positive whole-kilogram amount and serial reference.', true); return; }
    if (db.credits.some((c) => c.serial.toLowerCase() === serial.toLowerCase())) { toast('That serial already exists in the local workspace.', true); return; }
    if (backendConnected) {
      const year = Number(data.get('vintage')) || new Date().getFullYear();
      try { const batch = await apiRequest(`/api/projects/${encodeURIComponent(project.id)}/batches`, { method: 'POST', body: { serial_start: serial, quantity_kg_co2e: quantityKg, vintage_start: `${year}-01-01`, vintage_end: `${year}-12-31`, registry_name: data.get('registry') || null } }); $('#modal-root').innerHTML = ''; await refreshBackend(); toast(`Draft batch ${batch.batch_code} created. It is not issued.`); } catch (error) { toast(error.message, true); }
      return;
    }
    const batch = { id: id('DEMO-BATCH'), projectId: project.id, serial, vintage: String(data.get('vintage') || 'Unknown'), quantityKg, availableKg: 0, retiredKg: 0, registry: String(data.get('registry') || 'Not connected'), state: 'Draft', score: 0, provisional: true, demo: true, updatedAt: new Date().toISOString() };
    db.credits.unshift(batch); recordEvent(batch.id, 'Batch draft created', 'Local demo draft only; no issuance or external registry entry.'); save(); $('#modal-root').innerHTML = ''; toast('Local batch draft created.'); renderShell(); return;
  }
}

async function handleEvidenceFiles(fileList) {
  const files = Array.from(fileList || []); const target = $('#upload-progress'); if (!files.length || !target) return;
  target.hidden = false; target.innerHTML = '';
  if (backendConnected) {
    const projectId = $('#evidence-project')?.value;
    if (!projectId) { toast('Create a project before adding evidence.', true); return; }
    for (const file of files) {
      if (file.size > 10 * 1024 * 1024) { toast(`${file.name} exceeds the 10 MB limit.`, true); continue; }
      const ext = file.name.split('.').pop().toLowerCase(); const kind = ['png','jpg','jpeg','webp'].includes(ext) ? 'image' : ['csv','json'].includes(ext) ? 'data' : 'document';
      const form = new FormData(); form.append('file', file, file.name); form.append('evidence_type', kind); form.append('source_name', 'Local workspace upload');
      try {
        const record = await apiRequest(`/api/projects/${encodeURIComponent(projectId)}/evidence`, { method: 'POST', body: form });
        const row = document.createElement('div'); row.className = 'file-row'; row.innerHTML = `<span class="file-icon">✓</span><span class="file-main"><strong>${escapeHtml(record.filename)}</strong><small>Server SHA-256 · ${formatBytes(record.size_bytes)} · ${escapeHtml(record.sha256.slice(0, 16))}…</small></span><span class="tag">LOCAL STORAGE</span>`; target.appendChild(row);
      } catch (error) { toast(`${file.name}: ${error.message}`, true); }
    }
    await refreshBackend(); toast('Evidence saved in local off-chain storage; SHA-256 computed by the server.'); return;
  }
  const projectId = db.projects[0]?.id;
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) { toast(`${file.name} exceeds the 10 MB local limit.`, true); continue; }
    if (file.size === 0) { toast(`${file.name} is empty.`, true); continue; }
    let hash = '';
    try { if (!crypto.subtle) throw new Error('Secure hashing is unavailable in this context. Use localhost or HTTPS.'); hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer()))].map((b) => b.toString(16).padStart(2, '0')).join(''); }
    catch (error) { toast(error.message || 'Could not compute a SHA-256 digest.', true); continue; }
    const ext = file.name.split('.').pop().toLowerCase(); const kind = ['png','jpg','jpeg','webp'].includes(ext) ? 'Image' : ['csv','json'].includes(ext) ? 'Data' : 'Document';
    const record = { id: id('EVD'), projectId, name: file.name, kind, size: file.size, mime: file.type || 'application/octet-stream', uploadedAt: new Date().toISOString(), uploadedBy: 'Jordan Demo', hash, state: 'Not reviewed', demo: true, findings: [] };
    db.evidence.unshift(record); db.events.unshift({ id: id('EVT-DEMO'), targetId: projectId, type: 'Evidence metadata added', actor: 'Jordan Demo', reason: `${file.name} · SHA-256 computed locally. Original file was not uploaded or saved.`, at: record.uploadedAt, demo: true });
    db.credits.filter((c) => c.projectId === projectId).forEach((c) => { c.components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 }; c.components.M = Math.min(c.components.M, 45); recomputeScore(c); });
    const row = document.createElement('div'); row.className = 'file-row'; row.innerHTML = `<span class="file-icon">✓</span><span class="file-main"><strong>${escapeHtml(file.name)}</strong><small>SHA-256 computed locally · ${formatBytes(file.size)}</small></span><span class="tag">LOCAL ONLY</span>`; target.appendChild(row);
  }
  save(); toast('Evidence metadata saved locally. Original files were not uploaded.'); setTimeout(() => renderShell(), 650);
}
async function extractEvidence(evidenceId) {
  try {
    const result = await apiRequest(`/api/evidence/${encodeURIComponent(evidenceId)}/extract`, { method: 'POST' });
    toast(`Local extraction saved: ${result.candidate_claim_count} candidate claim(s), ${result.chunk_count} source chunk(s). Review candidates before use.`);
    await refreshBackend();
  } catch (error) { toast(`Could not extract this file: ${error.message}`, true); }
}

async function handleRegistryImport(file) {
  if (!file) return;
  const result = $('#registry-import-result');
  if (file.size > 5 * 1024 * 1024) { toast('CSV exceeds the 5 MB local limit.', true); return; }
  if (backendConnected) {
    const form = new FormData(); form.append('file', file, file.name);
    try {
      const imported = await apiRequest('/api/registry/import', { method: 'POST', body: form });
      if (result) result.innerHTML = `<div class="callout ${imported.potential_conflicts.length ? 'warning' : 'info'}">Imported ${imported.imported_count} rows. ${imported.potential_conflicts.length} potential serial conflict(s) found in imported data only.</div>`;
      await refreshBackend(); toast('Registry CSV imported to the database; checks cover the imported rows only.');
    } catch (error) { if (result) result.innerHTML = `<div class="callout danger">${escapeHtml(error.message)}</div>`; }
    return;
  }
  const rows = parseCsv(await file.text());
  if (!rows.length || !('external_serial' in rows[0])) { if (result) result.innerHTML = '<div class="callout danger">CSV needs an external_serial header. Use the supplied template.</div>'; return; }
  const normalized = rows.filter((r) => r.external_serial).map(normalizeImported);
  if (!normalized.length) { if (result) result.innerHTML = '<div class="callout warning">No rows with an external serial were found.</div>'; return; }
  db.importedRecords.push(...normalized);
  const serialCounts = new Map(); db.importedRecords.forEach((r) => { const serial = String(r.serial).toLowerCase(); serialCounts.set(serial, (serialCounts.get(serial) || 0) + 1); });
  db.credits.filter((c) => (serialCounts.get(c.serial.toLowerCase()) || 0) > 1).forEach((c) => { c.components = c.components || { M: 50, V: 50, C: 50, R: 50, A: 50 }; c.components.C = Math.min(c.components.C, 25); recomputeScore(c); if (!db.reviews.some((r) => r.targetId === c.id && r.state === 'Pending')) db.reviews.unshift({ id: id('REV'), targetId: c.id, targetType: 'Registry conflict', finding: 'Potential duplicate serial found in imported rows.', state: 'Pending', createdAt: new Date().toISOString(), actor: 'Deterministic registry rule', reason: '', demo: true }); recordEvent(c.id, 'Conflict detected', 'Duplicate serial found in available imported records only.'); });
  recordEvent('registry-import', 'Registry CSV imported', `${normalized.length} rows from ${file.name}; checks are limited to imported records.`); save();
  const duplicateRows = normalized.filter((n) => db.importedRecords.filter((r) => r.serial.toLowerCase() === n.serial.toLowerCase()).length > 1).length;
  if (result) result.innerHTML = `<div class="callout ${duplicateRows ? 'warning' : 'info'}">Imported ${normalized.length} local rows. ${duplicateRows} imported row(s) share a serial with an available record. This is not a live registry check.</div>`;
  toast(`${normalized.length} CSV rows imported to this browser.`);
}

function searchExplorer(query) {
  const q = query.trim().toLowerCase(); const matches = db.credits.filter((c) => `${c.id} ${c.serial} ${projectFor(c.projectId)?.name || ''}`.toLowerCase().includes(q));
  $('#explorer-results').innerHTML = matches.length ? matches.map((c) => `<div class="file-row"><span class="file-icon">◈</span><span class="file-main"><strong>${escapeHtml(c.id)}</strong><small>${escapeHtml(projectFor(c.projectId)?.name || c.projectId)} · ${escapeHtml(c.serial)}</small></span>${statusTag(c.state)}<a class="table-action" href="verify.html?batch=${encodeURIComponent(c.id)}">Public view →</a></div>`).join('') : emptyMini('No matching local record.', 'Search checks records available to this local API workspace.');
}
async function saveSettings(form) {
  const data = new FormData(form); db.settings = { ...db.settings, displayName: String(data.get('name')).trim(), email: String(data.get('email')).trim(), location: String(data.get('location')).trim(), organization: String(data.get('organization')).trim() }; save(); toast('Local preferences saved.'); renderShell();
  if (backendConnected) {
    try { await apiRequest('/api/me', { method: 'PUT', body: { display_name: String(data.get('name')).trim(), email: String(data.get('email')).trim(), location: String(data.get('location')).trim(), organization: String(data.get('organization')).trim() } }); await refreshBackend(); toast('Profile saved to the local database.'); }
    catch (error) { toast(error.message, true); }
    return;
  }
}

window.addEventListener('hashchange', () => { activeProjectTab = 'Overview'; assessmentResult = null; renderShell(); });
document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#global-search').focus(); }
  if (event.key === 'Escape') { $('#modal-root').innerHTML = ''; closeSidebar(); $('#search-results').hidden = true; }
});
document.addEventListener('click', (event) => { if (!event.target.closest('.global-search')) $('#search-results').hidden = true; });

renderNav();
$('.skip-link')?.addEventListener('click', (event) => {
  event.preventDefault();
  $('#page-content').focus();
  $('#page-content').scrollIntoView({ block: 'start' });
});
if (!location.hash) location.hash = '#/dashboard';
renderShell();
initializeBackend();
