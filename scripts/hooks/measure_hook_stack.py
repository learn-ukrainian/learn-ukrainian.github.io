#!/usr/bin/env python3
"""Measure shared harness hook wall times and emit a JSON report.

Used for the hook audit (operator 2026-08-06). Safe: empty/`{}` payloads only;
hooks are invoked with CLAUDE_PROJECT_DIR set; no network required for local guards.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _python_bin() -> str:
    """Prefer this checkout's venv; walk parents for layout-A worktrees."""
    for parent in [ROOT, *ROOT.parents]:
        cand = parent / ".venv" / "bin" / "python"
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    return sys.executable


PYTHON = _python_bin()

# (name, argv, stdin_bytes|None, env_extra)
STACK: list[tuple[str, list[str], bytes | None, dict[str, str]]] = [
    (
        "session-setup.sh",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/session-setup.sh")],
        None,
        {},
    ),
    (
        "post-compact.sh",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/post-compact.sh")],
        b"{}",
        {},
    ),
    (
        "post-compact.sh+GROK_SESSION",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/post-compact.sh")],
        b"{}",
        {"SESSION_HANDOFF_AGENT": "grok", "GROK_AGENT": "1"},
    ),
    (
        "enforce-venv.sh",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/enforce-venv.sh")],
        b"{}",
        {},
    ),
    (
        "heal-core-bare.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/heal-core-bare.py")],
        None,
        {},
    ),
    (
        "guard-primary-checkout-write.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/guard-primary-checkout-write.py")],
        b"{}",
        {},
    ),
    (
        "guard-pr-merge.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/guard-pr-merge.py")],
        b"{}",
        {},
    ),
    (
        "guard-secret-print.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/guard-secret-print.py")],
        b"{}",
        {},
    ),
    (
        "guard-branch-switch-in-main.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/guard-branch-switch-in-main.py")],
        b"{}",
        {},
    ),
    (
        "guard-admin-merge.py",
        [PYTHON, str(ROOT / "agents_extensions/shared/hooks/guard-admin-merge.py")],
        b"{}",
        {},
    ),
    (
        "context-monitor.sh",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/context-monitor.sh")],
        b'{"session_id":"","transcript_path":""}',
        {},
    ),
    (
        "context-monitor.sh+GROK_AGENT",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/context-monitor.sh")],
        b'{"session_id":"x","transcript_path":"/nonexistent"}',
        {"GROK_AGENT": "1", "SESSION_HANDOFF_AGENT": "grok"},
    ),
    (
        "tool-timing.sh",
        ["bash", str(ROOT / "agents_extensions/shared/hooks/tool-timing.sh")],
        b'{"tool_name":"Bash","duration_ms":1,"hook_event_name":"PostToolUse"}',
        {},
    ),
    (
        "codex_hook_entry pre-tool-use",
        ["bash", str(ROOT / "scripts/agent_runtime/codex_hook_entry.sh"), "pre-tool-use"],
        b"{}",
        {},
    ),
]


def _time_one(
    name: str,
    argv: list[str],
    stdin: bytes | None,
    env_extra: dict[str, str],
    *,
    repeats: int,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(ROOT)
    env.update(env_extra)
    samples: list[float] = []
    last_rc = 0
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter()
        proc = subprocess.run(argv, input=stdin, capture_output=True, env=env, cwd=ROOT)
        samples.append((time.perf_counter() - t0) * 1000.0)
        last_rc = int(proc.returncode)
    return {
        "name": name,
        "ms_median": round(statistics.median(samples), 2),
        "ms_mean": round(statistics.fmean(samples), 2),
        "ms_min": round(min(samples), 2),
        "ms_max": round(max(samples), 2),
        "samples": [round(s, 2) for s in samples],
        "rc": last_rc,
        "argv0": argv[0],
    }


def estimate_bash_pretool_tax(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum of typical PreToolUse Bash guards (Claude settings stack)."""
    names = {
        "enforce-venv.sh",
        "heal-core-bare.py",
        "guard-branch-switch-in-main.py",
        "guard-admin-merge.py",
        "guard-pr-merge.py",
        "guard-secret-print.py",
        "guard-primary-checkout-write.py",
    }
    by_name = {r["name"]: r for r in rows}
    parts = []
    total = 0.0
    for n in sorted(names):
        if n in by_name:
            parts.append({"name": n, "ms_median": by_name[n]["ms_median"]})
            total += float(by_name[n]["ms_median"])
    return {"components": parts, "ms_median_sum": round(total, 2)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3, help="Samples per hook (default 3)")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "batch_state" / "hook-audit-measure.json",
        help="Write JSON report here",
    )
    parser.add_argument("--json-stdout", action="store_true")
    args = parser.parse_args(argv)

    rows = [
        _time_one(name, argv, stdin, env_extra, repeats=args.repeats)
        for name, argv, stdin, env_extra in STACK
    ]
    bash_tax = estimate_bash_pretool_tax(rows)
    report = {
        "schema": "hook-stack-measure.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": str(ROOT),
        "repeats": args.repeats,
        "hooks": rows,
        "estimates": {
            "claude_bash_pretool_median_sum_ms": bash_tax["ms_median_sum"],
            "claude_bash_pretool_components": bash_tax["components"],
            "session_start_median_ms": next(
                (r["ms_median"] for r in rows if r["name"] == "session-setup.sh"), None
            ),
            "post_compact_median_ms": next(
                (r["ms_median"] for r in rows if r["name"] == "post-compact.sh"), None
            ),
            "post_compact_grok_median_ms": next(
                (r["ms_median"] for r in rows if r["name"] == "post-compact.sh+GROK_SESSION"),
                None,
            ),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json_stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.out}")
        print(
            f"session-setup median={report['estimates']['session_start_median_ms']} ms  "
            f"post-compact={report['estimates']['post_compact_median_ms']} ms  "
            f"post-compact+grok={report['estimates']['post_compact_grok_median_ms']} ms  "
            f"bash_pretool_sum={report['estimates']['claude_bash_pretool_median_sum_ms']} ms"
        )
        for r in sorted(rows, key=lambda x: -x["ms_median"])[:8]:
            print(f"  {r['ms_median']:8.1f} ms  {r['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
