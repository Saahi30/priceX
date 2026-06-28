import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PRIORITY_STOCKS_FILE = BASE_DIR / "priority_stocks.json"
DATA_FILE = BASE_DIR / "stocks_data.json"

def load_priority_stocks():
    if PRIORITY_STOCKS_FILE.exists():
        with open(PRIORITY_STOCKS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("high_priority_stocks", [])
            except json.JSONDecodeError:
                pass
    return []
