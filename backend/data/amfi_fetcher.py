"""Fetch AMFI bulk NAV data for fund metadata and live NAV."""
import requests
import io
from backend.data.store import upsert_fund

AMFI_ALL_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"


def fetch_amfi_fund_list() -> list:
    """
    Fetch the full AMFI fund list and return parsed dicts.
    Format: Scheme Code;ISIN Div Payout;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
    """
    try:
        resp = requests.get(AMFI_ALL_NAV_URL, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR fetching AMFI data: {e}")
        return []

    funds = []
    current_category = "unknown"

    for line in resp.text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Category headers look like "Open Ended Schemes(Equity Scheme - Large Cap Fund)"
        if not ";" in line:
            current_category = _parse_amfi_category(line)
            continue
        parts = line.split(";")
        if len(parts) < 6:
            continue
        scheme_code = parts[0].strip()
        scheme_name = parts[3].strip()
        try:
            nav = float(parts[4].strip()) if parts[4].strip() not in ("", "N.A.") else None
        except ValueError:
            nav = None

        funds.append({
            "amfi_code": scheme_code,
            "name": scheme_name,
            "category": current_category,
            "nav": nav,
        })

    print(f"AMFI: fetched {len(funds)} fund records")
    return funds


def _parse_amfi_category(header: str) -> str:
    h = header.lower()
    if "large cap" in h:
        return "large_cap"
    if "mid cap" in h:
        return "mid_cap"
    if "small cap" in h:
        return "small_cap"
    if "flexi cap" in h or "multi cap" in h:
        return "flexi_cap"
    if "multi asset" in h:
        return "multi_asset"
    if "elss" in h or "tax saver" in h:
        return "elss"
    if "balanced advantage" in h or "dynamic asset" in h:
        return "balanced_advantage"
    if "index" in h:
        return "index"
    if "debt" in h or "liquid" in h or "overnight" in h or "money market" in h:
        return "debt"
    return "other"


def build_amfi_code_map() -> dict:
    """Returns {amfi_code: fund_dict} for quick lookup."""
    funds = fetch_amfi_fund_list()
    return {f["amfi_code"]: f for f in funds}
