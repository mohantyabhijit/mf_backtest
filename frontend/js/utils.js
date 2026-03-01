/**
 * utils.js — Shared helpers
 */

export function formatCurrency(value, compact = false) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  if (compact) {
    if (Math.abs(value) >= 1e7) return "₹" + (value / 1e7).toFixed(2) + "Cr";
    if (Math.abs(value) >= 1e5) return "₹" + (value / 1e5).toFixed(2) + "L";
    if (Math.abs(value) >= 1e3) return "₹" + (value / 1e3).toFixed(1) + "K";
    return "₹" + value.toFixed(0);
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  }).format(value);
}

export function formatPct(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return value.toFixed(decimals) + "%";
}

export function formatNum(value, decimals = 3) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return value.toFixed(decimals);
}

export function setLoading(elementId, isLoading, text = "Loading...") {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (isLoading) {
    el.classList.add("loading");
    el.dataset.originalText = el.textContent;
    el.textContent = text;
    el.disabled = true;
  } else {
    el.classList.remove("loading");
    if (el.dataset.originalText) el.textContent = el.dataset.originalText;
    el.disabled = false;
  }
}

export function showError(containerId, message) {
  const el = document.getElementById(containerId);
  if (el) {
    el.innerHTML = `<div class="error-msg">⚠️ ${message}</div>`;
  }
}

export function showStatus(message, type = "info") {
  const bar = document.getElementById("status-bar");
  if (bar) {
    bar.textContent = message;
    bar.className = `status-bar status-${type}`;
    bar.style.display = "block";
    if (type !== "error") setTimeout(() => { bar.style.display = "none"; }, 4000);
  }
}

export const CHART_COLORS = [
  "#4A90D9", "#7ED321", "#E74C3C", "#9B59B6",
  "#F39C12", "#1ABC9C", "#27AE60", "#E67E22",
];
