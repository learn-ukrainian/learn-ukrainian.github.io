#!/usr/bin/env python3
"""Calibrate composer-2.5 (via Cursor Agent CLI) as a Russianism judge.

Sibling of ``scripts/audit/opencode_judge_calibration.py``. Difference:
routes through the ``cursor-agent -p`` / ``agent -p`` headless CLI instead
of ``opencode run``. Cursor exposes the in-house Composer 2.5 model + the
hosted Anthropic / OpenAI / xAI models behind one subscription, currently
under a 10x usage promotion (effectively free for batches this size).

User direction 2026-05-23: "i wnat to use and test composer 2.5 there ,
atm they are runnin 10x usage promotion".

Usage:
    .venv/bin/python scripts/audit/cursor_judge_calibration.py
    .venv/bin/python scripts/audit/cursor_judge_calibration.py --dry-run
    .venv/bin/python scripts/audit/cursor_judge_calibration.py --model composer-2.5-fast
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

CURSOR_BIN = "agent"  # symlinked to ~/.local/bin/agent and ~/.local/bin/cursor-agent
REQUEST_TIMEOUT_S = 600

OUT_DIR = PROJECT_ROOT / "audit" / "2026-05-23-composer-2.5-cursor-judge-calibration"


def call_cursor(prompt: str, model: str) -> dict:
    """Invoke composer-2.5 (or any cursor model) via ``agent -p`` headless mode.

    Cursor's text output is typically just the assistant reply (no event
    framing required), so we feed stdout to ``parse_json_verdict`` directly.

    --trust required because the CLI refuses non-interactive runs without
    workspace trust acknowledgement otherwise. We pass it because the judge
    prompt does NOT instruct the model to read or write any files.
    """
    t0 = time.time()
    try:
        proc = subprocess.run(
            [
                CURSOR_BIN,
                "-p",
                prompt,
                "--model",
                model,
                "--output-format",
                "text",
                "--trust",
            ],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT_S,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except FileNotFoundError:
        return {
            "verdict": "judge_error",
            "error": f"`{CURSOR_BIN}` not on PATH. Install via `curl https://cursor.com/install -fsS | bash`.",
            "duration_s": time.time() - t0,
        }
    except subprocess.TimeoutExpired:
        return {
            "verdict": "judge_error",
            "error": f"cursor-agent timed out after {REQUEST_TIMEOUT_S}s",
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
        default="composer-2.5",
        help="Cursor model id (default: composer-2.5). Also try composer-2.5-fast.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan + skip API calls")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help=f"Output directory (default: {OUT_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit to first N cases (smoke test). Default: all 12.",
    )
    args = parser.parse_args()

    cases = pull_calibration_cases()
    print(f"Loaded {len(cases)} calibration cases from working tree:{CALIBRATION_BLOB}")
    if args.limit:
        cases = cases[: args.limit]
        print(f"Limited to first {len(cases)} cases (smoke)")

    if args.dry_run:
        print(f"Would subprocess `{CURSOR_BIN} -p PROMPT --model {args.model} ...` per case")
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
            verdict = call_cursor(prompt, args.model)
            score = score_case(verdict, case["gold"])
            scores.append(score)
            row = judgment_row_from_case(case=case, model=args.model, verdict=verdict, score=score)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
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
        "via": "cursor-agent",
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
