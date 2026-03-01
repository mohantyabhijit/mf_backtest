"""
SIP Backtest Engine.
Simulates monthly SIP investments into one or multiple funds
with annual step-up, returning a portfolio DataFrame.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from backend.data.store import get_nav_series, get_index_series, get_fund


def _load_price_series(fund_id: str, start: str, end: str) -> pd.Series:
    """
    Load NAV/index data for a fund. Uses index proxy where fund has no data.
    Returns pd.Series indexed by date (datetime.date).
    """
    fund = get_fund(fund_id)
    if fund is None:
        raise ValueError(f"Fund not found: {fund_id}")

    if fund["source_type"] == "index":
        # Direct index
        rows = get_index_series(fund["proxy_fund"], start, end)
        data = {r["date"]: r["value"] for r in rows}
    else:
        rows = get_nav_series(fund_id, start, end)
        data = {r["date"]: r["nav"] for r in rows}

        # Fill pre-launch period with proxy index data
        if fund["proxy_fund"] and fund["launch_date"] and start < fund["launch_date"]:
            proxy_rows = get_index_series(fund["proxy_fund"], start, fund["launch_date"])
            if proxy_rows and data:
                # Scale proxy to match fund's first NAV
                fund_dates = sorted(data.keys())
                first_fund_nav = data[fund_dates[0]]
                proxy_list = sorted(proxy_rows, key=lambda r: r["date"])
                proxy_last = proxy_list[-1]["value"] if proxy_list else None

                if proxy_last and proxy_last > 0:
                    scale = first_fund_nav / proxy_last
                    for r in proxy_rows:
                        if r["date"] not in data:
                            data[r["date"]] = r["value"] * scale

    if not data:
        raise ValueError(f"No price data found for fund '{fund_id}' between {start} and {end}")

    series = pd.Series(data)
    series.index = pd.to_datetime(series.index)
    series = series.sort_index()
    return series


def _get_nav_on_or_after(series: pd.Series, target_date: pd.Timestamp) -> tuple:
    """Return (date, nav) for target_date or next available trading day."""
    # Look within 7 days forward (holidays, weekends)
    for delta in range(8):
        d = target_date + pd.Timedelta(days=delta)
        if d in series.index:
            return d, series[d]
    return None, None


def simulate_sip(
    fund_id: str,
    start_date: str,          # "YYYY-MM-DD"
    end_date: str,            # "YYYY-MM-DD"
    monthly_sip: float,       # INR, starting amount
    stepup_pct: float = 10.0, # % increase every April
    allocation: float = 1.0,  # fraction of monthly_sip allocated to this fund
) -> pd.DataFrame:
    """
    Simulate SIP for a single fund.
    Returns DataFrame with columns:
        date, sip_amount, nav, units_bought, total_units, portfolio_value, total_invested
    """
    series = _load_price_series(fund_id, start_date, end_date)

    current_sip = monthly_sip * allocation
    records = []
    total_units = 0.0
    total_invested = 0.0

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)

    # Iterate month by month
    current = start.replace(day=1)
    sip_year = current.year
    current_annual_sip = monthly_sip  # track base (pre-allocation) for step-ups

    while current <= end:
        # April step-up: increase SIP on April 1st
        if current.month == 4 and current.year > sip_year:
            current_annual_sip *= (1 + stepup_pct / 100.0)
            sip_year = current.year

        month_sip = current_annual_sip * allocation

        nav_date, nav = _get_nav_on_or_after(series, current)
        if nav_date is not None and nav > 0:
            units = month_sip / nav
            total_units += units
            total_invested += month_sip
            portfolio_value = total_units * nav
            records.append({
                "date": nav_date,
                "sip_amount": round(month_sip, 2),
                "nav": round(nav, 4),
                "units_bought": round(units, 4),
                "total_units": round(total_units, 4),
                "portfolio_value": round(portfolio_value, 2),
                "total_invested": round(total_invested, 2),
            })

        current = (current + relativedelta(months=1)).replace(day=1)

    return pd.DataFrame(records)


def simulate_strategy(
    allocations: dict,        # {fund_id: weight_fraction}  (must sum to 1.0)
    start_date: str,
    end_date: str,
    monthly_sip: float,
    stepup_pct: float = 10.0,
) -> dict:
    """
    Simulate a multi-fund strategy.
    allocations: {fund_id: fraction, ...}
    Returns {
        'combined': combined portfolio DataFrame (monthly),
        'funds': {fund_id: individual DataFrame},
        'params': {start_date, end_date, monthly_sip, stepup_pct}
    }
    """
    if abs(sum(allocations.values()) - 1.0) > 0.01:
        raise ValueError("Allocations must sum to 1.0")

    fund_results = {}
    for fund_id, weight in allocations.items():
        try:
            df = simulate_sip(
                fund_id, start_date, end_date,
                monthly_sip, stepup_pct, allocation=weight
            )
            fund_results[fund_id] = df
        except Exception as e:
            print(f"  Warning: could not simulate {fund_id}: {e}")

    if not fund_results:
        raise ValueError("No fund data available for any fund in strategy")

    # Combine: sum portfolio values and investments by date
    all_dates = sorted(set(
        d for df in fund_results.values() for d in df["date"].tolist()
    ))

    combined_rows = []
    for d in all_dates:
        total_pv = 0.0
        total_inv = 0.0
        total_sip = 0.0
        for fund_id, df in fund_results.items():
            row = df[df["date"] == d]
            if not row.empty:
                total_pv += row.iloc[-1]["portfolio_value"]
                total_inv += row.iloc[-1]["total_invested"]
                total_sip += row.iloc[-1]["sip_amount"]

        combined_rows.append({
            "date": d,
            "sip_amount": round(total_sip, 2),
            "portfolio_value": round(total_pv, 2),
            "total_invested": round(total_inv, 2),
            "gain": round(total_pv - total_inv, 2),
            "gain_pct": round((total_pv / total_inv - 1) * 100, 2) if total_inv > 0 else 0,
        })

    combined = pd.DataFrame(combined_rows)

    return {
        "combined": combined,
        "funds": fund_results,
        "params": {
            "start_date": start_date,
            "end_date": end_date,
            "monthly_sip": monthly_sip,
            "stepup_pct": stepup_pct,
            "allocations": allocations,
        },
    }
