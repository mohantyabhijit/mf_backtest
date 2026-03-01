"""Fetch historical NAV data from mfapi.in."""
import requests
import time
from datetime import datetime
from backend.data.store import upsert_nav_batch, get_nav_date_range

MFAPI_BASE = "https://api.mfapi.in/mf"


def fetch_fund_nav(amfi_code: str, fund_id: str, force: bool = False) -> int:
    """
    Fetch all historical NAV for a fund from mfapi.in and store in DB.
    Returns number of rows inserted.
    """
    min_d, max_d = get_nav_date_range(fund_id)
    if max_d and not force:
        # Already have data; skip unless forced
        print(f"  [{fund_id}] already has data up to {max_d}, skipping.")
        return 0

    url = f"{MFAPI_BASE}/{amfi_code}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [{fund_id}] ERROR fetching {url}: {e}")
        return 0

    nav_entries = data.get("data", [])
    if not nav_entries:
        print(f"  [{fund_id}] No NAV data returned from mfapi.in")
        return 0

    rows = []
    for entry in nav_entries:
        try:
            # mfapi returns date as "DD-MM-YYYY"
            date_str = datetime.strptime(entry["date"], "%d-%m-%Y").strftime("%Y-%m-%d")
            nav = float(entry["nav"])
            rows.append((fund_id, date_str, nav))
        except (ValueError, KeyError):
            continue

    if rows:
        upsert_nav_batch(rows)
        print(f"  [{fund_id}] Stored {len(rows)} NAV records (earliest: {min(r[1] for r in rows)})")

    time.sleep(0.3)  # be polite to the free API
    return len(rows)


def fetch_all_funds(funds: list, force: bool = False):
    """Fetch NAV for all mfapi funds in registry."""
    total = 0
    mf_funds = [f for f in funds if f["source_type"] == "mfapi" and f["amfi_code"]]
    print(f"Fetching NAV data for {len(mf_funds)} funds from mfapi.in...")
    for fund in mf_funds:
        count = fetch_fund_nav(fund["amfi_code"], fund["id"], force=force)
        total += count
    print(f"Done. Total NAV rows stored: {total}")
    return total
