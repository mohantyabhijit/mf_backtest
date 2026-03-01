#!/usr/bin/env python3
"""
One-time data seeder script.
Initialises the DB and fetches 25 years of NAV + index data.
Run: python3 -m scripts.seed_data   (from project root)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data.store import init_db, upsert_fund
from backend.data.fund_registry import FUNDS
from backend.data.fetcher import fetch_all_funds
from backend.data.index_fetcher import fetch_all_indices


def seed(force: bool = False):
    print("=" * 60)
    print("MF Backtest — Data Seeder")
    print("=" * 60)

    # 1. Init DB schema
    print("\n[1/4] Initialising database...")
    init_db()

    # 2. Insert fund registry
    print(f"\n[2/4] Inserting {len(FUNDS)} funds into registry...")
    for fund in FUNDS:
        upsert_fund(fund)
        print(f"  Registered: {fund['id']} ({fund['category']})")

    # 3. Fetch NAV data from mfapi.in
    print("\n[3/4] Fetching mutual fund NAV data from mfapi.in...")
    print("  (This may take a few minutes for the full history)")
    fetch_all_funds(FUNDS, force=force)

    # 4. Fetch index TRI data
    print("\n[4/4] Fetching index TRI data...")
    fetch_all_indices(force=force)

    print("\n" + "=" * 60)
    print("Seeding complete! Run: python3 -m backend.app")
    print("=" * 60)


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed(force=force)
