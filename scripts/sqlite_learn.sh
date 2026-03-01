#!/bin/bash
# Interactive SQLite learning session for MF database

DB_PATH="/Users/abhijit/programming/mf_backtest/data/mf_backtest.db"

echo "🎓 SQLite Learning Session - MF Database"
echo "========================================"
echo ""

# Test basic connection
echo "📊 TESTING DATABASE CONNECTION:"
if [ -f "$DB_PATH" ]; then
    echo "✅ Database found: $DB_PATH"
    echo "📏 Size: $(du -h $DB_PATH | cut -f1)"
else
    echo "❌ Database not found!"
    exit 1
fi

echo ""
echo "🔍 BASIC EXPLORATION:"

# Show tables and record counts
sqlite3 -header -column "$DB_PATH" "
SELECT 'Table Name' as category, 'Record Count' as value
UNION ALL
SELECT 'funds', CAST(COUNT(*) as TEXT) FROM funds
UNION ALL  
SELECT 'nav_data', CAST(COUNT(*) as TEXT) FROM nav_data
UNION ALL
SELECT 'index_data', CAST(COUNT(*) as TEXT) FROM index_data
UNION ALL
SELECT 'volatility_data', CAST(COUNT(*) as TEXT) FROM volatility_data
UNION ALL
SELECT 'economic_data', CAST(COUNT(*) as TEXT) FROM economic_data;
"

echo ""
echo "📈 SAMPLE MF DATA:"

# Show sample fund data
sqlite3 -header -column "$DB_PATH" "
SELECT id, name, category 
FROM funds 
ORDER BY category
LIMIT 8;
"

echo ""
echo "💰 RECENT NAV DATA:"

# Show recent NAV data
sqlite3 -header -column "$DB_PATH" "
SELECT fund_id, date, nav
FROM nav_data 
WHERE fund_id IN ('franklin_flexi', 'hdfc_multi_asset')
ORDER BY date DESC 
LIMIT 6;
"

echo ""
echo "📊 FUND CATEGORIES:"

# Group by category
sqlite3 -header -column "$DB_PATH" "
SELECT category, COUNT(*) as fund_count
FROM funds
GROUP BY category
ORDER BY fund_count DESC;
"

echo ""
echo "🎯 INTERACTIVE PRACTICE:"
echo "Try these commands:"
echo ""
echo "1. Connect to database:"
echo "   sqlite3 $DB_PATH"
echo ""
echo "2. Essential dot commands:"
echo "   .headers on    # Show column names"
echo "   .mode column   # Format output nicely" 
echo "   .tables        # Show all tables"
echo "   .schema funds  # Show table structure"
echo ""
echo "3. Sample queries to try:"
echo "   SELECT COUNT(*) FROM nav_data;"
echo "   SELECT * FROM funds WHERE category = 'large_cap';"
echo "   SELECT fund_id, MAX(nav) FROM nav_data GROUP BY fund_id;"
echo ""
echo "4. Exit SQLite:"
echo "   .exit"
echo ""

# Optional: Launch SQLite if requested
echo "🚀 LAUNCH INTERACTIVE SESSION? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Launching SQLite CLI..."
    echo "Use .exit to return to shell"
    sqlite3 "$DB_PATH" ".headers on" ".mode column" ".tables"
fi