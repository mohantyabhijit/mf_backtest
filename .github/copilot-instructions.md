# Copilot Instructions for MF Backtest

## Quick Start

**Development Server:**
```bash
python3 run.py
```
Server starts at http://localhost:5000

**First-time Setup:**
```bash
pip install -r requirements.txt
python3 scripts/seed_data.py  # Downloads ~25 years of historical NAV data
```

**Force Data Refresh:**
```bash
python3 scripts/seed_data.py --force
```

## Architecture Overview

This is a **Flask backend + vanilla HTML/CSS/JS frontend** application for backtesting Indian mutual fund SIP strategies.

### Backend Structure (`backend/`)
- **`app.py`** - Main Flask application and static file serving
- **`api/routes.py`** - REST API endpoints (`/api/strategies`, `/api/run`, `/api/run-all`, etc.)
- **`data/`** - Data layer
  - `store.py` - SQLite database operations (funds, nav_data, index_data tables)
  - `fund_registry.py` - Fund catalog with AMFI codes and category mappings
  - `fetcher.py` - mfapi.in NAV data fetching
  - `index_fetcher.py` - NSE/yfinance index TRI data fetching
  - `amfi_fetcher.py` - AMFI metadata fetching
- **`backtest/`** - Core simulation engine
  - `engine.py` - SIP simulation with monthly investments, step-ups, proxy filling
  - `strategies.py` - 8 predefined allocation strategies (S1-S8)
  - `metrics.py` - CAGR, XIRR, Sharpe ratio, max drawdown calculations

### Frontend Structure (`frontend/`)
- **`index.html`** - Single-page app with 4 tabs
- **`js/app.js`** - Main controller, tab navigation, data loading
- **`js/api.js`** - REST API client functions
- **`js/charts.js`** - Chart.js visualization wrappers
- **`js/utils.js`** - Formatting helpers and UI utilities
- **`css/style.css`** - Responsive styling

### Data Flow
1. **Seeding**: `scripts/seed_data.py` populates SQLite DB from mfapi.in + yfinance
2. **Simulation**: Frontend calls `/api/run` → `engine.py` loads NAV data → calculates SIP returns → `metrics.py` computes ratios
3. **Visualization**: Results rendered via Chart.js (growth charts, allocation pies, comparison tables)

## Key Conventions

### Fund Registry System
- **Fund IDs**: kebab-case identifiers (e.g., `franklin_bluechip`, `nippon_mid_cap`)
- **Categories**: `large_cap`, `mid_cap`, `small_cap`, `flexi_cap`, `multi_asset`, `elss`, `balanced_advantage`, `index`
- **Primary Fund Mapping**: `CATEGORY_PRIMARY_FUND` dict maps categories to representative funds for strategies
- **Proxy System**: Funds without historical data use index proxies (e.g., pre-2004 small cap uses Nifty Smallcap 250 TRI)

### Strategy Definition Pattern
Strategies in `strategies.py` use allocation dictionaries:
```python
"allocations": {
    _primary("large_cap"):  0.50,  # Uses CATEGORY_PRIMARY_FUND lookup
    _primary("mid_cap"):    0.30,
    _primary("small_cap"):  0.20,
}
```

### Date Handling
- **Storage Format**: `YYYY-MM-DD` strings in SQLite
- **Processing**: pandas datetime conversion in engine.py
- **API**: ISO date strings in JSON requests/responses

### SIP Simulation Rules
- **Monthly Investment**: 1st of each month (or next available NAV date)
- **Step-up Timing**: Every April (anniversary month)
- **NAV Lookup**: Linear search with fallback to nearest available date
- **Portfolio Calculation**: Units accumulated × final NAV values

### Data Source Priority
1. **Primary**: mfapi.in NAV data (free API)
2. **Fallback**: Index proxy data scaled to fund's first available NAV
3. **Index Data**: yfinance for TRI (Total Return Index) values

## Database Schema

```sql
-- Fund registry
CREATE TABLE funds (
    id TEXT PRIMARY KEY,          -- Fund identifier
    name TEXT,                    -- Display name
    amfi_code TEXT,               -- mfapi.in scheme code
    category TEXT,                -- large_cap, mid_cap, etc.
    source_type TEXT,             -- "mfapi" or "index"
    launch_date TEXT,             -- YYYY-MM-DD format
    proxy_fund TEXT               -- Fallback fund for pre-launch data
);

-- Historical NAV data
CREATE TABLE nav_data (
    fund_id TEXT,
    date TEXT,                    -- YYYY-MM-DD format
    nav REAL,
    PRIMARY KEY (fund_id, date)
);

-- Index TRI data  
CREATE TABLE index_data (
    index_name TEXT,              -- nifty_50_tri, nifty_midcap_150_tri, etc.
    date TEXT,
    value REAL,
    PRIMARY KEY (index_name, date)
);
```

## API Endpoints

**Core Endpoints:**
- `GET /api/strategies` - List all 8 strategies with allocations
- `POST /api/run` - Single strategy backtest
- `POST /api/run-all` - All strategies comparison
- `GET /api/funds` - Available funds with data date ranges

**Request Format (`/api/run`):**
```json
{
  "strategy_id": "S1",
  "start_date": "2000-01-01", 
  "end_date": "2024-12-31",
  "monthly_sip": 75000,
  "stepup_pct": 10
}
```

## Performance Notes

- **Data Loading**: Engine caches NAV series per fund to avoid repeated DB queries
- **Memory Usage**: Large datasets (25 years × multiple funds) held in pandas DataFrames
- **API Response Size**: `/api/run-all` returns 8 complete backtest results (~100KB JSON)

## Extending the System

**Adding New Funds:**
1. Add entry to `FUNDS` list in `fund_registry.py` with valid `amfi_code`
2. Re-run `scripts/seed_data.py --force` to fetch historical data
3. Update `CATEGORY_PRIMARY_FUND` if making it the primary fund for its category

**Adding New Strategies:**
1. Define allocation dict in `strategies.py` (must sum to 1.0)
2. Assign unique ID (S9, S10, etc.) and descriptive name
3. Frontend automatically picks up new strategies via `/api/strategies`

**Adding New Metrics:**
1. Implement calculation function in `metrics.py`
2. Add to `compute_all_metrics()` return dict
3. Frontend can access via API response and display in results tables