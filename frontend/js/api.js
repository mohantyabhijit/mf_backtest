/**
 * api.js — Fetch helpers for MF Backtest backend
 */

const API_BASE = "/api";

async function apiFetch(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

export async function fetchStrategies() {
  return apiFetch("/strategies");
}

export async function fetchFunds() {
  return apiFetch("/funds");
}

export async function runBacktest(params) {
  return apiFetch("/run", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function runAll(params) {
  return apiFetch("/run-all", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function fetchNavHistory(fundId, start, end) {
  const qs = new URLSearchParams({ start, end }).toString();
  return apiFetch(`/nav/${fundId}?${qs}`);
}

export async function fetchSipProjection(params) {
  return apiFetch("/sip-projection", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
