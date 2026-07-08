#!/usr/bin/env python3
"""Serial Gemini 1×17 QG bakeoff sweep driver (#4761).

Python-only — no bash. Run:
  QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_gemini_1x17_sweep.py

Resumes from partial work in audit/2026-07-08-gemini-strict-probe/ (8 cells done).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = REPO / ".venv" / "bin" / "python"
OUT = REPO / "audit" / "2026-07-08-gemini-multirun-1x"
PROBE = REPO / "audit" / "2026-07-08-gemini-strict-probe"
MODEL = "gemini-3.1-pro-high"

DONE_FIXTURES = frozenset(
    {"vesnianky", "koliadky", "khreshchennia-rusi", "skovoroda-hryhorii"}
)
REMAINING_FIXTURES = [
    "ahatanhel-krymskyi",
    "andriivski-vechornytsi",
    "franko-ivan",
    "holosinnia",
    "khmelnytskyi-1648",
    "kupalski",
    "lesya-ukrainka",
    "rusalii",
    "rusalka-dnistrova",
    "vesilnyi-obriad",
    "yaroslav-sofiya",
    "zaporozka-sich",
    "zhnyvarski",
]


def _log(msg: str) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_path = OUT / "_sweep.log"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _throttle_quota() -> tuple[float, float]:
    proc = subprocess.run(
        ["codexbar", "usage", "--provider", "antigravity", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    data = json.loads(proc.stdout)

    def find(o: object) -> dict | None:
        if isinstance(o, dict):
            if o.get("id") == "antigravity-quota-summary-gemini-5h":
                return o
            for v in o.values():
                r = find(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = find(v)
                if r:
                    return r
        return None

    node = find(data)
    if not node:
        raise RuntimeError("antigravity-quota-summary-gemini-5h not found in codexbar output")
    window = node["window"]
    reset = datetime.fromisoformat(window["resetsAt"].replace("Z", "+00:00"))
    mins = (reset - datetime.now(UTC)).total_seconds() / 60
    return float(window["usedPercent"]), mins


def _throttle_wait(cell: str) -> None:
    throttle_log = OUT / "THROTTLE.md"
    if not throttle_log.exists():
        throttle_log.write_text("# Throttle log\n\n", encoding="utf-8")
    while True:
        used, mins = _throttle_quota()
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        if used < 70 and mins >= 45:
            with throttle_log.open("a", encoding="utf-8") as fh:
                fh.write(f"| {ts} | {cell} | used_pct={used:.2f} reset_min={mins:.1f} | HEALTHY |\n")
            _log(f"throttle {cell}: HEALTHY used={used:.1f}% reset_min={mins:.1f}")
            return
        wait_s = max(60, int((mins + 5) * 60)) if mins < 45 else 600
        with throttle_log.open("a", encoding="utf-8") as fh:
            fh.write(
                f"| {ts} | {cell} | used_pct={used:.2f} reset_min={mins:.1f} | WAIT {wait_s}s |\n"
            )
        _log(f"throttle {cell}: WAIT {wait_s}s (used={used:.1f}% reset_min={mins:.1f})")
        time.sleep(wait_s)


def _seed_out_dir() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not PROBE.is_dir():
        return
    for src in PROBE.glob("gemini-3-1-pro-high__*.json"):
        dst = OUT / src.name
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
    for name in ("RESULTS.tsv", "THROTTLE.md"):
        src = PROBE / name
        if src.exists() and not (OUT / name).exists():
            (OUT / name).write_bytes(src.read_bytes())
    _log(f"seeded {len(list(OUT.glob('gemini*.json')))} artifacts into {OUT}")


def _artifact_path(slug: str, arm: str) -> Path | None:
    pin = MODEL.replace(".", "-")
    for path in OUT.glob(f"{pin}__{slug}*.json"):
        if "SCORECARD" in path.name:
            continue
        is_bare = "__bare__" in path.name
        if arm == "bare" and is_bare:
            return path
        if arm == "tooled" and not is_bare:
            return path
    return None


def _record(slug: str, arm: str) -> None:
    path = _artifact_path(slug, arm)
    if path is None:
        _log(f"WARN no artifact for {slug}/{arm}")
        return
    j = json.loads(path.read_text(encoding="utf-8"))
    sc = j.get("score") or {}
    blob = json.dumps(j)
    toolcap = "hard cap is 40" in blob or "used 46 tools" in blob
    row = (
        f"{slug}\t{arm}\t{j.get('status')}\t{sc.get('model_judgment_score')}\t"
        f"{sc.get('live_admissible_score')}\t{sc.get('invalid_fact_checks')}\t"
        f"{j.get('tool_call_count')}\t{j.get('wall_seconds')}\t"
        f"{j.get('raw_response') is not None}\t{toolcap}\n"
    )
    results = OUT / "RESULTS.tsv"
    if not results.exists():
        results.write_text(
            "fixture\tarm\tstatus\tmodel_judgment\tlive_admissible\t"
            "invalid_fact_checks\ttool_call_count\twall_seconds\t"
            "raw_response_nonnull\ttoolcap_error\n",
            encoding="utf-8",
        )
    with results.open("a", encoding="utf-8") as fh:
        fh.write(row)
    _log(f"recorded {slug}/{arm} status={j.get('status')}")


def _run_cell(slug: str, arm: str) -> int:
    if slug in DONE_FIXTURES:
        _log(f"skip {slug}/{arm} (seeded from partial run)")
        return 0
    if _artifact_path(slug, arm) is not None:
        _log(f"skip {slug}/{arm} (artifact exists)")
        return 0
    _throttle_wait(f"{slug}/{arm}")
    _log(f"run {slug}/{arm}")
    proc = subprocess.run(
        [
            str(PY),
            "-m",
            "scripts.audit.qg_bakeoff",
            "--models",
            MODEL,
            "--arm",
            arm,
            "--fixture",
            slug,
            "--out-dir",
            str(OUT),
        ],
        cwd=str(REPO),
        env={**os.environ, "QG_BAKEOFF": "1"},
        check=False,
    )
    _record(slug, arm)
    pause = 90 if arm == "tooled" else 60
    _log(f"pause {pause}s after {slug}/{arm}")
    time.sleep(pause)
    return proc.returncode


def main() -> int:
    if os.environ.get("QG_BAKEOFF") != "1":
        print("ERROR: export QG_BAKEOFF=1 before running", file=sys.stderr)
        return 2
    if not PY.is_file():
        print(f"ERROR: venv python not found at {PY}", file=sys.stderr)
        return 2
    _seed_out_dir()
    errors = 0
    consecutive_errors = 0
    for arm in ("tooled", "bare"):
        for slug in REMAINING_FIXTURES:
            rc = _run_cell(slug, arm)
            if rc != 0:
                errors += 1
                consecutive_errors += 1
            else:
                consecutive_errors = 0
            if consecutive_errors > 2:
                _log("HARD STOP: more than 2 consecutive cell failures")
                return 1
    _log(f"DONE errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
