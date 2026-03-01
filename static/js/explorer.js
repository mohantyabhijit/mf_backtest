// MF Database Explorer JavaScript

// Global state
let currentTable = '';
let currentPage = 1;
let totalPages = 1;
let allTables = [];

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadDatabaseInfo();
    loadTables();
});

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    showLoading();
    try {
        const response = await fetch(endpoint, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        showError(error.message);
        throw error;
    } finally {
        hideLoading();
    }
}

// Loading and Error Handling
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-modal').classList.remove('hidden');
}

function closeError() {
    document.getElementById('error-modal').classList.add('hidden');
}

// Tab Navigation
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Hide all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Highlight selected tab button
    event.target.classList.add('active');
}

// Database Info Loading
async function loadDatabaseInfo() {
    try {
        const data = await apiCall('/api/database-info');
        
        document.getElementById('db-path').textContent = `📁 ${data.database_path}`;
        document.getElementById('db-size').textContent = `💾 ${data.database_size_mb} MB`;
        document.getElementById('total-records').textContent = `📊 ${data.total_records.toLocaleString()} records`;
        
        // Update summary stats
        document.getElementById('summary-stats').innerHTML = `
            <div class="stat-item"><strong>Database Size:</strong> ${data.database_size_mb} MB</div>
            <div class="stat-item"><strong>Total Tables:</strong> ${data.total_tables}</div>
            <div class="stat-item"><strong>Total Records:</strong> ${data.total_records.toLocaleString()}</div>
            <div class="stat-item"><strong>SQLite Version:</strong> ${data.sqlite_version}</div>
        `;
        
    } catch (error) {
        console.error('Failed to load database info:', error);
    }
}

// Tables Loading
async function loadTables() {
    try {
        const data = await apiCall('/api/tables');
        allTables = data.tables;
        
        // Populate table selectors
        const tableSelect = document.getElementById('table-select');
        const schemaSelect = document.getElementById('schema-table-select');
        
        tableSelect.innerHTML = '<option value="">Select a table...</option>';
        schemaSelect.innerHTML = '<option value="">Select a table...</option>';
        
        // Update table summary
        let summaryHtml = '<div class="table-list">';
        
        data.tables.forEach(table => {
            const option = `<option value="${table.name}">${table.name} (${table.count.toLocaleString()} records)</option>`;
            tableSelect.innerHTML += option;
            schemaSelect.innerHTML += option;
            
            summaryHtml += `
                <div class="table-summary-item" onclick="selectTable('${table.name}')">
                    <strong>${table.name}</strong>
                    <span>${table.count.toLocaleString()} records</span>
                    <small>${table.columns.length} columns</small>
                </div>
            `;
        });
        
        summaryHtml += '</div>';
        document.getElementById('table-summary').innerHTML = summaryHtml;
        
    } catch (error) {
        console.error('Failed to load tables:', error);
    }
}

function selectTable(tableName) {
    document.getElementById('table-select').value = tableName;
    showTab('tables');
    loadTableData();
}

// Table Data Loading
async function loadTableData() {
    const tableName = document.getElementById('table-select').value;
    if (!tableName) {
        document.getElementById('table-data-container').innerHTML = '<p>Select a table to view its data</p>';
        return;
    }
    
    currentTable = tableName;
    currentPage = 1;
    
    const perPage = document.getElementById('per-page').value;
    
    try {
        const data = await apiCall(`/api/table/${tableName}?page=${currentPage}&per_page=${perPage}`);
        
        totalPages = data.total_pages;
        displayTableData(data);
        updatePaginationControls();
        
    } catch (error) {
        console.error('Failed to load table data:', error);
    }
}

function displayTableData(data) {
    if (data.data.length === 0) {
        document.getElementById('table-data-container').innerHTML = '<p>No data found in this table</p>';
        return;
    }
    
    let html = '<table class="data-table"><thead><tr>';
    
    // Create headers
    data.columns.forEach(column => {
        html += `<th>${column}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Create rows
    data.data.forEach(row => {
        html += '<tr>';
        data.columns.forEach(column => {
            const value = row[column];
            let displayValue = value;
            let cellClass = '';
            
            // Format different data types
            if (typeof value === 'number') {
                cellClass = 'number';
                if (value % 1 !== 0) {
                    displayValue = value.toFixed(4);
                }
            } else if (value && value.match && value.match(/^\d{4}-\d{2}-\d{2}/)) {
                cellClass = 'date';
            }
            
            html += `<td class="${cellClass}">${displayValue ?? 'NULL'}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    // Add summary info
    html = `
        <div class="table-info mb-2">
            <strong>${currentTable}</strong> - 
            Showing ${data.data.length} of ${data.total.toLocaleString()} records 
            (Page ${data.page} of ${data.total_pages})
        </div>
    ` + html;
    
    document.getElementById('table-data-container').innerHTML = html;
}

// Pagination Controls
function updatePaginationControls() {
    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadTableData();
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadTableData();
    }
}

// SQL Query Functions
function loadQuery(query) {
    document.getElementById('sql-query').value = query;
    showTab('query');
}

function loadSampleQuery(type) {
    const queries = {
        'funds': `SELECT f.id, f.name, f.category, COUNT(n.date) as nav_records
FROM funds f
LEFT JOIN nav_data n ON f.id = n.fund_id
GROUP BY f.id, f.name, f.category
ORDER BY nav_records DESC
LIMIT 10;`,
        'nav': `SELECT fund_id, 
       COUNT(*) as total_records,
       MIN(date) as start_date,
       MAX(date) as end_date,
       ROUND(MIN(nav), 2) as min_nav,
       ROUND(MAX(nav), 2) as max_nav,
       ROUND((MAX(nav) / MIN(nav) - 1) * 100, 2) as total_return_pct
FROM nav_data 
GROUP BY fund_id 
ORDER BY total_return_pct DESC
LIMIT 10;`
    };
    
    if (queries[type]) {
        loadQuery(queries[type]);
    }
}

async function executeQuery() {
    const query = document.getElementById('sql-query').value.trim();
    if (!query) {
        showError('Please enter a SQL query');
        return;
    }
    
    document.getElementById('query-status').textContent = 'Executing query...';
    
    try {
        const data = await apiCall('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        displayQueryResults(data);
        document.getElementById('query-status').textContent = `✅ Query executed successfully (${data.row_count} rows)`;
        
    } catch (error) {
        document.getElementById('query-status').textContent = '❌ Query failed';
        console.error('Query failed:', error);
    }
}

function displayQueryResults(data) {
    if (data.data.length === 0) {
        document.getElementById('query-results').innerHTML = '<p>Query returned no results</p>';
        return;
    }
    
    let html = '<table class="data-table"><thead><tr>';
    
    // Create headers
    data.columns.forEach(column => {
        html += `<th>${column}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Create rows
    data.data.forEach(row => {
        html += '<tr>';
        data.columns.forEach(column => {
            const value = row[column];
            let displayValue = value;
            let cellClass = '';
            
            // Format different data types
            if (typeof value === 'number') {
                cellClass = 'number';
                if (value % 1 !== 0) {
                    displayValue = value.toFixed(4);
                }
            } else if (value && value.match && value.match(/^\d{4}-\d{2}-\d{2}/)) {
                cellClass = 'date';
            }
            
            html += `<td class="${cellClass}">${displayValue ?? 'NULL'}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    // Add summary info
    html = `<div class="query-info mb-2"><strong>Results:</strong> ${data.row_count} rows returned</div>` + html;
    
    document.getElementById('query-results').innerHTML = html;
}

function clearQuery() {
    document.getElementById('sql-query').value = '';
    document.getElementById('query-results').innerHTML = '<p>Enter and execute a SQL query to see results</p>';
    document.getElementById('query-status').textContent = '';
}

// Schema Functions
async function loadTableSchema() {
    const tableName = document.getElementById('schema-table-select').value;
    if (!tableName) {
        document.getElementById('schema-details').innerHTML = '<p>Select a table to view its schema</p>';
        return;
    }
    
    try {
        const data = await apiCall(`/api/schema/${tableName}`);
        displaySchema(tableName, data);
        
    } catch (error) {
        console.error('Failed to load schema:', error);
    }
}

function displaySchema(tableName, data) {
    let html = `<h3>Table: ${tableName}</h3>`;
    
    // Columns section
    html += '<div class="schema-section"><h4>Columns</h4>';
    html += '<table class="data-table schema-table"><thead><tr>';
    html += '<th>Column</th><th>Type</th><th>Not Null</th><th>Default</th><th>Primary Key</th>';
    html += '</tr></thead><tbody>';
    
    data.columns.forEach(column => {
        html += `<tr>
            <td><strong>${column.name}</strong></td>
            <td>${column.type || 'TEXT'}</td>
            <td>${column.not_null ? '✓' : ''}</td>
            <td>${column.default || ''}</td>
            <td>${column.primary_key ? '🔑' : ''}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    
    // Indexes section
    if (data.indexes.length > 0) {
        html += '<div class="schema-section"><h4>Indexes</h4>';
        html += '<ul>';
        data.indexes.forEach(index => {
            html += `<li><strong>${index.name}</strong> ${index.unique ? '(Unique)' : ''}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Foreign keys section
    if (data.foreign_keys.length > 0) {
        html += '<div class="schema-section"><h4>Foreign Keys</h4>';
        html += '<ul>';
        data.foreign_keys.forEach(fk => {
            html += `<li><strong>${fk.column}</strong> → ${fk.references_table}.${fk.references_column}</li>`;
        });
        html += '</ul></div>';
    }
    
    // CREATE SQL section
    if (data.create_sql) {
        html += '<div class="schema-section"><h4>CREATE Statement</h4>';
        html += `<div class="create-sql">${data.create_sql}</div></div>`;
    }
    
    document.getElementById('schema-details').innerHTML = html;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to execute query
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (document.getElementById('query-tab').classList.contains('active')) {
            executeQuery();
        }
    }
});