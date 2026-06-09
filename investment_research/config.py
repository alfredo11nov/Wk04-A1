import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-8"

# ntfy.sh push notifications
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "investment-research-alerts")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NTFY_ENABLED = os.environ.get("NTFY_ENABLED", "true").lower() == "true"

# Two-stage daily schedule (Asia/Singapore = UTC+8)
TIMEZONE = "Asia/Singapore"
RESEARCH_TIME = os.environ.get("RESEARCH_TIME", "06:00")   # Financial Analyst + Fund Manager
DELIVERY_TIME = os.environ.get("DELIVERY_TIME", "08:00")   # Admin report + push notification

PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
CACHE_FILE     = DATA_DIR / "research_cache.json"
