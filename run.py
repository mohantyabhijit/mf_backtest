#!/usr/bin/env python3
"""Entry point: run the Flask development server."""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app
from backend.data.store import init_db

if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 50)
    print("  MF Backtest Server starting...")
    print("  Open: http://localhost:5000")
    print("  First time? Run: python3 scripts/seed_data.py")
    print("=" * 50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
