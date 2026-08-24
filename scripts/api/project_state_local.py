#!/usr/bin/env python3
"""Collect local project state and POST to the loopback Monitor ingest route."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.api.occupancy_local import resolve_launcher_host_id
from scripts.api.project_state_collect import collect_local_document
from scripts.api.project_state_sanitize import ProjectStateValidationError, validate_report_document

DEFAULT_POST_URL = "http://127.0.0.1:8765/api/fleet/projects/v1/report"
DEFAULT_TIMEOUT_S = 10.0


def _post_json(url: str, payload: dict, *, timeout_s: float) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and report per-host project state.")
    parser.add_argument("--host-id", help="Opaque reporter host id (default: resolve from env/config)")
    parser.add_argument("--repo-root", type=Path, help="Checkout root for collection (default: cwd)")
    parser.add_argument("--post-url", default=os.environ.get("MONITOR_PROJECT_STATE_URL", DEFAULT_POST_URL))
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--dry-run", action="store_true", help="Print JSON document only; do not POST")
    sub = parser.add_subparsers(dest="command")
    collect = sub.add_parser("collect", help="print sanitized JSON document")
    collect.add_argument("--dry-run", action="store_true", help="Print JSON document only; do not POST")
    sub.add_parser("report", help="collect and POST to loopback ingest")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "report"
    host_id = (args.host_id or resolve_launcher_host_id()).strip().lower()
    document = collect_local_document(host_id, repo_root=args.repo_root, include_lane_usage=True)
    if document is None:
        print("project-state: collection failed", file=sys.stderr)
        return 2
    try:
        validate_report_document(document)
    except ProjectStateValidationError as exc:
        print(f"project-state: validation failed: {exc}", file=sys.stderr)
        return 2

    if command == "collect" or args.dry_run:
        print(json.dumps(document, indent=2, sort_keys=True))
        return 0

    status, body = _post_json(args.post_url, document, timeout_s=args.timeout)
    if status == 200:
        print(body)
        return 0
    if status == 409:
        print("project-state: stale, skipped", file=sys.stderr)
        return 0
    if status == 400:
        print(f"project-state: invalid report ({status}): {body}", file=sys.stderr)
        return 1
    print(f"project-state: POST failed ({status}): {body}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
