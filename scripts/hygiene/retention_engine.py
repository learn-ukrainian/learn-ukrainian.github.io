#!/usr/bin/env python3
"""Sol PR-L: safe retention plan/apply engine (dry-run default).

Builds a content-addressed retention plan from the existing worktree reaper
and lane disk scanner, then applies only when the re-computed plan digest
still matches. Active sessions, dirty/ahead/untracked worktrees, and leased
paths never become apply candidates.

Usage::

    .venv/bin/python scripts/hygiene/retention_engine.py plan
    .venv/bin/python scripts/hygiene/retention_engine.py apply --plan path.json
    .venv/bin/python scripts/hygiene/retention_engine.py latest

Apply never enables itself via launchd by default — Gate 5 requires explicit
operator approval after seven days of dry-run evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_DIR = REPO_ROOT / "batch_state" / "fleet-comms" / "retention"
DEFAULT_ARCHIVE_ROOT = Path.home() / "Library" / "Application Support" / "learn-ukrainian" / "retention-archives"

# Ensure repo scripts/ is importable when invoked as a file path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hygiene.lane_disk_retention import (
    scan_dispatch_worktrees,
    scan_home_session_hints,
)
from scripts.orchestration.reap_worktrees import (
    ReapResult,
    primary_checkout_root,
    reap_worktrees,
    resolve_repo_root,
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_ERROR = 3
EXIT_DIGEST_MISMATCH = 4


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def plan_digest(plan_body: dict[str, Any]) -> str:
    """SHA-256 over the plan body excluding volatile envelope fields."""
    body = {
        k: v
        for k, v in plan_body.items()
        if k not in {"created_at", "digest", "plan_path", "receipt"}
    }
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _reap_result_dict(result: ReapResult) -> dict[str, Any]:
    return {
        "path": result.path,
        "branch": result.branch,
        "action": result.action,
        "reason": result.reason,
        "dirty": result.dirty,
        "pr": result.pr,
        "error": result.error,
    }


def build_plan(
    *,
    repo_root: Path,
    archive_root: Path,
    stale_hours: float = 72.0,
    build_age_hours: float = 6.0,
    include_home: bool = False,
    safe_only: bool = True,
) -> dict[str, Any]:
    """Assemble a dry retention plan (zero mutations)."""
    repo_root = repo_root.resolve()
    primary = primary_checkout_root(repo_root)

    # Reaper dry-run (apply=False): classifies would_remove vs skipped.
    reaper_results = reap_worktrees(
        repo_root=primary,
        apply=False,
        build_age_hours=build_age_hours,
        preserve_then_reap=False,
        prune_merged_branches=False,
        safe_only=safe_only,
    )
    would_reap = [
        _reap_result_dict(r)
        for r in reaper_results
        if r.action in {"would_remove", "would_preserve_then_remove"}
    ]
    preserved = [
        _reap_result_dict(r)
        for r in reaper_results
        if r.action == "skipped"
        and any(
            token in (r.reason or "").lower()
            for token in ("dirty", "ahead", "lease", "active", "untracked")
        )
    ]

    scanner = scan_dispatch_worktrees(repo_root=primary, stale_hours=stale_hours)
    home = scan_home_session_hints() if include_home else []

    candidates = {
        "worktree_reap": would_reap,
        "worktree_preserved": preserved,
        "scanner_stale": [asdict(w) for w in scanner if w.recommendation != "ok"],
        "home_sessions": home,
    }
    plan: dict[str, Any] = {
        "schema": "fleet-comms.retention.plan.v1",
        "mode": "dry-run",
        "created_at": _utc_now(),
        "repo_root": str(primary),
        "archive_root": str(archive_root.expanduser()),
        "policy": {
            "stale_hours": stale_hours,
            "build_age_hours": build_age_hours,
            "safe_only": safe_only,
            "include_home": include_home,
            "session_stream_history_excluded": True,
            "apply_requires_matching_digest": True,
            "scheduled_apply_default": False,
        },
        "candidates": candidates,
        "counts": {
            "would_reap": len(would_reap),
            "preserved": len(preserved),
            "scanner_stale": len(candidates["scanner_stale"]),
            "home_sessions": len(home),
        },
        "mutations": 0,
    }
    plan["digest"] = plan_digest(plan)
    return plan


def write_plan(plan: dict[str, Any], plan_dir: Path) -> Path:
    plan_dir.mkdir(parents=True, exist_ok=True)
    stamp = plan["created_at"].replace(":", "").replace("-", "")
    path = plan_dir / f"plan-{stamp}-{plan['digest'][:12]}.json"
    latest = plan_dir / "latest.json"
    text = json.dumps(plan, indent=2, sort_keys=True, default=str) + "\n"
    path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    plan["plan_path"] = str(path)
    return path


def load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("plan must be a JSON object")
    if payload.get("schema") != "fleet-comms.retention.plan.v1":
        raise ValueError(f"unsupported plan schema: {payload.get('schema')!r}")
    if not payload.get("digest"):
        raise ValueError("plan missing digest")
    return payload


def apply_plan(
    plan: dict[str, Any],
    *,
    repo_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply a previously written plan only if its digest still matches.

    Only worktree reaps go through the existing safe reaper. Session archives
    and home-session deletion are never auto-applied here (operator Gate 5).
    """
    expected = str(plan.get("digest") or "")
    if not expected:
        raise ValueError("plan missing digest")

    root = Path(repo_root or plan.get("repo_root") or REPO_ROOT).resolve()
    policy = plan.get("policy") or {}
    fresh = build_plan(
        repo_root=root,
        archive_root=Path(plan.get("archive_root") or DEFAULT_ARCHIVE_ROOT),
        stale_hours=float(policy.get("stale_hours", 72.0)),
        build_age_hours=float(policy.get("build_age_hours", 6.0)),
        include_home=bool(policy.get("include_home", False)),
        safe_only=bool(policy.get("safe_only", True)),
    )
    actual = fresh["digest"]
    if actual != expected:
        return {
            "ok": False,
            "error": "plan_digest_mismatch",
            "expected_digest": expected,
            "actual_digest": actual,
            "mutations": 0,
            "results": [],
        }

    target_paths = [
        Path(row["path"])
        for row in (plan.get("candidates") or {}).get("worktree_reap") or []
        if row.get("path")
    ]
    if dry_run or not target_paths:
        return {
            "ok": True,
            "mode": "dry-run" if dry_run or not target_paths else "apply",
            "digest": expected,
            "mutations": 0,
            "results": [],
            "note": "no worktree candidates" if not target_paths else "dry-run only",
        }

    results = reap_worktrees(
        repo_root=primary_checkout_root(root),
        apply=True,
        build_age_hours=float(policy.get("build_age_hours", 6.0)),
        preserve_then_reap=False,
        prune_merged_branches=False,
        target_paths=target_paths,
        safe_only=bool(policy.get("safe_only", True)),
    )
    applied = [_reap_result_dict(r) for r in results]
    mutations = sum(
        1
        for r in results
        if r.action in {"removed", "preserved_then_removed"}
    )
    receipt = {
        "ok": True,
        "mode": "apply",
        "digest": expected,
        "applied_at": _utc_now(),
        "mutations": mutations,
        "results": applied,
    }
    return receipt


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        root = resolve_repo_root(Path(args.repo_root).resolve() if args.repo_root else None)
    except RuntimeError:
        root = Path(args.repo_root or REPO_ROOT).resolve()
    plan = build_plan(
        repo_root=root,
        archive_root=Path(args.archive_root),
        stale_hours=args.stale_hours,
        build_age_hours=args.build_age_hours,
        include_home=args.include_home,
        safe_only=not args.unsafe,
    )
    path = write_plan(plan, Path(args.plan_dir))
    out = {**plan, "plan_path": str(path)}
    sys.stdout.write(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
    return EXIT_OK


def cmd_apply(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    try:
        plan = load_plan(plan_path)
        receipt = apply_plan(plan, dry_run=args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"failed to apply plan: {exc}\n")
        return EXIT_ERROR
    # Persist receipt next to plan
    receipt_path = plan_path.with_suffix(".receipt.json")
    if receipt.get("ok"):
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        receipt["receipt_path"] = str(receipt_path)
    sys.stdout.write(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
    if receipt.get("error") == "plan_digest_mismatch":
        return EXIT_DIGEST_MISMATCH
    return EXIT_OK if receipt.get("ok") else EXIT_ERROR


def cmd_latest(args: argparse.Namespace) -> int:
    latest = Path(args.plan_dir) / "latest.json"
    if not latest.is_file():
        sys.stdout.write(
            json.dumps(
                {
                    "schema": "fleet-comms.retention.plan.v1",
                    "missing": True,
                    "plan_dir": str(Path(args.plan_dir)),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return EXIT_OK
    sys.stdout.write(latest.read_text(encoding="utf-8"))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Write a dry retention plan + digest")
    plan.add_argument("--repo-root", default=None)
    plan.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    plan.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    plan.add_argument("--stale-hours", type=float, default=72.0)
    plan.add_argument("--build-age-hours", type=float, default=6.0)
    plan.add_argument("--include-home", action="store_true")
    plan.add_argument(
        "--unsafe",
        action="store_true",
        help="Allow reaper non-safe_only classification (still dry-run on plan)",
    )
    plan.set_defaults(func=cmd_plan)

    apply_p = sub.add_parser(
        "apply",
        help="Apply a plan only if digest still matches (worktree reaper only)",
    )
    apply_p.add_argument("--plan", type=Path, required=True, help="Path to plan JSON")
    apply_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Re-validate digest without mutating (default when no candidates)",
    )
    apply_p.set_defaults(func=cmd_apply)

    latest = sub.add_parser("latest", help="Print latest plan JSON if present")
    latest.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    latest.set_defaults(func=cmd_latest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
