/**
 * dataExplorer.js — Data Explorer functionality
 */

// ─── Data Explorer State ─────────────────────────────────────────────────
let explorerTables = [];
let explorerCurrentTable = '';
let explorerCurrentPage = 1;
let explorerCurrentPerPage = 50;
let explorerTotalPages = 1;

// ─── Initialize Data Explorer ────────────────────────────────────────────
export async function initDataExplorer() {
  initExplorerTabs();
  await loadDatabaseInfo();
  await loadExplorerTables();
  attachEventListeners();
  
  // Add keyboard shortcuts
  document.getElementById('explorer-sql-query')?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      executeExplorerQuery();
    }
  });
}

// ─── Attach Event Listeners ─────────────────────────────────────────────
function attachEventListeners() {
  // Table controls
  document.getElementById('explorer-table-select')?.addEventListener('change', loadExplorerTableData);
  document.getElementById('explorer-per-page')?.addEventListener('change', loadExplorerTableData);
  document.getElementById('explorer-prev-page')?.addEventListener('click', explorerPrevPage);
  document.getElementById('explorer-next-page')?.addEventListener('click', explorerNextPage);
  
  // Query controls
  document.getElementById('execute-query-btn')?.addEventListener('click', executeExplorerQuery);
  document.getElementById('clear-query-btn')?.addEventListener('click', clearExplorerQuery);
  document.getElementById('sample-query-btn')?.addEventListener('click', loadSampleQuery);
  
  // Schema controls
  document.getElementById('explorer-schema-table-select')?.addEventListener('change', loadExplorerTableSchema);
}

// ─── Explorer Tab Navigation ─────────────────────────────────────────────
function initExplorerTabs() {
  document.querySelectorAll(".explorer-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.explorerTab;
      document.querySelectorAll(".explorer-tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".explorer-tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`explorer-${target}`)?.classList.add("active");
    });
  });
}

// ─── Database Info ───────────────────────────────────────────────────────
async function loadDatabaseInfo() {
  try {
    const response = await fetch('/api/data-explorer/info');
    const data = await response.json();
    
    if (data.error) {
      console.error('Database info error:', data.error);
      return;
    }
    
    document.getElementById('db-size').textContent = `${data.database_size_mb} MB`;
    document.getElementById('db-tables').textContent = data.total_tables;
    document.getElementById('db-records').textContent = data.total_records.toLocaleString();
    document.getElementById('sqlite-version').textContent = data.sqlite_version;
  } catch (error) {
    console.error('Error loading database info:', error);
  }
}

// ─── Tables Management ───────────────────────────────────────────────────
async function loadExplorerTables() {
  try {
    const response = await fetch('/api/data-explorer/tables');
    const data = await response.json();
    
    if (data.error) {
      console.error('Tables error:', data.error);
      return;
    }
    
    explorerTables = data.tables;
    populateExplorerTableSelects();
  } catch (error) {
    console.error('Error loading tables:', error);
  }
}

function populateExplorerTableSelects() {
  const tableSelect = document.getElementById('explorer-table-select');
  const schemaSelect = document.getElementById('explorer-schema-table-select');
  
  const options = explorerTables
    .map(table => `<option value="${table.name}">${table.name} (${table.count.toLocaleString()} records)</option>`)
    .join('');
  
  if (tableSelect) {
    tableSelect.innerHTML = '<option value="">Select a table...</option>' + options;
  }
  
  if (schemaSelect) {
    schemaSelect.innerHTML = '<option value="">Select a table...</option>' + options;
  }
}

// ─── Table Data Loading ──────────────────────────────────────────────────
async function loadExplorerTableData() {
  const tableSelect = document.getElementById('explorer-table-select');
  const tableName = tableSelect?.value;
  
  if (!tableName) {
    document.getElementById('explorer-table-data').innerHTML = 
      '<p style="color:var(--text-muted);text-align:center;padding:2rem;">Select a table to view its data</p>';
    return;
  }
  
  explorerCurrentTable = tableName;
  explorerCurrentPage = 1;
  await fetchExplorerTableData();
};

async function fetchExplorerTableData() {
  if (!explorerCurrentTable) return;
  
  try {
    document.getElementById('explorer-table-data').innerHTML = 
      '<div style="text-align:center;padding:2rem;"><div class="spinner"></div><p>Loading...</p></div>';
    
    const response = await fetch(
      `/api/data-explorer/table/${explorerCurrentTable}?page=${explorerCurrentPage}&per_page=${explorerCurrentPerPage}`
    );
    const data = await response.json();
    
    if (data.error) {
      document.getElementById('explorer-table-data').innerHTML = 
        `<div class="error-msg">Error: ${data.error}</div>`;
      return;
    }
    
    explorerTotalPages = data.total_pages;
    updateExplorerPagination();
    renderExplorerTableData(data);
    
  } catch (error) {
    console.error('Error loading table data:', error);
    document.getElementById('explorer-table-data').innerHTML = 
      `<div class="error-msg">Error loading data: ${error.message}</div>`;
  }
}

function renderExplorerTableData(data) {
  const container = document.getElementById('explorer-table-data');
  
  if (data.data.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem;">No data found</p>';
    return;
  }
  
  const tableHtml = `
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            ${data.columns.map(col => `<th>${col}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.data.map(row => `
            <tr>
              ${data.columns.map(col => `<td>${formatCellValue(row[col])}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div style="margin-top:1rem;font-size:0.85rem;color:var(--text-muted);">
      Showing ${data.data.length} of ${data.total.toLocaleString()} records
    </div>
  `;
  
  container.innerHTML = tableHtml;
}

function formatCellValue(value) {
  if (value === null || value === undefined) return '<em>NULL</em>';
  if (typeof value === 'string' && value.length > 100) {
    return value.substring(0, 100) + '...';
  }
  return String(value);
}

// ─── Pagination ──────────────────────────────────────────────────────────
function updateExplorerPagination() {
  const pageInfo = document.getElementById('explorer-page-info');
  const prevBtn = document.getElementById('explorer-prev-page');
  const nextBtn = document.getElementById('explorer-next-page');
  const perPageSelect = document.getElementById('explorer-per-page');
  
  if (pageInfo) {
    pageInfo.textContent = `Page ${explorerCurrentPage} of ${explorerTotalPages}`;
  }
  
  if (prevBtn) {
    prevBtn.disabled = explorerCurrentPage <= 1;
  }
  
  if (nextBtn) {
    nextBtn.disabled = explorerCurrentPage >= explorerTotalPages;
  }
  
  if (perPageSelect) {
    explorerCurrentPerPage = parseInt(perPageSelect.value);
  }
}

function explorerPrevPage() {
  if (explorerCurrentPage > 1) {
    explorerCurrentPage--;
    fetchExplorerTableData();
  }
}

function explorerNextPage() {
  if (explorerCurrentPage < explorerTotalPages) {
    explorerCurrentPage++;
    fetchExplorerTableData();
  }
}

// ─── Query Execution ─────────────────────────────────────────────────────
async function executeExplorerQuery() {
  const queryTextarea = document.getElementById('explorer-sql-query');
  const query = queryTextarea?.value?.trim();
  
  if (!query) {
    alert('Please enter a SQL query');
    return;
  }
  
  try {
    document.getElementById('explorer-query-results').innerHTML = 
      '<div style="text-align:center;padding:2rem;"><div class="spinner"></div><p>Executing query...</p></div>';
    
    const response = await fetch('/api/data-explorer/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    const data = await response.json();
    
    if (data.error) {
      document.getElementById('explorer-query-results').innerHTML = 
        `<div class="error-msg">Error: ${data.error}</div>`;
      return;
    }
    
    renderExplorerQueryResults(data);
    
  } catch (error) {
    console.error('Error executing query:', error);
    document.getElementById('explorer-query-results').innerHTML = 
      `<div class="error-msg">Error executing query: ${error.message}</div>`;
  }
};

function renderExplorerQueryResults(data) {
  const container = document.getElementById('explorer-query-results');
  
  if (data.data.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem;">Query returned no results</p>';
    return;
  }
  
  const tableHtml = `
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            ${data.columns.map(col => `<th>${col}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.data.map(row => `
            <tr>
              ${data.columns.map(col => `<td>${formatCellValue(row[col])}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div style="margin-top:1rem;font-size:0.85rem;color:var(--text-muted);">
      Query returned ${data.row_count} row${data.row_count !== 1 ? 's' : ''}
    </div>
  `;
  
  container.innerHTML = tableHtml;
}

function clearExplorerQuery() {
  const queryTextarea = document.getElementById('explorer-sql-query');
  if (queryTextarea) {
    queryTextarea.value = '';
    document.getElementById('explorer-query-results').innerHTML = 
      '<p style="color:var(--text-muted);text-align:center;padding:2rem;">Enter and execute a SQL query to see results</p>';
  }
}

function loadSampleQuery() {
  const sampleQueries = [
    `SELECT f.name, f.category, COUNT(*) as records 
FROM funds f 
LEFT JOIN nav_data n ON f.id = n.fund_id 
GROUP BY f.id 
ORDER BY records DESC 
LIMIT 10;`,
    
    `SELECT f.name, n.date, n.nav 
FROM funds f 
JOIN nav_data n ON f.id = n.fund_id 
WHERE f.category = 'large_cap'
ORDER BY n.date DESC 
LIMIT 20;`,
    
    `SELECT category, COUNT(*) as fund_count 
FROM funds 
GROUP BY category 
ORDER BY fund_count DESC;`,
    
    `SELECT * FROM volatility_data 
ORDER BY date DESC 
LIMIT 10;`
  ];
  
  const randomQuery = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
  const queryTextarea = document.getElementById('explorer-sql-query');
  if (queryTextarea) {
    queryTextarea.value = randomQuery;
  }
}

// ─── Schema Viewing ──────────────────────────────────────────────────────
async function loadExplorerTableSchema() {
  const schemaSelect = document.getElementById('explorer-schema-table-select');
  const tableName = schemaSelect?.value;
  
  if (!tableName) {
    document.getElementById('explorer-schema-details').innerHTML = 
      '<p style="color:var(--text-muted);text-align:center;padding:2rem;">Select a table to view its schema</p>';
    return;
  }
  
  try {
    document.getElementById('explorer-schema-details').innerHTML = 
      '<div style="text-align:center;padding:2rem;"><div class="spinner"></div><p>Loading schema...</p></div>';
    
    const response = await fetch(`/api/data-explorer/schema/${tableName}`);
    const data = await response.json();
    
    if (data.error) {
      document.getElementById('explorer-schema-details').innerHTML = 
        `<div class="error-msg">Error: ${data.error}</div>`;
      return;
    }
    
    renderExplorerTableSchema(data);
    
  } catch (error) {
    console.error('Error loading schema:', error);
    document.getElementById('explorer-schema-details').innerHTML = 
      `<div class="error-msg">Error loading schema: ${error.message}</div>`;
  }
}

function renderExplorerTableSchema(data) {
  const container = document.getElementById('explorer-schema-details');
  
  let html = `
    <div class="schema-table">
      <h4>Columns</h4>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Not Null</th>
            <th>Default</th>
            <th>Primary Key</th>
          </tr>
        </thead>
        <tbody>
          ${data.columns.map(col => `
            <tr>
              <td><strong>${col.name}</strong></td>
              <td>${col.type || 'TEXT'}</td>
              <td>${col.not_null ? '✓' : ''}</td>
              <td>${col.default || ''}</td>
              <td>${col.primary_key ? '🔑' : ''}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  
  if (data.indexes && data.indexes.length > 0) {
    html += `
      <div class="schema-table">
        <h4>Indexes</h4>
        <table>
          <thead>
            <tr><th>Name</th><th>Unique</th></tr>
          </thead>
          <tbody>
            ${data.indexes.map(idx => `
              <tr>
                <td>${idx.name}</td>
                <td>${idx.unique ? '✓' : ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
  
  if (data.create_sql) {
    html += `
      <div class="create-sql">
        <h4>CREATE Statement</h4>
        <pre>${data.create_sql}</pre>
      </div>
    `;
  }
  
  container.innerHTML = html;
}