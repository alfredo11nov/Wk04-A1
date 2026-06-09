"""
Entry point — run the investment research team once.

Usage:
    python main.py           # Run now and print the briefing
    python main.py --quiet   # Run but suppress intermediate progress lines
"""

import sys

from investment_research.agents import run_research_team
from investment_research.notifications import send_push_notification


def main() -> None:
    results = run_research_team()

    # ── Print full briefing to Claude chat / terminal ─────────────────────────
    print("\n" + "=" * 64)
    print("  DAILY INVESTMENT BRIEFING")
    print("=" * 64)
    print(results["briefing"])
    print("=" * 64 + "\n")

    # ── Push notification (short summary to phone/desktop) ────────────────────
    sent = send_push_notification(results["push_notification"])
    if not sent:
        print(f"Push summary: {results['push_notification']}")


if __name__ == "__main__":
    main()
