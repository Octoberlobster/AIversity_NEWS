// src/api.js
export const API_BASE =
  process.env.REACT_APP_API_BASE || 'http://localhost:5000';

export async function fetchJson(body) {
  const res = await fetch(`${API_BASE}/api`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(res.status + ' ' + txt);
  }
  return res.json();
}
