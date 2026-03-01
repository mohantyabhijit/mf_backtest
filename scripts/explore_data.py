#!/usr/bin/env python3
"""
Python script to explore MF backtesting database data.
Usage: python3 explore_data.py
"""
import sqlite3
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.data.store import get_connection

def explore_funds():
    """Show fund summary"""
    conn = get_connection()
    
    print("🏛️  MUTUAL FUNDS OVERVIEW")
    print("=" * 50)
    
    # Fund distribution by category
    df = pd.read_sql_query("""
        SELECT category, COUNT(*) as fund_count,
               COUNT(CASE WHEN nav_count > 0 THEN 1 END) as with_data
        FROM (
            SELECT f.category, f.id,
                   (SELECT COUNT(*) FROM nav_data WHERE fund_id = f.id) as nav_count
            FROM funds f
        ) 
        GROUP BY category
        ORDER BY fund_count DESC
    """, conn)
    
    print(df.to_string(index=False))
    
    # Top funds by data volume
    print(f"\n📈 TOP 10 FUNDS BY DATA VOLUME:")
    df_top = pd.read_sql_query("""
        SELECT f.id, f.name, f.category, COUNT(n.date) as records,
               MIN(n.date) as start_date, MAX(n.date) as end_date
        FROM funds f 
        JOIN nav_data n ON f.id = n.fund_id
        GROUP BY f.id, f.name, f.category
        ORDER BY records DESC
        LIMIT 10
    """, conn)
    
    print(df_top.to_string(index=False))
    conn.close()

def explore_nav_trends():
    """Show NAV trends for popular funds"""
    conn = get_connection()
    
    print(f"\n📊 RECENT NAV TRENDS (Last 10 Days)")
    print("=" * 50)
    
    # Get recent NAV data for top funds
    df = pd.read_sql_query("""
        SELECT n.fund_id, n.date, n.nav, f.category
        FROM nav_data n
        JOIN funds f ON n.fund_id = f.id
        WHERE n.date >= date('now', '-10 days')
          AND n.fund_id IN ('franklin_flexi', 'hdfc_multi_asset', 'axis_elss')
        ORDER BY n.fund_id, n.date DESC
    """, conn)
    
    if not df.empty:
        for fund_id in df['fund_id'].unique():
            fund_data = df[df['fund_id'] == fund_id].head(5)
            print(f"\n{fund_id.upper()}:")
            print(fund_data[['date', 'nav']].to_string(index=False))
    
    conn.close()

def explore_market_data():
    """Show market indices and volatility"""
    conn = get_connection()
    
    print(f"\n🏛️  MARKET DATA OVERVIEW")
    print("=" * 50)
    
    # Index data summary
    df_idx = pd.read_sql_query("""
        SELECT index_name, COUNT(*) as records,
               MIN(date) as start_date, MAX(date) as end_date,
               ROUND(AVG(value), 2) as avg_value
        FROM index_data
        GROUP BY index_name
        ORDER BY records DESC
    """, conn)
    
    print("INDEX DATA:")
    print(df_idx.to_string(index=False))
    
    # Recent volatility
    df_vix = pd.read_sql_query("""
        SELECT index_name, date, ROUND(value, 2) as vix_value
        FROM volatility_data
        ORDER BY index_name, date DESC
        LIMIT 10
    """, conn)
    
    if not df_vix.empty:
        print(f"\nRECENT VOLATILITY:")
        print(df_vix.to_string(index=False))
    
    # Economic indicators
    df_econ = pd.read_sql_query("""
        SELECT indicator, date, value, unit, source
        FROM economic_data
        ORDER BY date DESC
    """, conn)
    
    if not df_econ.empty:
        print(f"\nECONOMIC INDICATORS:")
        print(df_econ.to_string(index=False))
    
    conn.close()

def main():
    print("🗃️  MF BACKTESTING DATABASE EXPLORER (Python)")
    print("=" * 60)
    
    try:
        explore_funds()
        explore_nav_trends() 
        explore_market_data()
        
        print(f"\n💡 NEXT STEPS:")
        print("- Run backtesting with: python3 run.py")
        print("- Access web UI at: http://localhost:5000") 
        print("- Explore more data with pandas DataFrames")
        
    except Exception as e:
        print(f"❌ Error exploring database: {e}")
        print("Make sure the database exists and is accessible.")

if __name__ == "__main__":
    main()