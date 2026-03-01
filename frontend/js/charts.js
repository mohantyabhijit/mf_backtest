/**
 * charts.js — Chart.js wrappers for MF Backtest
 */

import { formatCurrency, formatPct, CHART_COLORS } from "./utils.js";

const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

// ─── Strategy Comparison Bar Chart ───────────────────────────────────────────

export function renderStrategyComparison(results, metric = "cagr") {
  destroyChart("comparison");
  const canvas = document.getElementById("comparison-chart");
  if (!canvas) return;

  const labels = results.map((r) => r.name);
  const values = results.map((r) => r[metric] ?? 0);
  const colors = results.map((r) => r.color || "#4A90D9");

  chartInstances["comparison"] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: metricLabel(metric),
          data: values,
          backgroundColor: colors.map((c) => c + "CC"),
          borderColor: colors,
          borderWidth: 2,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => formatMetricValue(metric, ctx.parsed.y),
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => formatMetricValue(metric, v),
          },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: {
          ticks: { maxRotation: 30 },
          grid: { display: false },
        },
      },
    },
  });
}

// ─── Portfolio Growth Line Chart ──────────────────────────────────────────────

export function renderPortfolioGrowth(chartData, strategyName, color) {
  destroyChart("growth");
  const canvas = document.getElementById("growth-chart");
  if (!canvas) return;

  const labels = chartData.map((d) => d.date);
  const portfolioValues = chartData.map((d) => d.portfolio_value);
  const investedValues = chartData.map((d) => d.total_invested);

  chartInstances["growth"] = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Portfolio Value",
          data: portfolioValues,
          borderColor: color || "#4A90D9",
          backgroundColor: (color || "#4A90D9") + "20",
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "Total Invested",
          data: investedValues,
          borderColor: "#888",
          backgroundColor: "rgba(136,136,136,0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
          borderDash: [5, 3],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        y: {
          ticks: { callback: (v) => formatCurrency(v, true) },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: {
          ticks: { maxTicksLimit: 12, maxRotation: 0 },
          grid: { display: false },
        },
      },
    },
  });
}

// ─── Drawdown Chart ───────────────────────────────────────────────────────────

export function renderDrawdown(drawdownData) {
  destroyChart("drawdown");
  const canvas = document.getElementById("drawdown-chart");
  if (!canvas) return;

  const labels = drawdownData.map((d) => d.date);
  const values = drawdownData.map((d) => d.drawdown);

  chartInstances["drawdown"] = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Drawdown %",
          data: values,
          borderColor: "#E74C3C",
          backgroundColor: "rgba(231,76,60,0.2)",
          fill: true,
          tension: 0.2,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          ticks: { callback: (v) => `${v.toFixed(1)}%` },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: {
          ticks: { maxTicksLimit: 12, maxRotation: 0 },
          grid: { display: false },
        },
      },
    },
  });
}

// ─── Allocation Pie Chart ─────────────────────────────────────────────────────

export function renderAllocationPie(allocations, fundNames) {
  destroyChart("pie");
  const canvas = document.getElementById("allocation-pie");
  if (!canvas) return;

  const labels = Object.keys(allocations).map(
    (id) => fundNames[id] || id
  );
  const values = Object.values(allocations).map((v) => (v * 100).toFixed(1));
  const colors = [
    "#4A90D9", "#7ED321", "#E74C3C", "#9B59B6",
    "#F39C12", "#1ABC9C", "#27AE60", "#E67E22",
  ];

  chartInstances["pie"] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderWidth: 2 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { boxWidth: 14 } },
        tooltip: {
          callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed}%` },
        },
      },
    },
  });
}

// ─── SIP Schedule Bar Chart ───────────────────────────────────────────────────

export function renderSIPSchedule(schedule) {
  destroyChart("sip-schedule");
  const canvas = document.getElementById("sip-schedule-chart");
  if (!canvas) return;

  const labels = schedule.map((s) => s.year);
  const monthly = schedule.map((s) => s.monthly_sip);
  const cumulative = schedule.map((s) => s.cumulative_invested);

  chartInstances["sip-schedule"] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Monthly SIP (₹)",
          data: monthly,
          backgroundColor: "#4A90D9CC",
          borderColor: "#4A90D9",
          borderWidth: 1,
          yAxisID: "y",
        },
        {
          label: "Cumulative Invested (₹)",
          data: cumulative,
          type: "line",
          borderColor: "#F39C12",
          backgroundColor: "transparent",
          pointRadius: 3,
          yAxisID: "y2",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index" },
      plugins: { legend: { position: "top" } },
      scales: {
        y: {
          position: "left",
          ticks: { callback: (v) => formatCurrency(v, true) },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        y2: {
          position: "right",
          ticks: { callback: (v) => formatCurrency(v, true) },
          grid: { display: false },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// ─── Multi-strategy growth comparison ────────────────────────────────────────

export function renderMultiGrowth(results) {
  destroyChart("multi-growth");
  const canvas = document.getElementById("multi-growth-chart");
  if (!canvas) return;

  // All results have chart_data; use dates from first result
  const labels = results[0]?.chart_data?.map((d) => d.date) || [];
  const datasets = results
    .filter((r) => r.chart_data)
    .map((r) => ({
      label: r.name,
      data: r.chart_data.map((d) => d.portfolio_value),
      borderColor: r.color || "#4A90D9",
      backgroundColor: "transparent",
      tension: 0.3,
      pointRadius: 0,
      borderWidth: 2,
    }));

  chartInstances["multi-growth"] = new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top" } },
      scales: {
        y: {
          ticks: { callback: (v) => formatCurrency(v, true) },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: {
          ticks: { maxTicksLimit: 12, maxRotation: 0 },
          grid: { display: false },
        },
      },
    },
  });
}

// ─── SIP Projection Line Chart ────────────────────────────────────────────────

export function renderProjection(projections) {
  destroyChart("projection");
  const canvas = document.getElementById("projection-chart");
  if (!canvas) return;

  const labels = projections.map((p) => p.year);
  const corpus = projections.map((p) => p.corpus);

  chartInstances["projection"] = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Projected Corpus",
          data: corpus,
          borderColor: "#1ABC9C",
          backgroundColor: "rgba(26,188,156,0.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          ticks: { callback: (v) => formatCurrency(v, true) },
          grid: { color: "rgba(255,255,255,0.05)" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function metricLabel(metric) {
  const map = {
    cagr: "CAGR (%)", xirr: "XIRR (%)",
    absolute_return: "Absolute Return (%)",
    final_value: "Final Value (₹)", sharpe_ratio: "Sharpe Ratio",
    max_drawdown: "Max Drawdown (%)", volatility: "Volatility (%)",
  };
  return map[metric] || metric;
}

function formatMetricValue(metric, v) {
  if (["cagr","xirr","absolute_return","max_drawdown","volatility"].includes(metric))
    return `${v.toFixed(2)}%`;
  if (metric === "final_value") return formatCurrency(v, true);
  return v.toFixed(3);
}
