# 🗃️ MF Database Explorer - Integrated Guide

Your comprehensive SQLite data explorer is now fully integrated into the MF Backtest web application!

## 🚀 How to Use the Integrated Data Explorer

### 1. **Start the Application**
```bash
cd /Users/abhijit/programming/mf_backtest
python3 run.py
```

### 2. **Access the Data Explorer**
- Open: http://localhost:5000
- Click on the **"🗃️ Data Explorer"** tab in the main navigation

### 3. **Explore Your Data**

#### 📊 Database Overview
- View database size (9.05 MB)  
- See total tables (7) and records (55,751+)
- Check SQLite version and other metadata

#### 📋 Tables Browser
- **Select a table** from the dropdown to browse its data
- **Pagination controls**: Navigate through large datasets (25/50/100 per page)
- **Real-time data**: See live counts and sample data

#### 🔍 SQL Query Interface  
- **Write custom queries** in the SQL editor
- **Execute with Ctrl+Enter** or click the "Execute Query" button
- **Sample queries** available via "Sample Query" button
- **SELECT-only** for data safety

#### 🏗️ Schema Viewer
- **Inspect table structure**: columns, data types, constraints
- **View indexes** and primary keys
- **See CREATE statements** for each table

## 📊 Your Comprehensive Database

**Current Status:**
- **Database Size**: 9.05 MB
- **Total Records**: 55,751
- **Tables**: 7 (funds, nav_data, index_data, volatility_data, economic_data, bse_stock_data, derivatives_data)
- **SQLite Version**: 3.39.5

**Key Data Sources:**
1. **nav_data**: 54K+ NAV records across 25 mutual funds
2. **funds**: Fund metadata with categories (flexi_cap, mid_cap, elss, etc.)
3. **index_data**: Market indices for benchmarking
4. **volatility_data**: VIX data for market volatility analysis
5. **economic_data**: Economic indicators (USD-INR rates)
6. **bse_stock_data**: BSE market data
7. **derivatives_data**: Derivatives market data

## 🔍 Sample Queries to Try

**Top Funds by Data Volume:**
```sql
SELECT f.name, f.category, COUNT(*) as records 
FROM funds f 
LEFT JOIN nav_data n ON f.id = n.fund_id 
GROUP BY f.id 
ORDER BY records DESC 
LIMIT 10;
```

**Recent NAV Performance:**
```sql
SELECT f.name, n.date, n.nav 
FROM funds f 
JOIN nav_data n ON f.id = n.fund_id 
WHERE f.category = 'large_cap'
ORDER BY n.date DESC 
LIMIT 20;
```

**Fund Distribution by Category:**
```sql
SELECT category, COUNT(*) as fund_count 
FROM funds 
GROUP BY category 
ORDER BY fund_count DESC;
```

**Market Volatility Trends:**
```sql
SELECT * FROM volatility_data 
WHERE date >= '2024-01-01'
ORDER BY date DESC;
```

**Economic Indicators:**
```sql
SELECT * FROM economic_data 
ORDER BY date DESC 
LIMIT 10;
```

## 🎯 Features & Benefits

### 🔧 **Integrated Experience**
- **Seamless navigation**: Switch between backtesting and data exploration
- **Same database**: Explore the exact same data used in your backtests
- **Unified interface**: Consistent design and user experience

### 🛡️ **Safety & Security**
- **Read-only queries**: Only SELECT statements allowed
- **Error handling**: Clear, user-friendly error messages
- **Data protection**: No accidental data modification

### ⚡ **Performance Features**
- **Pagination**: Handle large datasets efficiently
- **Real-time loading**: Live data counts and instant results
- **Keyboard shortcuts**: Ctrl+Enter to execute queries

### 🎨 **User Experience**
- **Dark theme**: Easy on the eyes for long data sessions
- **Responsive design**: Works on desktop and mobile
- **Modern interface**: Clean, intuitive navigation

## 🚀 Workflow Integration

**Perfect for MF Backtesting:**

1. **Explore Data** → Use Data Explorer to understand your dataset
2. **Analyze Trends** → Run queries to find patterns in NAV data
3. **Select Strategies** → Use insights to inform your backtesting approach
4. **Run Backtests** → Switch to other tabs to test your strategies
5. **Validate Results** → Return to Data Explorer to verify calculations

## 💡 Pro Tips

- **Use Sample Queries**: Click "Sample Query" to get started quickly
- **Keyboard Shortcuts**: Ctrl+Enter executes queries without clicking
- **Table Navigation**: Use pagination to browse large datasets efficiently
- **Schema Reference**: Check the Schema tab to understand table relationships
- **Query History**: The editor remembers your last query for convenience

Your comprehensive MF backtesting system now provides both powerful analytics AND deep data exploration in one integrated platform! 🎉