#!/usr/bin/env python3
"""Calibrate Grok 4.3 (via Hermes OAuth) as a Russianism judge.

Standalone test harness — does NOT depend on PR #2006 being merged.

Pulls the calibration cases + prompt builder logic from PR #2006's branch
(``origin/pr-2006``) without committing them to main, then runs Grok 4.3
through the same 12-case Antonenko-grounded gold set used to rank
``claude-opus-4-7`` / ``gemini-3.1-pro-preview`` / ``gpt-5.5`` in the
2026-05-15 calibration study.

Auth: reads the OAuth ``access_token`` from ``~/.hermes/auth.json``
(populated by ``hermes auth add xai-oauth``). Token value is never
printed; only the leading 8 chars + ``...`` appear in error messages.

Output:
    audit/2026-05-15-grok-4.3-judge-calibration/
        judgments.jsonl       one row per case (verdict + raw + duration)
        REPORT.md             F1 / P / R + per-case breakdown
        leaderboard-row.json  one row ready to drop into the 4-judge table

Usage:
    .venv/bin/python scripts/audit/grok_judge_calibration.py
    .venv/bin/python scripts/audit/grok_judge_calibration.py --dry-run
    .venv/bin/python scripts/audit/grok_judge_calibration.py --model grok-4.3-fast

Refs: PR #2006 (russianism_judge harness), issue #1975 (m20 RED),
calibration study at ``audit/2026-05-15-russianism-judge-calibration/``
on the PR #2006 branch.
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

HERMES_AUTH = Path.home() / ".hermes" / "auth.json"

# Hermes CLI provides the OAuth-authenticated path to Grok 4.3.
# Direct calls to api.x.ai/v1 return 403 (token has session-level scope,
# not bearer-style API access). Hermes' own `proxy` subcommand only
# supports the `nous` upstream right now (`hermes proxy providers`), so
# we subprocess the headless one-shot mode (`hermes -z PROMPT -m MODEL`)
# per case.
HERMES_BIN = "hermes"

# Per-case timeout. Reasoning + tool-set instantiation in Hermes can take
# 60–120s; mirror the judge harness on PR #2006 (480s ceiling) so we
# don't spuriously kill slow calls.
REQUEST_TIMEOUT_S = 480

OUT_DIR = PROJECT_ROOT / "audit" / "2026-05-15-grok-4.3-judge-calibration"


def load_hermes_oauth_token() -> str:
    """Read the xai-oauth access_token from ~/.hermes/auth.json.

    Raises a SystemExit with a redacted hint if the file/key is missing
    or the token is empty. The token value itself is NEVER printed.
    """
    if not HERMES_AUTH.exists():
        sys.exit(
            f"ERROR: {HERMES_AUTH} not found. Run `hermes auth add xai-oauth` first."
        )
    try:
        data = json.loads(HERMES_AUTH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: ~/.hermes/auth.json is not valid JSON: {e}")
    try:
        token = data["providers"]["xai-oauth"]["tokens"]["access_token"]
    except (KeyError, TypeError):
        sys.exit(
            "ERROR: no xai-oauth.tokens.access_token in ~/.hermes/auth.json. "
            "Re-run `hermes auth add xai-oauth`."
        )
    if not isinstance(token, str) or not token.strip():
        sys.exit("ERROR: xai-oauth access_token is empty.")
    return token.strip()


def call_grok(prompt: str, model: str) -> dict:
    """Invoke Grok 4.3 through the Hermes CLI's one-shot mode.

    Returns a dict with at minimum a ``verdict`` key. On subprocess or
    parse error, ``verdict`` is ``"judge_error"`` or ``"json_parse_error"``
    and ``raw`` carries the first 500 chars for inspection.

    Auth: Hermes reads the xai-oauth token from ``~/.hermes/auth.json``
    automatically; we don't touch the token directly. Hermes also handles
    token refresh and the session-level handshake xAI requires (which is
    why direct ``api.x.ai/v1/chat/completions`` calls return 403 even
    with a syntactically-valid Bearer token).
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="grok-4.3", help="xAI model id (default: grok-4.3)")
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

    # Hermes manages the OAuth token internally; we just verify it's there.
    load_hermes_oauth_token()
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
            print(f"[{idx}/{len(cases)}] {case['prompt_id']}  (antonenko={len(antonenko)}) ", end="", flush=True)
            verdict = call_grok(prompt, args.model)
            score = score_case(verdict, case["gold"])
            scores.append(score)
            row = judgment_row_from_case(case=case, model=args.model, verdict=verdict, score=score)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            tag = "✓" if score["case_acc"] else "✗"
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
        "via": "hermes-oauth",
        "n": agg["n"],
        "f1": agg["f1"],
        "precision": agg["precision"],
        "recall": agg["recall"],
        "case_accuracy": agg["case_accuracy"],
        "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    leaderboard_path.write_text(json.dumps(leaderboard_row, indent=2, ensure_ascii=False), encoding="utf-8")
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
