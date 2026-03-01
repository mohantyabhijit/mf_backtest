#!/bin/bash
# Quick database explorer script

DB_PATH="/Users/abhijit/programming/mf_backtest/data/mf_backtest.db"

echo "🗃️  MF BACKTESTING DATABASE EXPLORER"
echo "================================="
echo "Database: $DB_PATH"
echo "Size: $(du -h $DB_PATH | cut -f1)"
echo ""

# Useful queries
echo "📊 QUICK DATA OVERVIEW:"
sqlite3 -header -column "$DB_PATH" "
SELECT 
    (SELECT COUNT(*) FROM funds) as total_funds,
    (SELECT COUNT(*) FROM nav_data) as nav_records,
    (SELECT COUNT(*) FROM index_data) as index_records,
    (SELECT COUNT(*) FROM volatility_data) as volatility_records,
    (SELECT COUNT(*) FROM economic_data) as economic_records;
"

echo ""
echo "📈 TOP FUNDS BY DATA VOLUME:"
sqlite3 -header -column "$DB_PATH" "
SELECT f.id, f.name, f.category, COUNT(n.date) as records
FROM funds f 
LEFT JOIN nav_data n ON f.id = n.fund_id
GROUP BY f.id, f.name, f.category
ORDER BY records DESC
LIMIT 5;
"

echo ""
echo "📅 LATEST DATA DATES:"
sqlite3 -header -column "$DB_PATH" "
SELECT 'NAV Data' as data_type, MAX(date) as latest_date FROM nav_data
UNION ALL SELECT 'Index Data', MAX(date) FROM index_data
UNION ALL SELECT 'Volatility Data', MAX(date) FROM volatility_data
UNION ALL SELECT 'Economic Data', MAX(date) FROM economic_data;
"

echo ""
echo "💡 TO EXPLORE INTERACTIVELY:"
echo "sqlite3 $DB_PATH"
echo ""
echo "💡 USEFUL COMMANDS:"
echo ".tables           - Show all tables"
echo ".schema funds     - Show table structure"  
echo ".headers on       - Show column names"
echo ".mode column      - Pretty formatting"
echo ""