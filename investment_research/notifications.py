"""
Push notification delivery via ntfy.sh.

Setup (one-time):
  1. Install the free ntfy app on iOS/Android — https://ntfy.sh
  2. Subscribe to the topic you set in NTFY_TOPIC (.env)
  3. Desktop: open https://ntfy.sh/<your-topic> in a browser

No account required for basic use.
"""

import requests
from .config import NTFY_TOPIC, NTFY_SERVER, NTFY_ENABLED


def send_push_notification(message: str, title: str = "Investment Research Team") -> bool:
    """Send a push notification via ntfy.sh. Returns True on success."""
    if not NTFY_ENABLED:
        print("Push notifications disabled (NTFY_ENABLED=false).")
        return False

    safe_message = message[:200]

    try:
        resp = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=safe_message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "high",
                "Tags": "chart_with_upwards_trend,briefcase",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"Push notification sent to ntfy topic '{NTFY_TOPIC}'.")
            return True
        print(f"ntfy returned HTTP {resp.status_code}: {resp.text[:120]}")
        return False
    except requests.RequestException as exc:
        print(f"Push notification failed: {exc}")
        return False
