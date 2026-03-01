#!/usr/bin/env python3
"""
Simple SQLite Data Explorer - Standalone Version
A basic web interface to explore your MF database using only standard library
"""
import http.server
import socketserver
import json
import sqlite3
import urllib.parse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))
from backend.data.store import get_connection, DB_PATH

PORT = 8001

class MFDataHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        elif self.path == '/explorer.css':
            self.serve_css()
        elif self.path == '/explorer.js':
            self.serve_js()
        elif self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)
    
    def serve_html(self):
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MF Database Explorer</title>
    <link rel="stylesheet" href="/explorer.css">
</head>
<body>
    <header>
        <h1>🗃️ MF Database Explorer</h1>
        <div id="db-info" class="db-info">
            <span id="db-path"></span>
            <span id="db-size"></span>
            <span id="total-records"></span>
        </div>
    </header>

    <nav class="tab-nav">
        <button class="tab-btn active" onclick="showTab('overview')">📊 Overview</button>
        <button class="tab-btn" onclick="showTab('tables')">📋 Tables</button>
        <button class="tab-btn" onclick="showTab('query')">🔍 SQL Query</button>
        <button class="tab-btn" onclick="showTab('schema')">🏗️ Schema</button>
    </nav>

    <main>
        <div id="overview-tab" class="tab-content active">
            <div class="overview-grid">
                <div class="overview-card">
                    <h3>📈 Database Summary</h3>
                    <div id="summary-stats">Loading...</div>
                </div>
                <div class="overview-card">
                    <h3>📊 Table Overview</h3>
                    <div id="table-summary">Loading...</div>
                </div>
                <div class="overview-card">
                    <h3>🚀 Quick Actions</h3>
                    <div class="quick-actions">
                        <button onclick="showTab('tables')">Browse Tables</button>
                        <button onclick="showTab('query')">Run Query</button>
                        <button onclick="loadSampleQuery()">Sample Query</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="tables-tab" class="tab-content">
            <div class="table-controls">
                <select id="table-select" onchange="loadTableData()">
                    <option value="">Select a table...</option>
                </select>
                <div class="pagination-controls">
                    <button id="prev-page" onclick="prevPage()">Previous</button>
                    <span id="page-info">Page 1</span>
                    <button id="next-page" onclick="nextPage()">Next</button>
                    <select id="per-page" onchange="loadTableData()">
                        <option value="25">25 per page</option>
                        <option value="50" selected>50 per page</option>
                        <option value="100">100 per page</option>
                    </select>
                </div>
            </div>
            <div id="table-data-container">
                <p>Select a table to view its data</p>
            </div>
        </div>

        <div id="query-tab" class="tab-content">
            <div class="query-container">
                <div class="query-editor">
                    <textarea id="sql-query" placeholder="Enter your SQL query here..."></textarea>
                    <div class="query-controls">
                        <button onclick="executeQuery()">▶️ Execute Query</button>
                        <button onclick="clearQuery()">🗑️ Clear</button>
                        <span id="query-status"></span>
                    </div>
                </div>
                <div id="query-results" class="query-results">
                    <p>Enter and execute a SQL query to see results</p>
                </div>
            </div>
        </div>

        <div id="schema-tab" class="tab-content">
            <div class="schema-controls">
                <select id="schema-table-select" onchange="loadTableSchema()">
                    <option value="">Select a table...</option>
                </select>
            </div>
            <div id="schema-details">
                <p>Select a table to view its schema</p>
            </div>
        </div>
    </main>

    <div id="loading" class="loading hidden">
        <div class="spinner"></div>
        <p>Loading...</p>
    </div>

    <script src="/explorer.js"></script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_css(self):
        css_file = Path('static/css/explorer.css')
        if css_file.exists():
            with open(css_file, 'r') as f:
                css_content = f.read()
        else:
            css_content = "body { font-family: Arial, sans-serif; }"
        
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css_content.encode())
    
    def serve_js(self):
        js_file = Path('static/js/explorer.js')  
        if js_file.exists():
            with open(js_file, 'r') as f:
                js_content = f.read()
        else:
            js_content = "console.log('JavaScript not found');"
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.wfile.write(js_content.encode())
    
    def handle_api_get(self):
        path_parts = self.path.split('/')
        
        try:
            if self.path == '/api/database-info':
                self.api_database_info()
            elif self.path == '/api/tables':
                self.api_tables()
            elif path_parts[2] == 'table' and len(path_parts) == 4:
                table_name = path_parts[3].split('?')[0]
                query_params = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
                page = int(query_params.get('page', [1])[0])
                per_page = int(query_params.get('per_page', [50])[0])
                self.api_table_data(table_name, page, per_page)
            elif path_parts[2] == 'schema' and len(path_parts) == 4:
                table_name = path_parts[3]
                self.api_table_schema(table_name)
            else:
                self.send_error(404)
        except Exception as e:
            self.send_json_error(str(e))
    
    def handle_api_post(self):
        try:
            if self.path == '/api/query':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                self.api_execute_query(data.get('query', ''))
            else:
                self.send_error(404)
        except Exception as e:
            self.send_json_error(str(e))
    
    def api_database_info(self):
        try:
            db_size = os.path.getsize(DB_PATH)
            conn = get_connection()
            
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            total_records = 0
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM `{table[0]}`").fetchone()[0]
                total_records += count
            
            sqlite_version = conn.execute("SELECT sqlite_version()").fetchone()[0]
            conn.close()
            
            self.send_json({
                'database_path': str(DB_PATH),
                'database_size': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'total_tables': len(tables),
                'total_records': total_records,
                'sqlite_version': sqlite_version
            })
        except Exception as e:
            self.send_json_error(str(e))
    
    def api_tables(self):
        try:
            conn = get_connection()
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
            
            table_info = []
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
                columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
                column_names = [col[1] for col in columns]
                sample_data = conn.execute(f"SELECT * FROM `{table_name}` LIMIT 3").fetchall()
                
                table_info.append({
                    'name': table_name,
                    'count': count,
                    'columns': column_names,
                    'sample_data': [dict(zip(column_names, row)) for row in sample_data]
                })
            
            conn.close()
            self.send_json({'tables': table_info})
        except Exception as e:
            self.send_json_error(str(e))
    
    def api_table_data(self, table_name, page, per_page):
        try:
            offset = (page - 1) * per_page
            conn = get_connection()
            
            total = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
            data = conn.execute(f"SELECT * FROM `{table_name}` LIMIT {per_page} OFFSET {offset}").fetchall()
            columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
            column_names = [col[1] for col in columns]
            
            rows = [dict(zip(column_names, row)) for row in data]
            
            conn.close()
            
            self.send_json({
                'data': rows,
                'columns': column_names,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
        except Exception as e:
            self.send_json_error(str(e))
    
    def api_table_schema(self, table_name):
        try:
            conn = get_connection()
            columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
            indexes = conn.execute(f"PRAGMA index_list(`{table_name}`)").fetchall()
            create_sql = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
            
            conn.close()
            
            self.send_json({
                'columns': [
                    {
                        'name': col[1],
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'default': col[4],
                        'primary_key': bool(col[5])
                    }
                    for col in columns
                ],
                'indexes': [{'name': idx[1], 'unique': bool(idx[2])} for idx in indexes],
                'create_sql': create_sql[0] if create_sql else None
            })
        except Exception as e:
            self.send_json_error(str(e))
    
    def api_execute_query(self, query):
        query = query.strip()
        if not query:
            self.send_json_error('No query provided')
            return
        
        if not query.upper().startswith('SELECT'):
            self.send_json_error('Only SELECT queries are allowed')
            return
        
        try:
            conn = get_connection()
            cursor = conn.execute(query)
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            rows = [dict(zip(column_names, row)) for row in results]
            
            conn.close()
            
            self.send_json({
                'data': rows,
                'columns': column_names,
                'row_count': len(rows)
            })
        except sqlite3.Error as e:
            self.send_json_error(f'SQL Error: {str(e)}')
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_json_error(self, message):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())

def start_server():
    print("🚀 Starting MF Data Explorer (Standalone)...")
    print(f"📍 Database: {DB_PATH}")
    print(f"🌐 URL: http://localhost:{PORT}")
    print("   Press Ctrl+C to stop the server")
    print("")
    
    try:
        with socketserver.TCPServer(("", PORT), MFDataHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped")

if __name__ == "__main__":
    start_server()