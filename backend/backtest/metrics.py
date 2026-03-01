"""
Financial metrics calculator for backtest results.
Input: combined portfolio DataFrame from engine.simulate_strategy()
"""
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from datetime import date


RISK_FREE_RATE = 0.065  # 6.5% India 10-yr Gsec approximate


def calc_cagr(total_invested: float, final_value: float, years: float) -> float:
    """Annualized CAGR given invested amount, final value and duration in years."""
    if total_invested <= 0 or years <= 0 or final_value <= 0:
        return 0.0
    return round(((final_value / total_invested) ** (1.0 / years) - 1) * 100, 2)


def calc_xirr(cashflows: list, dates: list) -> float:
    """
    Compute XIRR for SIP cashflows.
    cashflows: list of floats (negative = outflow/SIP, positive = final portfolio value)
    dates: list of date objects or strings
    Returns annualized IRR as a percentage.
    """
    if len(cashflows) != len(dates) or len(cashflows) < 2:
        return 0.0

    dates_dt = [pd.Timestamp(d) for d in dates]
    t0 = dates_dt[0]
    day_fracs = [(d - t0).days / 365.25 for d in dates_dt]

    def npv(rate):
        return sum(cf / (1 + rate) ** t for cf, t in zip(cashflows, day_fracs))

    try:
        xirr = brentq(npv, -0.9, 100.0, maxiter=1000)
        return round(xirr * 100, 2)
    except Exception:
        return 0.0


def calc_max_drawdown(portfolio_values: pd.Series) -> float:
    """Maximum peak-to-trough decline as a percentage."""
    if portfolio_values.empty:
        return 0.0
    rolling_max = portfolio_values.cummax()
    drawdowns = (portfolio_values - rolling_max) / rolling_max * 100
    return round(drawdowns.min(), 2)  # negative value


def calc_volatility(portfolio_values: pd.Series) -> float:
    """Annualized volatility of monthly returns (std dev)."""
    if len(portfolio_values) < 2:
        return 0.0
    monthly_returns = portfolio_values.pct_change().dropna()
    return round(monthly_returns.std() * np.sqrt(12) * 100, 2)


def calc_sharpe(cagr_pct: float, volatility_pct: float) -> float:
    """Sharpe ratio = (CAGR - risk_free) / volatility."""
    if volatility_pct == 0:
        return 0.0
    return round((cagr_pct - RISK_FREE_RATE * 100) / volatility_pct, 3)


def calc_absolute_return(total_invested: float, final_value: float) -> float:
    """Total absolute return as a percentage."""
    if total_invested <= 0:
        return 0.0
    return round((final_value / total_invested - 1) * 100, 2)


def calc_sip_schedule(
    monthly_sip: float,
    start_year: int,
    end_year: int,
    stepup_pct: float = 10.0,
) -> list:
    """Return year-wise SIP amounts and cumulative invested."""
    schedule = []
    current_sip = monthly_sip
    cumulative = 0.0
    year = start_year
    step_year = start_year

    while year <= end_year:
        if year > step_year and (year - start_year) > 0:
            # Step up every April (approximate: once per year from year 2)
            current_sip *= (1 + stepup_pct / 100.0)
            step_year = year

        annual = current_sip * 12
        cumulative += annual
        schedule.append({
            "year": year,
            "monthly_sip": round(current_sip, 0),
            "annual_sip": round(annual, 0),
            "cumulative_invested": round(cumulative, 0),
        })
        year += 1

    return schedule


def compute_all_metrics(result: dict) -> dict:
    """
    Compute all metrics for a strategy result from engine.simulate_strategy().
    Returns a metrics dict.
    """
    combined = result["combined"]
    params = result["params"]

    if combined.empty:
        return {"error": "No data"}

    pv = combined["portfolio_value"]
    final_value = float(pv.iloc[-1])
    total_invested = float(combined["total_invested"].iloc[-1])

    start_ts = pd.Timestamp(params["start_date"])
    end_ts = pd.Timestamp(params["end_date"])
    years = (end_ts - start_ts).days / 365.25

    # XIRR cashflows: SIP payments (negative) + final value (positive)
    cf_dates = combined["date"].tolist()
    cf_values = [-float(r) for r in combined["sip_amount"]]
    cf_values[-1] += final_value  # Add portfolio value at end

    cagr = calc_cagr(total_invested, final_value, years)
    xirr = calc_xirr(cf_values, cf_dates)
    max_dd = calc_max_drawdown(pv)
    vol = calc_volatility(pv)
    sharpe = calc_sharpe(cagr, vol)
    abs_return = calc_absolute_return(total_invested, final_value)

    # Monthly portfolio series for charts
    chart_data = [
        {
            "date": str(row["date"])[:10],
            "portfolio_value": row["portfolio_value"],
            "total_invested": row["total_invested"],
        }
        for _, row in combined.iterrows()
    ]

    # Drawdown series
    rolling_max = pv.cummax()
    drawdown_series = ((pv - rolling_max) / rolling_max * 100).round(2)
    drawdown_data = [
        {"date": str(combined.iloc[i]["date"])[:10], "drawdown": float(drawdown_series.iloc[i])}
        for i in range(len(combined))
    ]

    # SIP schedule
    sip_schedule = calc_sip_schedule(
        params["monthly_sip"],
        start_ts.year,
        end_ts.year,
        params["stepup_pct"],
    )

    return {
        "cagr": cagr,
        "xirr": xirr,
        "absolute_return": abs_return,
        "total_invested": round(total_invested, 0),
        "final_value": round(final_value, 0),
        "gain": round(final_value - total_invested, 0),
        "max_drawdown": max_dd,
        "volatility": vol,
        "sharpe_ratio": sharpe,
        "years": round(years, 1),
        "chart_data": chart_data,
        "drawdown_data": drawdown_data,
        "sip_schedule": sip_schedule,
    }
