#!/usr/bin/env python3
"""Calibrate Qwen 3.6 (via Hermes + OpenRouter) as a Russianism judge.

Standalone test harness — does NOT depend on PR #2006 being merged.

Pulls the calibration cases + prompt builder logic from PR #2006's branch
(``origin/pr-2006``) without committing them to main, then runs Qwen 3.6
through the same 12-case Antonenko-grounded gold set used to rank
``claude-opus-4-7`` / ``gemini-3.1-pro-preview`` / ``gpt-5.5`` /
``grok-4.3`` in the 2026-05-15 / 2026-05-17 calibration studies.

Auth: Qwen routes through OpenRouter; the OpenRouter provider is
configured in ``~/.hermes/config.yaml`` (set 2026-05-18 by the user when
the OpenRouter API key was added). No xai-oauth-style explicit token
read is required — Hermes resolves the OpenRouter key itself. This
harness only invokes the ``hermes -z PROMPT -m MODEL`` subprocess.

Output:
    audit/2026-05-19-qwen-3.6-judge-calibration/
        judgments.jsonl       one row per case (verdict + raw + duration)
        REPORT.md             F1 / P / R + per-case breakdown
        leaderboard-row.json  one row ready to drop into the judge table

Usage:
    .venv/bin/python scripts/audit/qwen_judge_calibration.py
    .venv/bin/python scripts/audit/qwen_judge_calibration.py --dry-run
    .venv/bin/python scripts/audit/qwen_judge_calibration.py --model qwen/qwen3.6-flash
    .venv/bin/python scripts/audit/qwen_judge_calibration.py --model qwen/qwen3.6-max-preview

Refs: PR #2006 (russianism_judge harness), `scripts/audit/grok_judge_calibration.py`
(parent pattern), 2026-05-19 user direction "Fire Russianism judge probe NOW"
(closes the first qwen empirical signal request on matrix §8.10 #2).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    from _judge_eval_lib import (
        CALIBRATION_BLOB,
        PR_2006_REF,
        PROJECT_ROOT,
        aggregate,
        build_judge_prompt,
        judgment_row_from_case,
        parse_json_verdict,
        pull_calibration_cases,
        render_grok_report,
        retrieve_antonenko,
        score_case,
    )
except ModuleNotFoundError:
    from scripts.audit._judge_eval_lib import (
        CALIBRATION_BLOB,
        PR_2006_REF,
        PROJECT_ROOT,
        aggregate,
        build_judge_prompt,
        judgment_row_from_case,
        parse_json_verdict,
        pull_calibration_cases,
        render_grok_report,
        retrieve_antonenko,
        score_case,
    )

# Hermes CLI invokes Qwen 3.6 via the configured OpenRouter provider.
# Unlike the Grok harness, we do not pre-flight an explicit OAuth token
# read — Hermes resolves the OpenRouter API key from its own
# ~/.hermes/config.yaml at invocation time and a missing key surfaces
# as a non-zero exit on the first call (which we capture as
# judge_error).
HERMES_BIN = "hermes"

# Per-case timeout. Qwen reasoning + tool-set instantiation can take
# 60-120s on first MCP-aware call. Mirror the Grok harness's 480s
# ceiling so slow calls don't get spuriously killed.
REQUEST_TIMEOUT_S = 480

OUT_DIR = PROJECT_ROOT / "audit" / "2026-05-19-qwen-3.6-judge-calibration"


def call_qwen(prompt: str, model: str) -> dict:
    """Invoke Qwen 3.6 through the Hermes CLI's one-shot mode.

    Returns a dict with at minimum a ``verdict`` key. On subprocess or
    parse error, ``verdict`` is ``"judge_error"`` or
    ``"json_parse_error"`` and ``raw`` carries the first 500 chars for
    inspection.

    Auth: Hermes resolves the OpenRouter API key from
    ``~/.hermes/config.yaml`` automatically; we don't touch the key
    directly.
    """
    t0 = time.time()
    try:
        proc = subprocess.run(
            [HERMES_BIN, "-z", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT_S,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except FileNotFoundError:
        return {
            "verdict": "judge_error",
            "error": f"`{HERMES_BIN}` not on PATH. Install via the Hermes setup wizard.",
            "duration_s": time.time() - t0,
        }
    except subprocess.TimeoutExpired:
        return {
            "verdict": "judge_error",
            "error": f"hermes -z timed out after {REQUEST_TIMEOUT_S}s",
            "duration_s": time.time() - t0,
        }
    duration = time.time() - t0

    if proc.returncode != 0:
        return {
            "verdict": "judge_error",
            "returncode": proc.returncode,
            "stdout": proc.stdout[:500],
            "stderr": proc.stderr[:500],
            "duration_s": duration,
        }

    return parse_json_verdict(proc.stdout, duration_s=duration)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--model",
        default="qwen/qwen3.6-plus",
        help=(
            "OpenRouter model id (default: qwen/qwen3.6-plus). "
            "Try qwen/qwen3.6-flash for the budget probe or "
            "qwen/qwen3.6-max-preview for the top-tier probe."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan + skip API calls")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help=f"Output directory (default: {OUT_DIR})",
    )
    args = parser.parse_args()

    cases = pull_calibration_cases()
    print(f"Loaded {len(cases)} calibration cases from {PR_2006_REF}:{CALIBRATION_BLOB}")

    if args.dry_run:
        print(f"Would subprocess `{HERMES_BIN} -z PROMPT -m {args.model}` for each case")
        print(f"Would write artifacts to {args.out_dir}")
        for c in cases:
            print(f"  - {c['prompt_id']}  (expected_clean={c['gold']['expected_clean']})")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    judgments_path = args.out_dir / "judgments.jsonl"
    report_path = args.out_dir / "REPORT.md"
    leaderboard_path = args.out_dir / "leaderboard-row.json"

    scores: list[dict] = []
    with judgments_path.open("w", encoding="utf-8") as fh:
        for idx, case in enumerate(cases, 1):
            target = case["output_text"]
            antonenko = retrieve_antonenko(target)
            prompt = build_judge_prompt(target, antonenko)
            print(
                f"[{idx}/{len(cases)}] {case['prompt_id']}  (antonenko={len(antonenko)}) ",
                end="",
                flush=True,
            )
            verdict = call_qwen(prompt, args.model)
            score = score_case(verdict, case["gold"])
            scores.append(score)
            row = judgment_row_from_case(case=case, model=args.model, verdict=verdict, score=score)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            tag = "PASS" if score["case_acc"] else "FAIL"
            print(f"{tag} verdict={verdict.get('verdict')} dur={row['duration_s']}s")

    agg = aggregate(scores)
    print("")
    print(f"Aggregate over {agg['n']} cases:")
    print(f"  case_accuracy: {agg['case_accuracy']*100:.1f}%")
    print(f"  precision:     {agg['precision']*100:.1f}%")
    print(f"  recall:        {agg['recall']*100:.1f}%")
    print(f"  F1:            {agg['f1']*100:.1f}%")

    leaderboard_row = {
        "judge": args.model,
        "via": "hermes-openrouter",
        "n": agg["n"],
        "f1": agg["f1"],
        "precision": agg["precision"],
        "recall": agg["recall"],
        "case_accuracy": agg["case_accuracy"],
        "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    leaderboard_path.write_text(
        json.dumps(leaderboard_row, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report_path.write_text(
        render_grok_report(model=args.model, agg=agg, judgments_path=judgments_path),
        encoding="utf-8",
    )

    print("")
    print(f"Wrote {judgments_path}")
    print(f"Wrote {report_path}")
    print(f"Wrote {leaderboard_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
