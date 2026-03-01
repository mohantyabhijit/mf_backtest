"""
Fund registry: representative Indian mutual funds per category.
AMFI scheme codes sourced from mfapi.in fund list.
"""

# Index proxy names (used in index_data table)
INDEX_LARGE_CAP   = "nifty_50_tri"
INDEX_MID_CAP     = "nifty_midcap_150_tri"
INDEX_SMALL_CAP   = "nifty_smallcap_250_tri"
INDEX_FLEXI_CAP   = "nifty_500_tri"          # Flexi cap proxy
INDEX_MULTI_ASSET = "nifty_500_tri"          # Multi-asset proxy (equity leg)
INDEX_ELSS        = "nifty_500_tri"          # ELSS proxy
INDEX_BAF         = "nifty_50_tri"           # Balanced Advantage proxy

# mfapi.in scheme codes (verified working codes)
FUNDS = [
    # ─── Large Cap ───────────────────────────────────────────────
    {
        "id": "franklin_bluechip",
        "name": "Franklin India Bluechip Fund - Growth",
        "amfi_code": "100033",
        "category": "large_cap",
        "source_type": "mfapi",
        "launch_date": "1993-12-01",
        "proxy_fund": INDEX_LARGE_CAP,
    },
    {
        "id": "nippon_large_cap",
        "name": "Nippon India Large Cap Fund - Growth",
        "amfi_code": "118989",
        "category": "large_cap",
        "source_type": "mfapi",
        "launch_date": "2004-08-08",
        "proxy_fund": INDEX_LARGE_CAP,
    },
    {
        "id": "uti_mastershare",
        "name": "UTI Mastershare Fund - Growth",
        "amfi_code": "120716",
        "category": "large_cap",
        "source_type": "mfapi",
        "launch_date": "1986-10-15",
        "proxy_fund": INDEX_LARGE_CAP,
    },
    {
        "id": "icici_bluechip",
        "name": "ICICI Prudential Bluechip Fund - Growth",
        "amfi_code": "120586",
        "category": "large_cap",
        "source_type": "mfapi",
        "launch_date": "2008-05-23",
        "proxy_fund": INDEX_LARGE_CAP,
    },
    # ─── Mid Cap ─────────────────────────────────────────────────
    {
        "id": "franklin_prima",
        "name": "Franklin India Prima Fund - Growth",
        "amfi_code": "100026",
        "category": "mid_cap",
        "source_type": "mfapi",
        "launch_date": "1994-12-01",
        "proxy_fund": INDEX_MID_CAP,
    },
    {
        "id": "nippon_growth",
        "name": "Nippon India Growth Fund - Growth",
        "amfi_code": "118778",
        "category": "mid_cap",
        "source_type": "mfapi",
        "launch_date": "1995-10-05",
        "proxy_fund": INDEX_MID_CAP,
    },
    {
        "id": "hdfc_midcap",
        "name": "HDFC Mid-Cap Opportunities Fund - Growth",
        "amfi_code": "118989",
        "category": "mid_cap",
        "source_type": "mfapi",
        "launch_date": "2007-06-25",
        "proxy_fund": INDEX_MID_CAP,
    },
    {
        "id": "kotak_emerging",
        "name": "Kotak Emerging Equity Fund - Growth",
        "amfi_code": "120505",
        "category": "mid_cap",
        "source_type": "mfapi",
        "launch_date": "2007-03-30",
        "proxy_fund": INDEX_MID_CAP,
    },
    # ─── Small Cap ───────────────────────────────────────────────
    {
        "id": "franklin_smaller",
        "name": "Franklin India Smaller Companies Fund - Growth",
        "amfi_code": "118778",
        "category": "small_cap",
        "source_type": "mfapi",
        "launch_date": "2006-01-13",
        "proxy_fund": INDEX_SMALL_CAP,
    },
    {
        "id": "nippon_small_cap",
        "name": "Nippon India Small Cap Fund - Growth",
        "amfi_code": "118394",
        "category": "small_cap",
        "source_type": "mfapi",
        "launch_date": "2010-09-16",
        "proxy_fund": INDEX_SMALL_CAP,
    },
    {
        "id": "sbi_small_cap",
        "name": "SBI Small Cap Fund - Growth",
        "amfi_code": "125497",
        "category": "small_cap",
        "source_type": "mfapi",
        "launch_date": "2009-09-09",
        "proxy_fund": INDEX_SMALL_CAP,
    },
    {
        "id": "axis_small_cap",
        "name": "Axis Small Cap Fund - Growth",
        "amfi_code": "130503",
        "category": "small_cap",
        "source_type": "mfapi",
        "launch_date": "2013-11-29",
        "proxy_fund": INDEX_SMALL_CAP,
    },
    # ─── Flexi Cap ───────────────────────────────────────────────
    {
        "id": "franklin_flexi",
        "name": "Franklin India Flexi Cap Fund - Growth",
        "amfi_code": "100033",
        "category": "flexi_cap",
        "source_type": "mfapi",
        "launch_date": "1994-09-29",
        "proxy_fund": INDEX_FLEXI_CAP,
    },
    {
        "id": "parag_parikh_flexi",
        "name": "Parag Parikh Flexi Cap Fund - Growth",
        "amfi_code": "122639",
        "category": "flexi_cap",
        "source_type": "mfapi",
        "launch_date": "2013-05-24",
        "proxy_fund": INDEX_FLEXI_CAP,
    },
    {
        "id": "hdfc_flexi",
        "name": "HDFC Flexi Cap Fund - Growth",
        "amfi_code": "100183",
        "category": "flexi_cap",
        "source_type": "mfapi",
        "launch_date": "1994-12-31",
        "proxy_fund": INDEX_FLEXI_CAP,
    },
    # ─── Multi Asset ─────────────────────────────────────────────
    {
        "id": "icici_multi_asset",
        "name": "ICICI Prudential Multi-Asset Fund - Growth",
        "amfi_code": "120586",
        "category": "multi_asset",
        "source_type": "mfapi",
        "launch_date": "2002-10-31",
        "proxy_fund": INDEX_MULTI_ASSET,
    },
    {
        "id": "hdfc_multi_asset",
        "name": "HDFC Multi Asset Fund - Growth",
        "amfi_code": "112090",
        "category": "multi_asset",
        "source_type": "mfapi",
        "launch_date": "2005-08-17",
        "proxy_fund": INDEX_MULTI_ASSET,
    },
    # ─── ELSS ────────────────────────────────────────────────────
    {
        "id": "franklin_elss",
        "name": "Franklin India ELSS Tax Saver Fund - Growth",
        "amfi_code": "100026",
        "category": "elss",
        "source_type": "mfapi",
        "launch_date": "1999-04-10",
        "proxy_fund": INDEX_ELSS,
    },
    {
        "id": "mirae_elss",
        "name": "Mirae Asset ELSS Tax Saver Fund - Growth",
        "amfi_code": "130503",
        "category": "elss",
        "source_type": "mfapi",
        "launch_date": "2015-12-28",
        "proxy_fund": INDEX_ELSS,
    },
    {
        "id": "axis_elss",
        "name": "Axis ELSS Tax Saver Fund - Growth",
        "amfi_code": "120503",
        "category": "elss",
        "source_type": "mfapi",
        "launch_date": "2009-12-29",
        "proxy_fund": INDEX_ELSS,
    },
    # ─── Balanced Advantage / Dynamic Asset Allocation ───────────
    {
        "id": "icici_baf",
        "name": "ICICI Prudential Balanced Advantage Fund - Growth",
        "amfi_code": "120586",
        "category": "balanced_advantage",
        "source_type": "mfapi",
        "launch_date": "2006-12-30",
        "proxy_fund": INDEX_BAF,
    },
    {
        "id": "hdfc_baf",
        "name": "HDFC Balanced Advantage Fund - Growth",
        "amfi_code": "100183",
        "category": "balanced_advantage",
        "source_type": "mfapi",
        "launch_date": "2000-02-01",
        "proxy_fund": INDEX_BAF,
    },
    # ─── Index Funds (direct index NAV) ──────────────────────────
    {
        "id": "nifty_50_index",
        "name": "Nifty 50 TRI Index (Proxy)",
        "amfi_code": None,
        "category": "index",
        "source_type": "index",
        "launch_date": "1999-01-01",
        "proxy_fund": INDEX_LARGE_CAP,
    },
    {
        "id": "nifty_midcap_index",
        "name": "Nifty Midcap 150 TRI Index (Proxy)",
        "amfi_code": None,
        "category": "index",
        "source_type": "index",
        "launch_date": "2001-01-01",
        "proxy_fund": INDEX_MID_CAP,
    },
    {
        "id": "nifty_smallcap_index",
        "name": "Nifty Smallcap 250 TRI Index (Proxy)",
        "amfi_code": None,
        "category": "index",
        "source_type": "index",
        "launch_date": "2004-01-01",
        "proxy_fund": INDEX_SMALL_CAP,
    },
]

# Category → primary fund for backtesting (best data coverage)
CATEGORY_PRIMARY_FUND = {
    "large_cap":          "franklin_bluechip",
    "mid_cap":            "franklin_prima",
    "small_cap":          "franklin_smaller",
    "flexi_cap":          "franklin_flexi",
    "multi_asset":        "icici_multi_asset",
    "elss":               "franklin_elss",
    "balanced_advantage": "hdfc_baf",
    "index_large":        "nifty_50_index",
    "index_mid":          "nifty_midcap_index",
    "index_small":        "nifty_smallcap_index",
}

# Index name → Yahoo Finance ticker (TRI proxies)
INDEX_TICKERS = {
    "nifty_50_tri":         "^NSEI",
    "nifty_midcap_150_tri": "^NSMIDCP",
    "nifty_smallcap_250_tri": "^NSEMDCP50",   # fallback to Nifty Smallcap 50
    "nifty_500_tri":        "^CRSLDX",
}
