// Talk to the backend on port 8000 using whatever host/IP the browser used
// to reach this frontend - so this works identically over localhost or a
// LAN IP without any per-machine configuration.
const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

const TOKEN_KEY = "cgl_token";
const USER_KEY = "cgl_user";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function logout() {
  clearSession();
  window.location.href = "index.html";
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "index.html";
  }
}

async function apiFetch(path, options = {}) {
  const headers = Object.assign({}, options.headers || {});
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let data = null;
  try {
    data = await resp.json();
  } catch (e) {
    data = null;
  }
  if (!resp.ok) {
    const message = (data && data.detail) || `Request failed (${resp.status})`;
    const err = new Error(message);
    err.status = resp.status;
    throw err;
  }
  return data;
}
