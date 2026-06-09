import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-8"

# ntfy.sh push notifications — install the free ntfy app, subscribe to your topic
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "investment-research-alerts")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NTFY_ENABLED = os.environ.get("NTFY_ENABLED", "true").lower() == "true"

# Daily run time in 24-hour HH:MM format (local server time)
RUN_TIME = os.environ.get("RUN_TIME", "08:00")

PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
