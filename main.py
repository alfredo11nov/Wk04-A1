"""
Run the investment research team.

    python main.py              # Full run right now (all 3 agents)
    python main.py --stage1     # Research only (Analyst + Fund Manager, saves cache)
    python main.py --stage2     # Delivery only (Admin loads cache, sends notification)
"""

import sys

from investment_research.agents import run_research_team, run_stage1, run_stage2
from investment_research.notifications import send_push_notification


def _deliver(results: dict) -> None:
    """Print briefing + send push notification."""
    print("\n" + "=" * 64)
    print("  DAILY INVESTMENT BRIEFING")
    print("=" * 64)
    print(results["briefing"])
    print("=" * 64 + "\n")

    sent = send_push_notification(results["push_notification"])
    if not sent:
        print(f"Push summary: {results['push_notification']}")


def main() -> None:
    args = sys.argv[1:]

    if "--stage1" in args:
        run_stage1()

    elif "--stage2" in args:
        results = run_stage2()
        _deliver(results)

    else:
        # Full run — kickoff or manual trigger
        results = run_research_team()
        _deliver(results)


if __name__ == "__main__":
    main()
