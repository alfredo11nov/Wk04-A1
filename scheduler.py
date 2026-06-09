"""
Two-stage daily scheduler (Asia/Singapore timezone).

  06:00 SGT — Stage 1: Financial Analyst + Fund Manager  (background research)
  08:00 SGT — Stage 2: Admin formats briefing + sends push notification

Usage:
    python scheduler.py                  # Start scheduler (runs every day)
    python scheduler.py --run-now        # Fire both stages immediately, then schedule

Configure via .env:
    RESEARCH_TIME=06:00
    DELIVERY_TIME=08:00
"""

import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from investment_research.config import RESEARCH_TIME, DELIVERY_TIME, TIMEZONE
from investment_research.agents import run_stage1, run_stage2
from investment_research.notifications import send_push_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

sgt = pytz.timezone(TIMEZONE)


def stage1_job() -> None:
    log.info("Stage 1 starting — background research…")
    try:
        run_stage1()
        log.info("Stage 1 complete.")
    except Exception as exc:
        log.exception("Stage 1 failed: %s", exc)


def stage2_job() -> None:
    log.info("Stage 2 starting — delivering briefing…")
    try:
        results = run_stage2()

        print("\n" + "=" * 64)
        print("  DAILY INVESTMENT BRIEFING")
        print("=" * 64)
        print(results["briefing"])
        print("=" * 64 + "\n")

        sent = send_push_notification(results["push_notification"])
        if not sent:
            log.info("Push summary: %s", results["push_notification"])

        log.info("Stage 2 complete — briefing delivered.")
    except Exception as exc:
        log.exception("Stage 2 failed: %s", exc)


def _parse_time(t: str) -> tuple[int, int]:
    h, m = t.split(":")
    return int(h), int(m)


def run_scheduler() -> None:
    scheduler = BlockingScheduler(timezone=sgt)

    r_hour, r_min = _parse_time(RESEARCH_TIME)
    d_hour, d_min = _parse_time(DELIVERY_TIME)

    scheduler.add_job(
        stage1_job,
        CronTrigger(hour=r_hour, minute=r_min, timezone=sgt),
        id="stage1_research",
        name=f"Stage 1 Research @ {RESEARCH_TIME} SGT",
    )
    scheduler.add_job(
        stage2_job,
        CronTrigger(hour=d_hour, minute=d_min, timezone=sgt),
        id="stage2_delivery",
        name=f"Stage 2 Delivery @ {DELIVERY_TIME} SGT",
    )

    log.info("Investment Research Team scheduler started.")
    log.info("Stage 1 (research) : %s SGT", RESEARCH_TIME)
    log.info("Stage 2 (delivery) : %s SGT", DELIVERY_TIME)
    log.info("Timezone           : %s", TIMEZONE)

    scheduler.start()


if __name__ == "__main__":
    if "--run-now" in sys.argv:
        log.info("--run-now: firing both stages immediately.")
        stage1_job()
        stage2_job()

    run_scheduler()
