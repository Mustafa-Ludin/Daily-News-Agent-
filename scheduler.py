from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from main import run_workflow


def run_scheduler() -> None:
    load_dotenv()

    timezone_name = os.getenv("SCHEDULER_TIMEZONE", "America/New_York")
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        _log(f"Invalid SCHEDULER_TIMEZONE '{timezone_name}', falling back to UTC.")
        timezone_name = "UTC"
        timezone = ZoneInfo(timezone_name)

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        _scheduled_job,
        trigger=CronTrigger(hour=8, minute=0, timezone=timezone),
        id="daily_ai_news_workflow",
        name="Daily AI News Workflow",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    _log("Scheduler started")
    _log(f"Daily job scheduled for 8:00 AM ({timezone_name}).")
    _log("Waiting for next run...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        _log("Scheduler stopped.")


def _scheduled_job() -> None:
    try:
        run_workflow()
    except Exception as exc:
        _log(f"Job failed: {exc}")
    else:
        _log("Job executed successfully")
    finally:
        _log("Waiting for next run...")


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


if __name__ == "__main__":
    run_scheduler()
