#!/usr/bin/env python3
"""
Self-healing watchdog — monitors batch builds, cleans zombies, alerts on stalls.

Does NOT auto-restart anything. Just keeps the environment clean and loud about problems.

Usage:
    .venv/bin/python scripts/watchdog.py              # Run once
    .venv/bin/python scripts/watchdog.py --loop        # Run every 5 min
    .venv/bin/python scripts/watchdog.py --loop --interval 120  # Every 2 min
    .venv/bin/python scripts/watchdog.py --dry-run     # Show what would be cleaned

Requires the monitoring API at localhost:8765.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

API_BASE = "http://localhost:8765/api/comms"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "watchdog.log"

# Thresholds
STALE_MSG_HOURS = 4.0       # Force-ack messages older than this
STALL_MINUTES = 30           # Alert if no new files in this window
ZOMBIE_CLEAN_INTERVAL = 600  # Clean zombies every 10 min (when looping)


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, mode="a"),
        ],
    )


def api_get(path: str) -> dict | None:
    try:
        req = Request(f"{API_BASE}/{path}", method="GET")
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (URLError, json.JSONDecodeError, OSError) as e:
        logging.error(f"API GET {path} failed: {e}")
        return None


def api_post(path: str) -> dict | None:
    try:
        req = Request(f"{API_BASE}/{path}", method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (URLError, json.JSONDecodeError, OSError) as e:
        logging.error(f"API POST {path} failed: {e}")
        return None


def check_api_health() -> bool:
    """Verify the monitoring API is reachable."""
    data = api_get("health")
    if not data:
        logging.error("Monitoring API unreachable at localhost:8765")
        return False
    if not data.get("db_exists"):
        logging.error("Broker DB does not exist")
        return False
    logging.info(
        f"API healthy — DB: {data.get('db_size_kb', 0)} KB, "
        f"queue: {data.get('queue_depth', 0)}, "
        f"alive PIDs: {data.get('alive_processes', 0)}"
    )
    return True


def check_batch_progress() -> dict:
    """Check batch progress and report stalled/dead tracks."""
    data = api_get("batch-progress")
    if not data:
        return {"healthy": 0, "stalled": 0, "dead": 0, "complete": 0}

    counts = {"healthy": 0, "stalled": 0, "dead": 0, "complete": 0, "unknown": 0}
    alerts = []

    for track, info in (data.get("tracks") or {}).items():
        health = info.get("health", "unknown")
        counts[health] = counts.get(health, 0) + 1

        done = info.get("research_done", 0)
        total = info.get("total_expected", 0)
        pct = round(done / total * 100) if total > 0 else 0

        if health == "dead":
            alerts.append(f"DEAD: {track} — {done}/{total} ({pct}%) — no process, log stale")
        elif health == "stalled":
            last = info.get("last_created")
            age_str = f"{last['seconds_ago']}s ago" if last else "unknown"
            alerts.append(f"STALLED: {track} — {done}/{total} ({pct}%) — last file: {age_str}")
        elif health == "healthy":
            tput = info.get("throughput_per_hour", 0)
            logging.info(f"  {track}: healthy — {done}/{total} ({pct}%) — {tput}/hr")

    # Log completed
    for track, info in (data.get("tracks") or {}).items():
        if info.get("health") == "complete":
            done = info.get("research_done", 0)
            logging.info(f"  {track}: COMPLETE — {done}/{done}")

    # Alerts
    for alert in alerts:
        logging.warning(f"  {alert}")

    logging.info(
        f"Batch summary: {counts['healthy']} healthy, {counts['stalled']} stalled, "
        f"{counts['dead']} dead, {counts['complete']} complete — "
        f"{data.get('running_processes', 0)} processes running"
    )

    return counts


def clean_zombies(dry_run: bool = False) -> int:
    """Detect and clean zombie messages + orphan PIDs."""
    data = api_get(f"zombies?stale_hours={STALE_MSG_HOURS}")
    if not data:
        return 0

    zombies = data.get("zombies", [])
    if not zombies:
        logging.info("No zombies detected")
        return 0

    # Categorize
    stale = [z for z in zombies if z["type"] == "stale_message"]
    orphans = [z for z in zombies if z["type"] == "orphan_pid"]
    pingpongs = [z for z in zombies if z["type"] == "pingpong"]
    error_loops = [z for z in zombies if z["type"] == "error_loop"]

    logging.info(
        f"Zombies found: {len(stale)} stale msgs, {len(orphans)} orphan PIDs, "
        f"{len(pingpongs)} ping-pong loops, {len(error_loops)} error loops"
    )

    if dry_run:
        for z in zombies:
            logging.info(f"  [DRY-RUN] would clean: {z['type']} — {z}")
        return 0

    cleaned = 0

    # Ack stale messages individually so we can log them
    for z in stale:
        msg_id = z.get("message_id")
        if msg_id:
            result = api_post(f"acknowledge/{msg_id}")
            if result:
                cleaned += 1
                logging.info(
                    f"  Acked stale msg #{msg_id} — "
                    f"from={z.get('from')}, to={z.get('to')}, "
                    f"age={z.get('age_hours', '?')}h, task={z.get('task_id', '?')}"
                )

    # Full cleanup for orphan PIDs
    if orphans:
        result = api_post(f"cleanup?max_age_hours={STALE_MSG_HOURS}")
        if result:
            extra = result.get("cleaned", 0) - cleaned
            if extra > 0:
                cleaned += extra
                logging.info(f"  Cleaned {extra} orphan PID files")

    # Alert on ping-pong and error loops (don't auto-fix, just warn loudly)
    for z in pingpongs:
        logging.warning(
            f"  PING-PONG: task={z.get('task_id')} — "
            f"{z.get('message_count_1h')} msgs in 1h"
        )
    for z in error_loops:
        logging.warning(
            f"  ERROR LOOP: task={z.get('task_id')} — "
            f"{z.get('error_count')} errors"
        )

    logging.info(f"Cleaned {cleaned} zombies total")
    return cleaned


def check_message_stats():
    """Log message flow stats."""
    data = api_get("stats")
    if not data:
        return

    logging.info(
        f"Comms stats: {data.get('total_messages', 0)} total, "
        f"{data.get('last_hour', 0)} last hour, "
        f"{data.get('unacked', 0)} unacked, "
        f"{data.get('error_rate', 0)}% errors"
    )

    # Warn if error rate is high
    error_rate = data.get("error_rate", 0)
    if error_rate > 10:
        logging.warning(f"High error rate: {error_rate}%")

    # Warn if queue depth is growing
    unacked = data.get("unacked", 0)
    if unacked > 200:
        logging.warning(f"Large unacked queue: {unacked} messages")


def run_once(dry_run: bool = False):
    """Single watchdog pass."""
    logging.info("=" * 50)
    logging.info(f"Watchdog pass — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 50)

    if not check_api_health():
        logging.error("Aborting — API not reachable")
        return

    check_batch_progress()
    clean_zombies(dry_run=dry_run)
    check_message_stats()

    logging.info("Watchdog pass complete")
    logging.info("")


def main():
    parser = argparse.ArgumentParser(description="Batch build watchdog")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between checks (default: 300)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without acting")
    args = parser.parse_args()

    setup_logging()

    if args.loop:
        logging.info(f"Watchdog starting in loop mode — interval: {args.interval}s")
        while True:
            try:
                run_once(dry_run=args.dry_run)
            except KeyboardInterrupt:
                logging.info("Watchdog stopped by user")
                break
            except Exception as e:
                logging.error(f"Watchdog error: {e}")
            time.sleep(args.interval)
    else:
        run_once(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
