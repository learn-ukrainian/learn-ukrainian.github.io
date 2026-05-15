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
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT_ROOT / "data" / "sources.db"
HERMES_AUTH = Path.home() / ".hermes" / "auth.json"

# Use PR #2006's branch as the canonical source for the calibration set
# + Antonenko prompt template. This keeps the test reproducible without
# requiring PR #2006 to merge first.
PR_2006_REF = "origin/pr-2006"
CALIBRATION_BLOB = "eval/russianism/calibration-cases.jsonl"

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


def pull_calibration_cases() -> list[dict]:
    """Pull the 12 calibration cases from PR #2006's branch (read-only).

    We do NOT copy the file to the working tree — keeps PR #2006 the
    single source of truth for the gold labels.
    """
    proc = subprocess.run(
        ["git", "show", f"{PR_2006_REF}:{CALIBRATION_BLOB}"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit(
            f"ERROR: could not read {CALIBRATION_BLOB} from {PR_2006_REF}.\n"
            f"git stderr: {proc.stderr.strip()}\n"
            "If origin/pr-2006 has been pruned, refetch with:\n"
            "  git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'"
        )
    cases = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        cases.append(json.loads(line))
    return cases


def retrieve_antonenko(text: str, k: int = 8) -> list[dict]:
    """Find Antonenko entries whose headwords appear in ``text``.

    Ported verbatim from ``scripts/audit/russianism_judge.py`` on
    ``origin/pr-2006``. Grounds the judge prompt in canonical evidence.
    """
    conn = sqlite3.connect(DB)
    try:
        words = set(re.findall(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+", text.lower()))
        if not words:
            return []
        placeholders = ",".join("?" * len(words))
        rows = conn.execute(
            f"""
            SELECT word, section, page, text
            FROM style_guide
            WHERE word_lower IN ({placeholders})
               OR EXISTS (
                   SELECT 1 FROM (
                       SELECT value FROM json_each(?)
                   ) t WHERE word_lower = t.value
               )
            LIMIT ?
            """,
            (*words, json.dumps(list(words)), k),
        ).fetchall()
    finally:
        conn.close()
    return [
        {"headword": r[0], "section": r[1], "page": r[2], "text": (r[3] or "")[:600]}
        for r in rows
    ]


def build_judge_prompt(target_text: str, antonenko_entries: list[dict]) -> str:
    """Universal Russianism-judge prompt (identical across families)."""
    rules_section = ""
    if antonenko_entries:
        rules_section = (
            "## Relevant Antonenko-Davydovych entries "
            "(potentially applicable rules):\n\n"
        )
        for i, e in enumerate(antonenko_entries[:8], 1):
            rules_section += f"### Rule {i}: {e['headword']}\n{e['text']}\n\n"
    else:
        rules_section = (
            "(No directly-keyed Antonenko entries found for words in this text. "
            "Apply general knowledge of Ukrainian register and Russianism patterns.)\n"
        )

    return f"""You are an expert Ukrainian-language proofreader specializing in identifying Russianisms (русизми), calques (кальки), Surzhyk (суржик), and unnatural Ukrainian phrasing.
Your authority is Антоненко-Давидович «Як ми говоримо» — the canonical Ukrainian reference for Russianism identification and correction.

## Text to evaluate

```
{target_text}
```

{rules_section}

## Your task

Identify EVERY Russianism, calque, Surzhyk, or unnatural Ukrainian construction in the text above. For each issue:

- Quote the exact problematic phrase
- Cite the relevant Antonenko rule by its headword (if applicable from the rules above) or general principle
- Provide the correct Ukrainian alternative
- Severity: 1=minor (debatable), 2=clear Russianism, 3=blatant calque or borrowing

If the text is genuinely clean Ukrainian with NO Russianisms, output `{{"verdict": "clean", "issues": []}}`.

Otherwise output JSON with this exact shape:

```json
{{
  "verdict": "issues_found",
  "issues": [
    {{"phrase": "...", "rule": "...", "correct": "...", "severity": 1-3}}
  ]
}}
```

Output ONLY the JSON object — no commentary, no markdown fences, no preamble."""


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

    raw_content = proc.stdout
    # Strip markdown fences if the judge wrapped its JSON.
    m = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if not m:
        return {
            "verdict": "judge_error",
            "raw": raw_content[:500],
            "duration_s": duration,
            "note": "no JSON object in response",
        }
    try:
        verdict = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return {
            "verdict": "json_parse_error",
            "raw": m.group(0)[:500],
            "error": str(e),
            "duration_s": duration,
        }
    verdict["_duration_s"] = duration
    return verdict


def score_case(verdict: dict, gold: dict) -> dict:
    """Per-case scoring vs hand-labels.

    Returns ``{"case_acc": bool, "sev1_tolerant": dict}``.
    Mirrors ``score_judge_calibration.py`` logic from PR #2006:

    - Case-level accuracy = correctly classified clean vs issues_found.
    - Sev1-tolerant P/R/F1 = count sev≥2 flags only (sev1 is debatable
      and not penalized).
    """
    expected_clean = bool(gold.get("expected_clean"))
    judged_clean = verdict.get("verdict") == "clean"
    case_acc = expected_clean == judged_clean

    # Sev≥2 flags from the judge (the "actionable" set).
    issues = verdict.get("issues") or []
    sev2_plus_judge = sum(
        1
        for it in issues
        if isinstance(it, dict) and isinstance(it.get("severity"), int) and it["severity"] >= 2
    )
    # Gold's expected_flags is the count of expected sev≥2 patterns.
    expected_flags_n = len(gold.get("expected_flags") or [])
    if expected_clean:
        # Clean cases: any sev≥2 flag is a false positive.
        fp = sev2_plus_judge
        fn = 0
        tp = 0
    else:
        # Dirty cases: tp = min(judge flags, expected), fn = remaining
        # expected, fp = judge flags beyond expected. This is a coarse
        # but defensible approximation when phrase-level alignment isn't
        # tracked here.
        tp = min(sev2_plus_judge, expected_flags_n)
        fn = max(0, expected_flags_n - sev2_plus_judge)
        fp = max(0, sev2_plus_judge - expected_flags_n)

    return {
        "case_acc": case_acc,
        "judged_clean": judged_clean,
        "expected_clean": expected_clean,
        "judge_sev2_plus_count": sev2_plus_judge,
        "expected_flags_count": expected_flags_n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def aggregate(scores: list[dict]) -> dict:
    """Aggregate per-case scores into P/R/F1 + case accuracy."""
    tp = sum(s["tp"] for s in scores)
    fp = sum(s["fp"] for s in scores)
    fn = sum(s["fn"] for s in scores)
    n = len(scores)
    case_acc = sum(1 for s in scores if s["case_acc"]) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "n": n,
        "case_accuracy": round(case_acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


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
            row = {
                "prompt_id": case["prompt_id"],
                "model": args.model,
                "verdict": verdict.get("verdict"),
                "judge_sev2_plus_count": score["judge_sev2_plus_count"],
                "expected_flags_count": score["expected_flags_count"],
                "case_acc": score["case_acc"],
                "duration_s": round(verdict.get("_duration_s", verdict.get("duration_s", 0.0)), 2),
                "raw": verdict,
            }
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

    report_lines = [
        f"# Grok 4.3 Russianism judge calibration — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        f"Model: `{args.model}` via Hermes OAuth (`api.x.ai/v1`)",
        f"Cases: {agg['n']} (from `{CALIBRATION_BLOB}` on `{PR_2006_REF}`)",
        "",
        "## Aggregate",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Case accuracy | **{agg['case_accuracy']*100:.1f}%** |",
        f"| Precision (sev≥2) | {agg['precision']*100:.1f}% |",
        f"| Recall (sev≥2) | {agg['recall']*100:.1f}% |",
        f"| **F1 (sev≥2)** | **{agg['f1']*100:.1f}%** |",
        f"| tp / fp / fn | {agg['tp']} / {agg['fp']} / {agg['fn']} |",
        "",
        "## Reference leaderboard (2026-05-15, n=12)",
        "",
        "| Judge | F1 | Precision | Recall | Case acc |",
        "|---|---:|---:|---:|---:|",
        "| claude-opus-4-7 | 86% | 79% | 94% | 100% |",
        "| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |",
        "| gpt-5.5 | 78% | 90% | 69% | 83% |",
        f"| **{args.model}** | **{agg['f1']*100:.0f}%** | **{agg['precision']*100:.0f}%** | **{agg['recall']*100:.0f}%** | **{agg['case_accuracy']*100:.0f}%** |",
        "",
        f"Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `{PR_2006_REF}` for the prior 3 judges.",
        "",
        "## Per-case breakdown",
        "",
        "| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |",
        "|---|---|---|:---:|---:|---:|",
    ]
    with judgments_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            case_id = row["prompt_id"]
            expected = "clean" if row["expected_flags_count"] == 0 else "issues"
            judged = row["verdict"]
            mark = "✓" if row["case_acc"] else "✗"
            report_lines.append(
                f"| `{case_id}` | {expected} | {judged} | {mark} | {row['judge_sev2_plus_count']} | {row['duration_s']:.1f} |"
            )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("")
    print(f"Wrote {judgments_path}")
    print(f"Wrote {report_path}")
    print(f"Wrote {leaderboard_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
