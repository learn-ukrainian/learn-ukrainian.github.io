"""Sol PR-M residual: reconcile PR open→merge metrics from GitHub (no content).

Uses ``gh pr list --json`` only. Never stores PR bodies or review text —
numbers and timestamps only.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def collect_github_pr_metrics(
    *,
    repo: str = "learn-ukrainian/learn-ukrainian.github.io",
    search: str = "fleet-comms",
    limit: int = 30,
    gh_bin: str = "gh",
) -> dict[str, Any]:
    """Return open→merge latency stats for matching PRs (metadata only)."""
    cmd = [
        gh_bin,
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "merged",
        "--search",
        search,
        "--limit",
        str(limit),
        "--json",
        "number,title,createdAt,mergedAt,additions,deletions,changedFiles",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {
            "content_included": False,
            "ok": False,
            "error": (proc.stderr or proc.stdout or "gh failed").strip()[:300],
            "repo": repo,
            "search": search,
        }
    try:
        rows = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {
            "content_included": False,
            "ok": False,
            "error": f"json_decode: {exc}",
            "repo": repo,
            "search": search,
        }

    latencies: list[float] = []
    samples: list[dict[str, Any]] = []
    for row in rows:
        created = _parse_ts(row.get("createdAt"))
        merged = _parse_ts(row.get("mergedAt"))
        if not created or not merged:
            continue
        seconds = (merged - created).total_seconds()
        if seconds < 0:
            continue
        latencies.append(seconds)
        samples.append(
            {
                "number": row.get("number"),
                "open_to_merge_seconds": round(seconds, 1),
                "changed_files": row.get("changedFiles"),
                # sizes only — no title/body content
            }
        )

    summary: dict[str, Any] = {
        "content_included": False,
        "ok": True,
        "repo": repo,
        "search": search,
        "n": len(latencies),
        "open_to_merge_seconds": {},
        "samples": samples[: limit],
    }
    if latencies:
        summary["open_to_merge_seconds"] = {
            "n": len(latencies),
            "avg": round(sum(latencies) / len(latencies), 1),
            "min": round(min(latencies), 1),
            "max": round(max(latencies), 1),
        }
    return summary
