"""
Strategy definitions for Indian MF backtesting.
Each strategy maps fund_id → allocation weight (must sum to 1.0).
"""
from backend.data.fund_registry import CATEGORY_PRIMARY_FUND

def _primary(category: str) -> str:
    return CATEGORY_PRIMARY_FUND[category]


# ──────────────────────────────────────────────────────────────
# Strategy definitions
# ──────────────────────────────────────────────────────────────

STRATEGIES = {
    "S1": {
        "id": "S1",
        "name": "Large-Mid-Small 50-30-20",
        "description": "50% Large Cap + 30% Mid Cap + 20% Small Cap. Classic balanced equity allocation.",
        "color": "#4A90D9",
        "allocations": {
            _primary("large_cap"):  0.50,
            _primary("mid_cap"):    0.30,
            _primary("small_cap"):  0.20,
        },
    },
    "S2": {
        "id": "S2",
        "name": "Equal Weight 33-33-33",
        "description": "Equal allocation across Large, Mid and Small Cap. Higher mid/small exposure.",
        "color": "#7ED321",
        "allocations": {
            _primary("large_cap"):  0.334,
            _primary("mid_cap"):    0.333,
            _primary("small_cap"):  0.333,
        },
    },
    "S3": {
        "id": "S3",
        "name": "Conservative 70-20-10",
        "description": "70% Large Cap + 20% Mid Cap + 10% Small Cap. Lower risk, steadier growth.",
        "color": "#9B59B6",
        "allocations": {
            _primary("large_cap"):  0.70,
            _primary("mid_cap"):    0.20,
            _primary("small_cap"):  0.10,
        },
    },
    "S4": {
        "id": "S4",
        "name": "Aggressive Growth 20-40-40",
        "description": "20% Large + 40% Mid + 40% Small Cap. High risk, high potential returns.",
        "color": "#E74C3C",
        "allocations": {
            _primary("large_cap"):  0.20,
            _primary("mid_cap"):    0.40,
            _primary("small_cap"):  0.40,
        },
    },
    "S5": {
        "id": "S5",
        "name": "Flexi + Multi Asset",
        "description": "60% Flexi Cap + 40% Multi Asset. Fund manager driven allocation with multi-asset diversification.",
        "color": "#F39C12",
        "allocations": {
            _primary("flexi_cap"):    0.60,
            _primary("multi_asset"):  0.40,
        },
    },
    "S6": {
        "id": "S6",
        "name": "Index Only (Passive)",
        "description": "50% Nifty 50 + 30% Midcap 150 + 20% Smallcap 250. Pure index strategy, lowest cost.",
        "color": "#1ABC9C",
        "allocations": {
            "nifty_50_index":       0.50,
            "nifty_midcap_index":   0.30,
            "nifty_smallcap_index": 0.20,
        },
    },
    "S7": {
        "id": "S7",
        "name": "ELSS Tax Saver Focused",
        "description": "40% ELSS + 30% Flexi Cap + 30% Mid Cap. Tax saving with ₹1.5L/yr deduction under 80C.",
        "color": "#27AE60",
        "allocations": {
            _primary("elss"):       0.40,
            _primary("flexi_cap"):  0.30,
            _primary("mid_cap"):    0.30,
        },
    },
    "S8": {
        "id": "S8",
        "name": "Balanced Advantage",
        "description": "50% Balanced Advantage Fund + 30% Large Cap + 20% Mid Cap. Dynamic equity/debt allocation.",
        "color": "#E67E22",
        "allocations": {
            _primary("balanced_advantage"): 0.50,
            _primary("large_cap"):          0.30,
            _primary("mid_cap"):            0.20,
        },
    },
}


def get_strategy(strategy_id: str) -> dict:
    return STRATEGIES.get(strategy_id)


def list_strategies() -> list:
    return [
        {k: v for k, v in s.items() if k != "allocations"}
        for s in STRATEGIES.values()
    ]


def get_strategy_allocations(strategy_id: str) -> dict:
    s = STRATEGIES.get(strategy_id)
    return s["allocations"] if s else {}
