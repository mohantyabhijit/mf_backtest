"""Flask API routes for MF Backtest."""
from flask import Blueprint, request, jsonify
from backend.backtest.strategies import list_strategies, get_strategy, STRATEGIES
from backend.backtest.engine import simulate_strategy
from backend.backtest.metrics import compute_all_metrics
from backend.data.store import get_all_funds, get_nav_series, get_index_series, get_fund, get_nav_date_range
from backend.data.fund_registry import FUNDS

api = Blueprint("api", __name__, url_prefix="/api")

DEFAULT_START = "2000-01-01"
DEFAULT_END   = "2024-12-31"
DEFAULT_SIP   = 75000
DEFAULT_STEP  = 10.0


@api.route("/strategies", methods=["GET"])
def strategies():
    return jsonify(list_strategies())


@api.route("/funds", methods=["GET"])
def funds():
    db_funds = get_all_funds()
    # Enrich with data availability
    result = []
    for f in db_funds:
        min_d, max_d = get_nav_date_range(f["id"])
        result.append({**f, "data_from": min_d, "data_to": max_d})
    return jsonify(result)


@api.route("/run", methods=["POST"])
def run_backtest():
    body = request.get_json(force=True) or {}
    strategy_id = body.get("strategy_id", "S1")
    start_date  = body.get("start_date", DEFAULT_START)
    end_date    = body.get("end_date", DEFAULT_END)
    monthly_sip = float(body.get("monthly_sip", DEFAULT_SIP))
    stepup_pct  = float(body.get("stepup_pct", DEFAULT_STEP))

    strategy = get_strategy(strategy_id)
    if not strategy:
        return jsonify({"error": f"Unknown strategy: {strategy_id}"}), 400

    try:
        result = simulate_strategy(
            allocations=strategy["allocations"],
            start_date=start_date,
            end_date=end_date,
            monthly_sip=monthly_sip,
            stepup_pct=stepup_pct,
        )
        metrics = compute_all_metrics(result)
        metrics["strategy"] = {
            "id": strategy["id"],
            "name": strategy["name"],
            "description": strategy["description"],
            "color": strategy["color"],
            "allocations": strategy["allocations"],
        }
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/run-all", methods=["POST"])
def run_all():
    """Run all strategies with the same params and return comparison."""
    body = request.get_json(force=True) or {}
    start_date  = body.get("start_date", DEFAULT_START)
    end_date    = body.get("end_date", DEFAULT_END)
    monthly_sip = float(body.get("monthly_sip", DEFAULT_SIP))
    stepup_pct  = float(body.get("stepup_pct", DEFAULT_STEP))

    results = []
    for sid, strategy in STRATEGIES.items():
        try:
            result = simulate_strategy(
                allocations=strategy["allocations"],
                start_date=start_date,
                end_date=end_date,
                monthly_sip=monthly_sip,
                stepup_pct=stepup_pct,
            )
            metrics = compute_all_metrics(result)
            results.append({
                "strategy_id":    sid,
                "name":           strategy["name"],
                "color":          strategy["color"],
                "cagr":           metrics.get("cagr"),
                "xirr":           metrics.get("xirr"),
                "absolute_return":metrics.get("absolute_return"),
                "total_invested": metrics.get("total_invested"),
                "final_value":    metrics.get("final_value"),
                "gain":           metrics.get("gain"),
                "max_drawdown":   metrics.get("max_drawdown"),
                "volatility":     metrics.get("volatility"),
                "sharpe_ratio":   metrics.get("sharpe_ratio"),
                "chart_data":     metrics.get("chart_data"),
            })
        except Exception as e:
            results.append({"strategy_id": sid, "name": strategy["name"], "error": str(e)})

    return jsonify(results)


@api.route("/nav/<fund_id>", methods=["GET"])
def nav_history(fund_id):
    fund = get_fund(fund_id)
    if not fund:
        return jsonify({"error": "Fund not found"}), 404

    start = request.args.get("start", DEFAULT_START)
    end   = request.args.get("end", DEFAULT_END)

    if fund["source_type"] == "index":
        rows = get_index_series(fund["proxy_fund"], start, end)
        data = [{"date": r["date"], "nav": r["value"]} for r in rows]
    else:
        rows = get_nav_series(fund_id, start, end)
        data = [{"date": r["date"], "nav": r["nav"]} for r in rows]

    return jsonify({"fund": dict(fund), "nav_data": data})


@api.route("/sip-projection", methods=["POST"])
def sip_projection():
    """Project future SIP corpus without historical data (pure math)."""
    from backend.backtest.metrics import calc_sip_schedule
    body = request.get_json(force=True) or {}
    monthly_sip = float(body.get("monthly_sip", DEFAULT_SIP))
    stepup_pct  = float(body.get("stepup_pct", DEFAULT_STEP))
    years       = int(body.get("years", 15))
    expected_return = float(body.get("expected_return", 14.0)) / 100  # annual

    from datetime import date
    start_year = date.today().year
    end_year = start_year + years - 1

    schedule = calc_sip_schedule(monthly_sip, start_year, end_year, stepup_pct)

    # Month-by-month projection
    monthly_rate = (1 + expected_return) ** (1/12) - 1
    corpus = 0.0
    current_monthly = monthly_sip
    step_year = start_year
    projections = []

    for yr in range(start_year, end_year + 1):
        if yr > step_year:
            current_monthly *= (1 + stepup_pct / 100.0)
            step_year = yr
        for m in range(12):
            corpus = (corpus + current_monthly) * (1 + monthly_rate)
        projections.append({
            "year": yr,
            "corpus": round(corpus, 0),
            "monthly_sip": round(current_monthly, 0),
        })

    total_invested = sum(s["annual_sip"] for s in schedule)
    return jsonify({
        "projections": projections,
        "sip_schedule": schedule,
        "total_invested": round(total_invested, 0),
        "final_corpus": round(corpus, 0),
        "expected_return_pct": expected_return * 100,
    })
