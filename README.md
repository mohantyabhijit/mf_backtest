# MF Backtest — Indian Mutual Fund Strategy Backtester

A Python + plain HTML/CSS/JS tool to backtest Indian mutual fund SIP strategies over 25 years of historical data.

## Features
- **8 Strategies**: 50-30-20, Equal Weight, Conservative, Aggressive, Flexi+Multi Asset, Index Only, ELSS, Balanced Advantage
- **SIP Simulation**: ₹75,000/month with 10% annual step-up every April
- **Metrics**: CAGR, XIRR, Absolute Return, Max Drawdown, Volatility, Sharpe Ratio
- **Data**: mfapi.in (free), AMFI bulk NAV, NSE index TRI proxies
- **Frontend**: Chart.js charts, 4 interactive tabs

## Setup

### 1. Install dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Seed historical data (run once — takes ~5–10 minutes)
```bash
python3 scripts/seed_data.py
```
This fetches 25 years of NAV data from mfapi.in and stores it in `data/mf_backtest.db`.

### 3. Start the server
```bash
python3 run.py
```
Open **http://localhost:5000** in your browser.

## Data Sources

| Source | URL | What |
|--------|-----|------|
| mfapi.in | https://api.mfapi.in/mf/{code} | Historical NAV (free) |
| AMFI India | https://www.amfiindia.com/spages/NAVAll.txt | Fund metadata |
| NSE / yfinance | via `yfinance` library | Nifty TRI index data |

## Strategies

| ID | Name | Allocation |
|----|------|-----------|
| S1 | Large-Mid-Small 50-30-20 | 50% Large + 30% Mid + 20% Small |
| S2 | Equal Weight 33-33-33 | Equal Large/Mid/Small |
| S3 | Conservative 70-20-10 | 70% Large + 20% Mid + 10% Small |
| S4 | Aggressive 20-40-40 | 20% Large + 40% Mid + 40% Small |
| S5 | Flexi + Multi Asset | 60% Flexi Cap + 40% Multi Asset |
| S6 | Index Only (Passive) | 50% Nifty 50 + 30% Midcap 150 + 20% Smallcap 250 |
| S7 | ELSS Tax Saver | 40% ELSS + 30% Flexi + 30% Mid |
| S8 | Balanced Advantage | 50% BAF + 30% Large + 20% Mid |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | List all 8 strategies |
| GET | `/api/funds` | List registered funds with data availability |
| POST | `/api/run` | Run single strategy backtest |
| POST | `/api/run-all` | Run all strategies, return comparison |
| GET | `/api/nav/<fund_id>` | Get NAV history for a fund |
| POST | `/api/sip-projection` | Forward-looking SIP projection |

### `/api/run` request body
```json
{
  "strategy_id": "S1",
  "start_date": "2000-01-01",
  "end_date": "2024-12-31",
  "monthly_sip": 75000,
  "stepup_pct": 10
}
```

## Project Structure
```
mf_backtest/
├── backend/
│   ├── data/
│   │   ├── store.py            SQLite DB layer
│   │   ├── fund_registry.py    Fund catalog
│   │   ├── fetcher.py          mfapi.in NAV fetcher
│   │   ├── amfi_fetcher.py     AMFI metadata fetcher
│   │   └── index_fetcher.py    NSE/yfinance index fetcher
│   ├── backtest/
│   │   ├── engine.py           SIP simulation engine
│   │   ├── strategies.py       Strategy definitions
│   │   └── metrics.py          CAGR, XIRR, Sharpe, etc.
│   ├── api/routes.py           Flask API routes
│   └── app.py                  Flask app
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js              Main controller
│       ├── charts.js           Chart.js wrappers
│       ├── api.js              API client
│       └── utils.js            Helpers
├── data/mf_backtest.db         SQLite (created by seed_data.py)
├── scripts/seed_data.py        Data seeder
├── run.py                      Server entry point
└── requirements.txt
```

## Notes
- Past performance is not indicative of future returns
- Index data before 2001 (Midcap) / 2004 (Smallcap) uses proxies
- AMFI scheme codes in fund_registry.py may need updating if funds merge/rename
- Re-seed with `python3 scripts/seed_data.py --force` to refresh all data
