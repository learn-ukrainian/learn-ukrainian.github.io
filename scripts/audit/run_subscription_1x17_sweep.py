#!/usr/bin/env python3
"""Serial subscription-runtime 1×17 QG bakeoff sweep (#4761 / #4762 / #4763).

Python-only — no bash. Examples:
  QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_subscription_1x17_sweep.py --model claude-opus-4-8
  QG_BAKEOFF=1 .venv/bin/python scripts/audit/run_subscription_1x17_sweep.py --model gpt-5.5

Claude and GPT can run in parallel (separate out dirs, separate subscription buckets).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = REPO / ".venv" / "bin" / "python"

ALL_FIXTURES = [
    "vesnianky",
    "koliadky",
    "khreshchennia-rusi",
    "skovoroda-hryhorii",
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

MODEL_OUT_DIRS = {
    "claude-opus-4-8": REPO / "audit" / "2026-07-08-claude-multirun-1x",
    "gpt-5.5": REPO / "audit" / "2026-07-08-gpt-multirun-1x",
}


def _pin_slug(pin: str) -> str:
    normalized = unicodedata.normalize("NFKD", pin).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "model"


def _log(out: Path, msg: str) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_path = out / "_sweep.log"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _artifact_path(out: Path, model: str, slug: str, arm: str) -> Path | None:
    pin = _pin_slug(model)
    for path in out.glob(f"{pin}__{slug}*.json"):
        if "SCORECARD" in path.name:
            continue
        is_bare = "__bare__" in path.name
        if arm == "bare" and is_bare:
            return path
        if arm == "tooled" and not is_bare:
            return path
    return None


def _record(out: Path, model: str, slug: str, arm: str) -> None:
    path = _artifact_path(out, model, slug, arm)
    if path is None:
        _log(out, f"WARN no artifact for {slug}/{arm}")
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
    results = out / "RESULTS.tsv"
    if not results.exists():
        results.write_text(
            "fixture\tarm\tstatus\tmodel_judgment\tlive_admissible\t"
            "invalid_fact_checks\ttool_call_count\twall_seconds\t"
            "raw_response_nonnull\ttoolcap_error\n",
            encoding="utf-8",
        )
    with results.open("a", encoding="utf-8") as fh:
        fh.write(row)
    _log(out, f"recorded {slug}/{arm} status={j.get('status')}")


def _run_cell(out: Path, model: str, slug: str, arm: str) -> int:
    if _artifact_path(out, model, slug, arm) is not None:
        _log(out, f"skip {slug}/{arm} (artifact exists)")
        return 0
    _log(out, f"run {slug}/{arm}")
    proc = subprocess.run(
        [
            str(PY),
            "-m",
            "scripts.audit.qg_bakeoff",
            "--models",
            model,
            "--arm",
            arm,
            "--fixture",
            slug,
            "--out-dir",
            str(out),
        ],
        cwd=str(REPO),
        env={**os.environ, "QG_BAKEOFF": "1"},
        check=False,
    )
    _record(out, model, slug, arm)
    pause = 90 if arm == "tooled" else 60
    _log(out, f"pause {pause}s after {slug}/{arm}")
    time.sleep(pause)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        required=True,
        choices=sorted(MODEL_OUT_DIRS),
        help="Subscription-runtime model pin",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output directory (default: model-specific audit dir)",
    )
    args = parser.parse_args(argv)

    if os.environ.get("QG_BAKEOFF") != "1":
        print("ERROR: export QG_BAKEOFF=1 before running", file=sys.stderr)
        return 2
    if not PY.is_file():
        print(f"ERROR: venv python not found at {PY}", file=sys.stderr)
        return 2

    out = args.out_dir or MODEL_OUT_DIRS[args.model]
    out.mkdir(parents=True, exist_ok=True)
    _log(out, f"start model={args.model} out={out}")

    errors = 0
    consecutive_errors = 0
    for arm in ("tooled", "bare"):
        for slug in ALL_FIXTURES:
            rc = _run_cell(out, args.model, slug, arm)
            if rc != 0:
                errors += 1
                consecutive_errors += 1
            else:
                consecutive_errors = 0
            if consecutive_errors > 2:
                _log(out, "HARD STOP: more than 2 consecutive cell failures")
                return 1
    _log(out, f"DONE errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
