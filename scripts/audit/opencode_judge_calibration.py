#!/usr/bin/env python3
"""Calibrate qwen3.7-max (via opencode + OpenRouter) as a Russianism judge.

Sibling of ``scripts/audit/qwen_judge_calibration.py``. Difference: routes
through the ``opencode run`` CLI instead of ``hermes -z``, so the judge runs
inside opencode's coder-agent runtime. This is the **deployment-realistic**
shape for qwen3.7-max as a 2nd-judge candidate (PR-D1 wired the bridge
via ``ab ask-opencode`` 2026-05-23, default model ``openrouter/qwen/qwen3.7-max``).

Confound vs hermes route: opencode injects a substantial coder-agent system
prompt (~13K tokens measured on smoke). For apples-to-apples comparison
against the 2026-05-15 leaderboard (which used near-empty system context)
prefer the hermes route. For "how does qwen3.7-max behave as a judge IF we
wire it into the V7 pipeline via opencode" prefer this route.

User direction 2026-05-23: "you should use qwen3.7-max with opencode
against openrouter".

Usage:
    .venv/bin/python scripts/audit/opencode_judge_calibration.py
    .venv/bin/python scripts/audit/opencode_judge_calibration.py --dry-run
    .venv/bin/python scripts/audit/opencode_judge_calibration.py --model openrouter/qwen/qwen3.7-max
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

OPENCODE_BIN = "opencode"
REQUEST_TIMEOUT_S = 600  # opencode startup + reasoning overhead

OUT_DIR = PROJECT_ROOT / "audit" / "2026-05-23-qwen3.7-max-opencode-judge-calibration"


def call_opencode(prompt: str, model: str) -> dict:
    """Invoke qwen3.7-max via ``opencode run`` one-shot.

    Returns a dict with at minimum a ``verdict`` key. Errors surface as
    ``verdict=judge_error|json_parse_error``.
    """
    t0 = time.time()
    try:
        proc = subprocess.run(
            [OPENCODE_BIN, "run", "--format", "json", "-m", model, prompt],
            capture_output=True,
            text=True,
            timeout=REQUEST_TIMEOUT_S,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except FileNotFoundError:
        return {
            "verdict": "judge_error",
            "error": f"`{OPENCODE_BIN}` not on PATH.",
            "duration_s": time.time() - t0,
        }
    except subprocess.TimeoutExpired:
        return {
            "verdict": "judge_error",
            "error": f"opencode run timed out after {REQUEST_TIMEOUT_S}s",
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

    # opencode --format json emits one JSON event per line. The model's final
    # textual reply lives in events of type "text" inside ``part.text``.
    # Concatenate all "text" parts to assemble the full assistant response.
    text_parts: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "text":
            part = evt.get("part") or {}
            txt = part.get("text")
            if isinstance(txt, str):
                text_parts.append(txt)

    if not text_parts:
        return {
            "verdict": "judge_error",
            "error": "no text event in opencode JSON stream",
            "stdout_tail": proc.stdout[-500:],
            "duration_s": duration,
        }

    assembled = "".join(text_parts)
    return parse_json_verdict(assembled, duration_s=duration)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--model",
        default="openrouter/qwen/qwen3.7-max",
        help="opencode model id (default: openrouter/qwen/qwen3.7-max)",
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
        print(f"Would subprocess `{OPENCODE_BIN} run --format json -m {args.model} PROMPT` per case")
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
            verdict = call_opencode(prompt, args.model)
            score = score_case(verdict, case["gold"])
            scores.append(score)
            row = judgment_row_from_case(case=case, model=args.model, verdict=verdict, score=score)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()  # survive mid-run kills (lesson from hermes cal SIGTERM)
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
        "via": "opencode-openrouter",
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
