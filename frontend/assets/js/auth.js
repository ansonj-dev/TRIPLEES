const TOKEN_KEY = 'vericarb-api-demo-token';
let mode = 'login';
const form = document.querySelector('#auth-form');
const message = document.querySelector('#auth-message');
const showMessage = (text, isError = false) => { message.textContent = text; message.classList.toggle('error', isError); message.hidden = false; };
function setMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll('.auth-tab').forEach((tab) => { const active = tab.dataset.authMode === mode; tab.classList.toggle('active', active); tab.setAttribute('aria-selected', String(active)); });
  document.querySelectorAll('[data-signup-only]').forEach((node) => { node.hidden = mode !== 'signup'; });
  document.querySelector('#auth-title').textContent = mode === 'signup' ? 'Create your workspace' : 'Welcome back';
  document.querySelector('#auth-subtitle').textContent = mode === 'signup' ? 'Create a local prototype account to start tracking projects.' : 'Sign in to your local TRIPLEES workspace.';
  document.querySelector('#auth-submit').textContent = mode === 'signup' ? 'Create account' : 'Sign in';
  document.querySelector('#auth-password').autocomplete = mode === 'signup' ? 'new-password' : 'current-password';
  message.hidden = true;
}
document.querySelectorAll('[data-auth-mode]').forEach((tab) => tab.addEventListener('click', () => setMode(tab.dataset.authMode)));
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const fields = new FormData(form);
  const payload = mode === 'signup'
    ? { display_name: fields.get('display_name'), email: fields.get('email'), password: fields.get('password'), organization: fields.get('organization') || null }
    : { email: fields.get('email'), password: fields.get('password') };
  const button = document.querySelector('#auth-submit'); button.disabled = true; button.textContent = mode === 'signup' ? 'Creating account…' : 'Signing in…';
  try {
    const response = await fetch(mode === 'signup' ? '/api/auth/signup' : '/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || result.detail?.message || 'Could not authenticate.');
    localStorage.setItem(TOKEN_KEY, result.access_token);
    window.location.replace('app.html#/dashboard');
  } catch (error) { showMessage(error.message, true); }
  finally { button.disabled = false; button.textContent = mode === 'signup' ? 'Create account' : 'Sign in'; }
});
document.querySelector('#demo-login').addEventListener('click', async () => {
  const button = document.querySelector('#demo-login'); button.disabled = true; button.textContent = 'Opening demo workspace…';
  try {
    const response = await fetch('/api/auth/demo', { method: 'POST' }); const result = await response.json();
    if (!response.ok) throw new Error(result.detail?.message || 'Demo sign-in is unavailable.');
    localStorage.setItem(TOKEN_KEY, result.access_token);
    window.location.replace('app.html#/dashboard');
  } catch (error) { showMessage(error.message, true); button.disabled = false; button.textContent = 'Explore the demo workspace'; }
});
setMode('login');
