/**
 * Admin API service — all /api/admin/* calls with auto-token injection.
 * Auto-redirects to /admin/login on any 401 response.
 */

const BASE = "/api/admin";

export function getToken() {
  return localStorage.getItem("adminToken") || "";
}

export function hasToken() {
  return !!localStorage.getItem("adminToken");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  };
}

/** On 401 — clear token and bounce to login page */
function _handle401() {
  localStorage.removeItem("adminToken");
  window.location.href = "/admin/login";
}

async function _checkAuth(res) {
  if (res.status === 401) {
    _handle401();
    throw new Error("Session expired. Redirecting to login…");
  }
  return res;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function adminLogin(username, password) {
  const res = await fetch(`${BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Login failed");
  localStorage.setItem("adminToken", data.token);
  return data;
}

export async function adminVerify() {
  const token = getToken();
  console.log('[adminVerify] token in localStorage:', token ? token.substring(0, 20) + '...' : 'NONE');
  const res = await fetch(`${BASE}/verify`, { headers: authHeaders() });
  console.log('[adminVerify] response status:', res.status);
  return res.ok;
}

export function adminLogout() {
  localStorage.removeItem("adminToken");
}

// ── Datasets ─────────────────────────────────────────────────────────────────

export async function fetchDatasets() {
  console.log('[fetchDatasets] calling GET /api/admin/datasets');
  console.log('[fetchDatasets] token:', getToken() ? getToken().substring(0, 20) + '...' : 'NONE');
  const res = await _checkAuth(
    await fetch(`${BASE}/datasets`, { headers: authHeaders() })
  );
  console.log('[fetchDatasets] response status:', res.status);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  const data = await res.json();
  console.log('[fetchDatasets] datasets received:', data.length, data);
  return data;
}

export async function uploadDataset(formData) {
  if (!hasToken()) { console.error('[uploadDataset] No token — redirecting to login'); _handle401(); return; }
  console.log('[uploadDataset] token:', getToken().substring(0, 20) + '...');
  console.log('[uploadDataset] FormData entries:');
  for (const [k, v] of formData.entries()) {
    console.log(`  ${k}:`, v instanceof File ? `File(${v.name}, ${v.size}b)` : v);
  }
  const res = await _checkAuth(
    await fetch(`${BASE}/datasets/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${getToken()}` },
      body: formData,
    })
  );
  console.log('[uploadDataset] response status:', res.status);
  const data = await res.json();
  console.log('[uploadDataset] response body:', data);
  if (!res.ok) throw new Error(data.error || `Upload failed (${res.status})`);
  return data;
}

export async function deleteDataset(datasetId) {
  const res = await _checkAuth(
    await fetch(`${BASE}/datasets/${datasetId}`, {
      method: "DELETE",
      headers: authHeaders(),
    })
  );
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
}

// ── Training ─────────────────────────────────────────────────────────────────

export async function startTraining(datasetId) {
  const res = await _checkAuth(
    await fetch(`${BASE}/train/${datasetId}`, {
      method: "POST",
      headers: authHeaders(),
    })
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.message || "Training failed to start");
  return data;
}

export async function fetchTrainStatus() {
  const res = await _checkAuth(
    await fetch(`${BASE}/train/status`, { headers: authHeaders() })
  );
  if (!res.ok) throw new Error("Failed to fetch training status");
  return res.json();
}

// ── Results (public) ─────────────────────────────────────────────────────────

export async function fetchResults() {
  const res = await fetch(`${BASE}/results`);
  if (!res.ok) throw new Error("Failed to fetch results");
  return res.json();
}

export async function fetchResult(datasetId) {
  const res = await fetch(`${BASE}/results/${datasetId}`);
  if (!res.ok) throw new Error("Result not found");
  return res.json();
}
