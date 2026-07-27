import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PRIORITY_STOCKS_FILE = BASE_DIR / "priority_stocks.json"
DATA_FILE = BASE_DIR / "stocks_data.json"

def load_priority_stocks():
    # First try reading from the environment variable provided by GitHub Actions
    env_priority = os.environ.get("PRIORITY_STOCKS")
    if env_priority:
        try:
            data = json.loads(env_priority)
            return data.get("high_priority_stocks", [])
        except json.JSONDecodeError:
            pass

    # Fallback to local file if it exists
    if PRIORITY_STOCKS_FILE.exists():
        with open(PRIORITY_STOCKS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("high_priority_stocks", [])
            except json.JSONDecodeError:
                pass
    return []
