"""
Keeps the investment research team running on a daily schedule.

Usage:
    python scheduler.py             # Start the scheduler (runs at RUN_TIME daily)
    python scheduler.py --run-now   # Trigger one run immediately, then keep scheduling

Configure via .env:
    RUN_TIME=08:00   (24-hour format, server local time)
"""

import logging
import sys
from datetime import datetime

import schedule
import time

from investment_research.config import RUN_TIME
from main import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def scheduled_job() -> None:
    log.info("Scheduled run starting…")
    try:
        main()
        log.info("Scheduled run completed successfully.")
    except Exception as exc:
        log.exception("Scheduled run failed: %s", exc)


def run_scheduler() -> None:
    schedule.every().day.at(RUN_TIME).do(scheduled_job)
    log.info("Investment Research Team scheduler started.")
    log.info("Daily briefing will run at %s (server local time).", RUN_TIME)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    if "--run-now" in sys.argv:
        log.info("--run-now flag detected; running immediately.")
        scheduled_job()

    run_scheduler()
