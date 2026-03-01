"""
SQLite Data Explorer - Web Interface
A simple Flask web app to explore your MF backtesting database
"""
from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.data.store import get_connection, DB_PATH

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'mf-data-explorer-key'

@app.route('/')
def index():
    """Main data explorer page"""
    return render_template('data_explorer.html')

@app.route('/api/tables')
def get_tables():
    """Get all tables with record counts and basic info"""
    try:
        conn = get_connection()
        
        # Get table names
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        table_info = []
        for table in tables:
            table_name = table[0]
            
            # Get record count
            count = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
            
            # Get column info
            columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
            column_names = [col[1] for col in columns]
            
            # Get sample data
            sample_data = conn.execute(f"SELECT * FROM `{table_name}` LIMIT 3").fetchall()
            
            table_info.append({
                'name': table_name,
                'count': count,
                'columns': column_names,
                'sample_data': [dict(zip(column_names, row)) for row in sample_data]
            })
        
        conn.close()
        return jsonify({'tables': table_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>')
def get_table_data(table_name):
    """Get data from specific table with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        conn = get_connection()
        
        # Get total count
        total = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
        
        # Get data with pagination
        data = conn.execute(f"""
            SELECT * FROM `{table_name}` 
            LIMIT {per_page} OFFSET {offset}
        """).fetchall()
        
        # Get column names
        columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
        column_names = [col[1] for col in columns]
        
        # Convert to list of dictionaries
        rows = [dict(zip(column_names, row)) for row in data]
        
        conn.close()
        
        return jsonify({
            'data': rows,
            'columns': column_names,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema/<table_name>')
def get_table_schema(table_name):
    """Get detailed schema for a table"""
    try:
        conn = get_connection()
        
        # Get column info with types
        columns = conn.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
        
        # Get indexes
        indexes = conn.execute(f"PRAGMA index_list(`{table_name}`)").fetchall()
        
        # Get foreign keys
        foreign_keys = conn.execute(f"PRAGMA foreign_key_list(`{table_name}`)").fetchall()
        
        # Get CREATE statement
        create_sql = conn.execute(f"""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='{table_name}'
        """).fetchone()
        
        conn.close()
        
        return jsonify({
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
            'foreign_keys': [
                {
                    'column': fk[3],
                    'references_table': fk[2],
                    'references_column': fk[4]
                }
                for fk in foreign_keys
            ],
            'create_sql': create_sql[0] if create_sql else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute SQL query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Basic security - only allow SELECT statements
        if not query.upper().startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        conn = get_connection()
        
        try:
            cursor = conn.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert to list of dictionaries
            rows = [dict(zip(column_names, row)) for row in results]
            
            conn.close()
            
            return jsonify({
                'data': rows,
                'columns': column_names,
                'row_count': len(rows)
            })
            
        except sqlite3.Error as e:
            conn.close()
            return jsonify({'error': f'SQL Error: {str(e)}'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database-info')
def get_database_info():
    """Get general database information"""
    try:
        conn = get_connection()
        
        # Database size
        db_size = os.path.getsize(DB_PATH)
        
        # Total records across all tables
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        total_records = 0
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM `{table[0]}`").fetchone()[0]
            total_records += count
        
        # SQLite version
        sqlite_version = conn.execute("SELECT sqlite_version()").fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'database_path': str(DB_PATH),
            'database_size': db_size,
            'database_size_mb': round(db_size / (1024 * 1024), 2),
            'total_tables': len(tables),
            'total_records': total_records,
            'sqlite_version': sqlite_version
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 Starting MF Data Explorer...")
    print("📍 Database:", DB_PATH)
    print("🌐 URL: http://localhost:5001")
    
    app.run(debug=True, port=5001)