/**
 * app.js — Main controller for MF Backtest frontend
 */
import { fetchStrategies, fetchFunds, runBacktest, runAll, fetchNavHistory, fetchSipProjection } from "./api.js";
import {
  renderStrategyComparison, renderPortfolioGrowth, renderDrawdown,
  renderAllocationPie, renderSIPSchedule, renderMultiGrowth, renderProjection,
} from "./charts.js";
import { formatCurrency, formatPct, formatNum, setLoading, showError, showStatus } from "./utils.js";

// ─── State ────────────────────────────────────────────────────────────────────
let allStrategies = [];
let allFunds = [];
let fundNameMap = {};
let lastComparisonResults = [];

// ─── Tab Navigation ───────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(target)?.classList.add("active");
    });
  });
}

// ─── Load initial data ────────────────────────────────────────────────────────
async function loadInitialData() {
  try {
    [allStrategies, allFunds] = await Promise.all([fetchStrategies(), fetchFunds()]);
    fundNameMap = Object.fromEntries(allFunds.map((f) => [f.id, f.name]));
    populateStrategySelects();
    populateFundSelect();
    renderFundsTable();
    showStatus("Data loaded. Ready to run backtests.", "success");
  } catch (e) {
    showStatus("⚠️ Could not load data. Please run seed_data.py first.", "error");
  }
}

function populateStrategySelects() {
  const selects = document.querySelectorAll(".strategy-select");
  selects.forEach((sel) => {
    sel.innerHTML = allStrategies
      .map((s) => `<option value="${s.id}">${s.id}: ${s.name}</option>`)
      .join("");
  });
}

function populateFundSelect() {
  const sel = document.getElementById("fund-select");
  if (!sel) return;
  const categories = [...new Set(allFunds.map((f) => f.category))].sort();
  sel.innerHTML = categories.map((cat) => {
    const opts = allFunds
      .filter((f) => f.category === cat)
      .map((f) => `<option value="${f.id}">${f.name} (${f.data_from || "no data"} – ${f.data_to || "no data"})</option>`)
      .join("");
    return `<optgroup label="${cat.replace(/_/g, " ").toUpperCase()}">${opts}</optgroup>`;
  }).join("");
}

// ─── Comparison Tab ───────────────────────────────────────────────────────────
function getComparisonParams() {
  return {
    start_date: document.getElementById("comp-start")?.value || "2000-01-01",
    end_date: document.getElementById("comp-end")?.value || "2024-12-31",
    monthly_sip: parseFloat(document.getElementById("comp-sip")?.value || 75000),
    stepup_pct: parseFloat(document.getElementById("comp-stepup")?.value || 10),
  };
}

async function runComparison() {
  setLoading("btn-compare", true, "Running…");
  try {
    const params = getComparisonParams();
    const results = await runAll(params);
    lastComparisonResults = results.filter((r) => !r.error);
    renderComparisonTable(lastComparisonResults);
    const metric = document.getElementById("comp-metric")?.value || "cagr";
    renderStrategyComparison(lastComparisonResults, metric);
    renderMultiGrowth(lastComparisonResults);
    showStatus("Comparison complete.", "success");
  } catch (e) {
    showError("comparison-table-container", e.message);
    showStatus("Error: " + e.message, "error");
  } finally {
    setLoading("btn-compare", false);
  }
}

function renderComparisonTable(results) {
  const container = document.getElementById("comparison-table-container");
  if (!container || !results.length) return;

  const rows = results.map((r) => `
    <tr>
      <td><span class="color-dot" style="background:${r.color}"></span>${r.name}</td>
      <td class="num ${r.cagr >= 14 ? 'highlight' : ''}">${formatPct(r.cagr)}</td>
      <td class="num">${formatPct(r.xirr)}</td>
      <td class="num">${formatPct(r.absolute_return)}</td>
      <td class="num">${formatCurrency(r.total_invested, true)}</td>
      <td class="num">${formatCurrency(r.final_value, true)}</td>
      <td class="num">${formatCurrency(r.gain, true)}</td>
      <td class="num ${r.max_drawdown < -40 ? 'warn' : ''}">${formatPct(r.max_drawdown)}</td>
      <td class="num">${formatPct(r.volatility)}</td>
      <td class="num">${formatNum(r.sharpe_ratio)}</td>
      <td><button class="btn-sm btn-secondary" onclick="deepDiveFromTable('${r.strategy_id}')">Deep Dive →</button></td>
    </tr>
  `).join("");

  container.innerHTML = `
    <div class="table-scroll">
    <table class="data-table">
      <thead><tr>
        <th>Strategy</th>
        <th>CAGR</th><th>XIRR</th><th>Abs. Return</th>
        <th>Invested</th><th>Final Value</th><th>Gain</th>
        <th>Max DD</th><th>Volatility</th><th>Sharpe</th><th></th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
    </div>
  `;
}

window.deepDiveFromTable = function (strategyId) {
  document.querySelector('[data-tab="deep-dive"]')?.click();
  document.getElementById("dive-strategy").value = strategyId;
  runDeepDive();
};

document.getElementById("comp-metric")?.addEventListener("change", () => {
  if (lastComparisonResults.length)
    renderStrategyComparison(lastComparisonResults, document.getElementById("comp-metric").value);
});

// ─── Deep Dive Tab ────────────────────────────────────────────────────────────
async function runDeepDive() {
  const strategyId = document.getElementById("dive-strategy")?.value;
  if (!strategyId) return;

  setLoading("btn-dive", true, "Simulating…");
  try {
    const params = {
      strategy_id: strategyId,
      start_date: document.getElementById("dive-start")?.value || "2000-01-01",
      end_date: document.getElementById("dive-end")?.value || "2024-12-31",
      monthly_sip: parseFloat(document.getElementById("dive-sip")?.value || 75000),
      stepup_pct: parseFloat(document.getElementById("dive-stepup")?.value || 10),
    };
    const result = await runBacktest(params);
    renderDeepDive(result);
    showStatus(`Deep dive complete: ${result.strategy?.name}`, "success");
  } catch (e) {
    showError("dive-metrics", e.message);
    showStatus("Error: " + e.message, "error");
  } finally {
    setLoading("btn-dive", false);
  }
}

function renderDeepDive(result) {
  // Metrics cards
  const container = document.getElementById("dive-metrics");
  if (container) {
    const s = result.strategy;
    container.innerHTML = `
      <div class="metrics-grid">
        <div class="metric-card highlight-card">
          <div class="metric-label">CAGR</div>
          <div class="metric-value">${formatPct(result.cagr)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">XIRR</div>
          <div class="metric-value">${formatPct(result.xirr)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Absolute Return</div>
          <div class="metric-value">${formatPct(result.absolute_return)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Total Invested</div>
          <div class="metric-value">${formatCurrency(result.total_invested)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Final Corpus</div>
          <div class="metric-value large">${formatCurrency(result.final_value)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Gain</div>
          <div class="metric-value">${formatCurrency(result.gain)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Max Drawdown</div>
          <div class="metric-value ${result.max_drawdown < -40 ? 'warn' : ''}">${formatPct(result.max_drawdown)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Volatility (Ann.)</div>
          <div class="metric-value">${formatPct(result.volatility)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Sharpe Ratio</div>
          <div class="metric-value">${formatNum(result.sharpe_ratio)}</div>
        </div>
      </div>
      <p class="strategy-desc">${s?.description || ""}</p>
    `;
  }

  if (result.chart_data) renderPortfolioGrowth(result.chart_data, result.strategy?.name, result.strategy?.color);
  if (result.drawdown_data) renderDrawdown(result.drawdown_data);
  if (result.strategy?.allocations) renderAllocationPie(result.strategy.allocations, fundNameMap);
  if (result.sip_schedule) {
    renderSIPSchedule(result.sip_schedule);
    renderSIPScheduleTable(result.sip_schedule);
  }
  renderExportBtn(result);
}

function renderSIPScheduleTable(schedule) {
  const el = document.getElementById("sip-table");
  if (!el) return;
  const rows = schedule.map((s) => `
    <tr>
      <td>${s.year}</td>
      <td>${formatCurrency(s.monthly_sip)}</td>
      <td>${formatCurrency(s.annual_sip)}</td>
      <td>${formatCurrency(s.cumulative_invested)}</td>
    </tr>
  `).join("");
  el.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Year</th><th>Monthly SIP</th><th>Annual SIP</th><th>Cumulative Invested</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderExportBtn(result) {
  const container = document.getElementById("export-container");
  if (!container || !result.chart_data) return;
  container.innerHTML = `<button class="btn btn-secondary" id="btn-export">⬇ Export CSV</button>`;
  document.getElementById("btn-export").addEventListener("click", () => exportCSV(result));
}

function exportCSV(result) {
  const rows = [["Date", "Portfolio Value", "Total Invested", "Gain"]];
  result.chart_data.forEach((d) => {
    rows.push([d.date, d.portfolio_value, d.total_invested, (d.portfolio_value - d.total_invested).toFixed(0)]);
  });
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `mf_backtest_${result.strategy?.id || "result"}.csv`;
  a.click();
}

// ─── SIP Calculator Tab ───────────────────────────────────────────────────────
async function calcProjection() {
  setLoading("btn-project", true, "Calculating…");
  try {
    const params = {
      monthly_sip: parseFloat(document.getElementById("proj-sip")?.value || 75000),
      stepup_pct: parseFloat(document.getElementById("proj-stepup")?.value || 10),
      years: parseInt(document.getElementById("proj-years")?.value || 15),
      expected_return: parseFloat(document.getElementById("proj-return")?.value || 14),
    };
    const result = await fetchSipProjection(params);
    renderProjection(result.projections);
    renderProjectionSummary(result);
    showStatus("Projection calculated.", "success");
  } catch (e) {
    showError("projection-summary", e.message);
  } finally {
    setLoading("btn-project", false);
  }
}

function renderProjectionSummary(result) {
  const el = document.getElementById("projection-summary");
  if (!el) return;
  el.innerHTML = `
    <div class="metrics-grid">
      <div class="metric-card highlight-card">
        <div class="metric-label">Projected Corpus</div>
        <div class="metric-value large">${formatCurrency(result.final_corpus)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Total Invested</div>
        <div class="metric-value">${formatCurrency(result.total_invested)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Wealth Multiplier</div>
        <div class="metric-value">${(result.final_corpus / result.total_invested).toFixed(2)}x</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Expected Return</div>
        <div class="metric-value">${formatPct(result.expected_return_pct)}</div>
      </div>
    </div>
  `;
}

// Live update on input change
document.querySelectorAll("#calc-tab input").forEach((input) => {
  input.addEventListener("input", debounce(calcProjection, 600));
});

// ─── Fund Explorer Tab ────────────────────────────────────────────────────────
function renderFundsTable() {
  const container = document.getElementById("funds-table-container");
  if (!container || !allFunds.length) return;
  const rows = allFunds.map((f) => `
    <tr>
      <td>${f.name}</td>
      <td><span class="badge badge-${f.category}">${f.category.replace(/_/g, " ")}</span></td>
      <td>${f.amfi_code || "—"}</td>
      <td>${f.launch_date || "—"}</td>
      <td>${f.data_from || "No data"}</td>
      <td>${f.data_to || "No data"}</td>
      <td><button class="btn-sm btn-secondary" onclick="viewFundNav('${f.id}')">View NAV</button></td>
    </tr>
  `).join("");
  container.innerHTML = `
    <div class="table-scroll">
    <table class="data-table">
      <thead><tr><th>Fund</th><th>Category</th><th>AMFI Code</th><th>Launch</th><th>Data From</th><th>Data To</th><th></th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    </div>
  `;
}

window.viewFundNav = async function(fundId) {
  document.getElementById("fund-select").value = fundId;
  await loadFundNav();
};

async function loadFundNav() {
  const fundId = document.getElementById("fund-select")?.value;
  if (!fundId) return;
  setLoading("btn-load-nav", true, "Loading…");
  try {
    const start = document.getElementById("nav-start")?.value || "2000-01-01";
    const end   = document.getElementById("nav-end")?.value   || "2024-12-31";
    const data  = await fetchNavHistory(fundId, start, end);
    renderNavChart(data);
    showStatus(`Loaded ${data.nav_data.length} NAV records for ${data.fund.name}`, "success");
  } catch (e) {
    showStatus("Error: " + e.message, "error");
  } finally {
    setLoading("btn-load-nav", false);
  }
}

function renderNavChart(data) {
  const container = document.getElementById("nav-chart-container");
  if (!container) return;
  container.innerHTML = '<canvas id="nav-chart"></canvas>';
  const canvas = document.getElementById("nav-chart");
  const labels = data.nav_data.map((d) => d.date);
  const values = data.nav_data.map((d) => d.nav);

  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: data.fund.name,
        data: values,
        borderColor: "#4A90D9",
        backgroundColor: "rgba(74,144,217,0.1)",
        fill: true,
        pointRadius: 0,
        tension: 0.2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: {
        y: { ticks: { callback: (v) => "₹" + v.toFixed(2) } },
        x: { ticks: { maxTicksLimit: 12, maxRotation: 0 } },
      },
    },
  });
}

// ─── Utility ──────────────────────────────────────────────────────────────────
function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ─── Event Bindings ───────────────────────────────────────────────────────────
document.getElementById("btn-compare")?.addEventListener("click", runComparison);
document.getElementById("btn-dive")?.addEventListener("click", runDeepDive);
document.getElementById("btn-project")?.addEventListener("click", calcProjection);
document.getElementById("btn-load-nav")?.addEventListener("click", loadFundNav);

// ─── Init ─────────────────────────────────────────────────────────────────────
initTabs();
loadInitialData().then(() => {
  // Auto-run projection on load
  calcProjection();
});
