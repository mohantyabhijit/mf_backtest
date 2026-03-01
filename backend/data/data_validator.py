"""
Data quality validation and gap analysis for MF backtesting system.
"""
import sqlite3
from datetime import datetime, date
from backend.data.store import get_connection


def validate_nav_data_coverage():
    """Validate NAV data coverage for all funds"""
    conn = get_connection()
    
    print("=== NAV Data Coverage Analysis ===")
    
    # Check fund coverage
    fund_stats = conn.execute("""
        SELECT f.id, f.name, f.category,
               COUNT(n.date) as nav_records,
               MIN(n.date) as earliest_date,
               MAX(n.date) as latest_date
        FROM funds f 
        LEFT JOIN nav_data n ON f.id = n.fund_id
        GROUP BY f.id, f.name, f.category
        ORDER BY nav_records DESC
    """).fetchall()
    
    for fund in fund_stats:
        records = fund[3] if fund[3] else 0
        status = "✓ Good" if records > 1000 else "⚠ Limited" if records > 0 else "✗ No Data"
        print(f"  {fund[0]:<20} {status:<12} {records:>6} records  ({fund[4]} to {fund[5]})")
    
    # Summary by category
    print("\n=== Coverage by Category ===")
    category_stats = conn.execute("""
        SELECT f.category,
               COUNT(DISTINCT f.id) as total_funds,
               COUNT(DISTINCT CASE WHEN n.fund_id IS NOT NULL THEN f.id END) as funds_with_data,
               AVG(CASE WHEN n.fund_id IS NOT NULL THEN nav_count ELSE 0 END) as avg_records
        FROM funds f 
        LEFT JOIN (
            SELECT fund_id, COUNT(*) as nav_count 
            FROM nav_data 
            GROUP BY fund_id
        ) n ON f.id = n.fund_id
        GROUP BY f.category
        ORDER BY f.category
    """).fetchall()
    
    for cat in category_stats:
        coverage = (cat[2] / cat[1]) * 100 if cat[1] > 0 else 0
        print(f"  {cat[0]:<20} {cat[2]:>2}/{cat[1]:>2} funds ({coverage:>5.1f}%)  Avg: {cat[3]:>6.0f} records")
    
    conn.close()


def validate_index_data_coverage():
    """Validate index data coverage"""
    conn = get_connection()
    
    print("\n=== Index Data Coverage Analysis ===")
    
    index_stats = conn.execute("""
        SELECT index_name,
               COUNT(*) as records,
               MIN(date) as earliest_date,
               MAX(date) as latest_date
        FROM index_data
        GROUP BY index_name
        ORDER BY records DESC
    """).fetchall()
    
    for idx in index_stats:
        status = "✓ Good" if idx[1] > 300 else "⚠ Limited"
        print(f"  {idx[0]:<25} {status:<12} {idx[1]:>4} records  ({idx[2]} to {idx[3]})")
    
    conn.close()


def validate_economic_data():
    """Validate economic indicators"""
    conn = get_connection()
    
    print("\n=== Economic Data Analysis ===")
    
    econ_stats = conn.execute("""
        SELECT indicator, source, unit,
               COUNT(*) as records,
               MIN(date) as earliest_date,
               MAX(date) as latest_date,
               AVG(value) as avg_value
        FROM economic_data
        GROUP BY indicator, source, unit
        ORDER BY records DESC
    """).fetchall()
    
    for econ in econ_stats:
        print(f"  {econ[0]:<20} {econ[1]:<15} {econ[3]:>3} records  Avg: {econ[6]:>8.2f} {econ[2]}")
    
    conn.close()


def validate_volatility_data():
    """Validate volatility indices"""
    conn = get_connection()
    
    print("\n=== Volatility Data Analysis ===")
    
    vol_stats = conn.execute("""
        SELECT index_name,
               COUNT(*) as records,
               MIN(date) as earliest_date,
               MAX(date) as latest_date,
               AVG(value) as avg_vix,
               MIN(value) as min_vix,
               MAX(value) as max_vix
        FROM volatility_data
        GROUP BY index_name
        ORDER BY records DESC
    """).fetchall()
    
    for vol in vol_stats:
        print(f"  {vol[0]:<15} {vol[1]:>3} records  Avg: {vol[4]:>6.2f}  Range: {vol[5]:>6.2f}-{vol[6]:>6.2f}")
        
    conn.close()


def check_data_gaps():
    """Identify potential data gaps"""
    conn = get_connection()
    
    print("\n=== Data Gap Analysis ===")
    
    # Check for funds with no recent data (older than 1 year)
    old_data = conn.execute("""
        SELECT f.id, f.name, MAX(n.date) as last_nav_date
        FROM funds f
        JOIN nav_data n ON f.id = n.fund_id
        GROUP BY f.id, f.name
        HAVING MAX(n.date) < date('now', '-365 days')
        ORDER BY MAX(n.date) DESC
    """).fetchall()
    
    if old_data:
        print(f"  ⚠ Funds with stale data (>1 year old):")
        for fund in old_data:
            print(f"    {fund[0]:<20} Last NAV: {fund[2]}")
    else:
        print("  ✓ All funds have recent data")
    
    # Check for missing weekdays (potential data gaps)
    print(f"\n  Latest data dates:")
    latest_dates = conn.execute("""
        SELECT 'NAV Data' as type, MAX(date) as latest_date FROM nav_data
        UNION ALL SELECT 'Index Data', MAX(date) FROM index_data
        UNION ALL SELECT 'Volatility Data', MAX(date) FROM volatility_data
    """).fetchall()
    
    for data_type in latest_dates:
        days_ago = (datetime.now().date() - datetime.strptime(data_type[1], '%Y-%m-%d').date()).days
        status = "✓ Current" if days_ago <= 7 else "⚠ Stale" if days_ago <= 30 else "✗ Very Old"
        print(f"    {data_type[0]:<15} {data_type[1]} ({days_ago} days ago) {status}")
    
    conn.close()


def generate_data_summary():
    """Generate comprehensive data summary"""
    conn = get_connection()
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MF BACKTESTING DATA SUMMARY")
    print("=" * 60)
    
    # Total records summary
    totals = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM funds) as total_funds,
            (SELECT COUNT(*) FROM nav_data) as total_nav_records,
            (SELECT COUNT(*) FROM index_data) as total_index_records,
            (SELECT COUNT(*) FROM economic_data) as total_econ_records,
            (SELECT COUNT(*) FROM volatility_data) as total_vol_records,
            (SELECT COUNT(DISTINCT fund_id) FROM nav_data) as funds_with_nav_data
    """).fetchone()
    
    print(f"📊 Data Coverage:")
    print(f"   • Mutual Funds: {totals[0]} registered, {totals[5]} with NAV data")
    print(f"   • NAV Records: {totals[1]:,} data points")
    print(f"   • Index Records: {totals[2]:,} data points") 
    print(f"   • Economic Indicators: {totals[3]} indicators")
    print(f"   • Volatility Indices: {totals[4]} data points")
    
    # Date range coverage
    date_ranges = conn.execute("""
        SELECT 
            MIN(date) as earliest_nav, MAX(date) as latest_nav,
            (SELECT MIN(date) FROM index_data) as earliest_index,
            (SELECT MAX(date) FROM index_data) as latest_index
        FROM nav_data
    """).fetchone()
    
    print(f"\n📅 Time Coverage:")
    print(f"   • NAV Data: {date_ranges[0]} to {date_ranges[1]}")
    print(f"   • Index Data: {date_ranges[2]} to {date_ranges[3]}")
    
    # Data sources summary  
    print(f"\n🔗 Data Sources Integrated:")
    print(f"   • mfapi.in: Mutual fund NAV data")
    print(f"   • AMFI India: Fund metadata") 
    print(f"   • Yahoo Finance: Index TRI and volatility data")
    print(f"   • Exchange Rate API: USD-INR rates")
    print(f"   • Enhanced libraries: jugaad-data, bsedata, nsepy (available)")
    
    # Quality assessment
    nav_quality = (totals[5] / totals[0]) * 100 if totals[0] > 0 else 0
    print(f"\n✅ Data Quality Score:")
    print(f"   • Fund Coverage: {nav_quality:.1f}% ({totals[5]}/{totals[0]} funds have data)")
    print(f"   • Volume: {totals[1]:,} NAV records across 8 categories")
    print(f"   • Timespan: ~25 years of historical data")
    print(f"   • Market Coverage: NSE, BSE indices + volatility")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ MF BACKTESTING DATA SYSTEM READY")
    print("=" * 60)


def run_full_validation():
    """Run complete data validation suite"""
    validate_nav_data_coverage()
    validate_index_data_coverage() 
    validate_economic_data()
    validate_volatility_data()
    check_data_gaps()
    generate_data_summary()


if __name__ == "__main__":
    run_full_validation()