#!/usr/bin/env python3
"""LLM-as-judge for Russianism detection — universal multi-family judge.

Antonenko-Davydovych-grounded LLM judge for evaluating Ukrainian text for
Russianisms (русизми), calques (кальки), Surzhyk, and unnatural phrasing.
Same prompt across all three judge families = fair head-to-head measurement.

Companion to ``scripts/audit/russianism_eval.py`` (the eval harness that
produces ``outputs.jsonl``). This script consumes those outputs and
produces ``judgments-{tag}.jsonl`` with one issue list per (prompt, model)
cell. Used in two modes:

1. **Calibration mode** — score the judge against a hand-labeled gold
   set (``eval/russianism/calibration-cases.jsonl``) and compute P/R/F1
   via ``scripts/audit/score_judge_calibration.py``.
2. **Production mode** — judge model outputs from the eval harness or
   live curriculum content; flag sev≥2 issues for human review.

Supported judges (across three families, all using identical prompt):

  --judge-family gemini  --judge-model gemini-3.1-pro-preview
  --judge-family gemini  --judge-model gemini-3-pro-preview
  --judge-family codex   --judge-model gpt-5.5
  --judge-family claude  --judge-model claude-opus-4-7
  --judge-family claude  --judge-model claude-opus-4-6

Per the 2026-05-15 4-judge calibration study (n=12 hand-labeled cases),
**claude-opus-4-7 is the recommended primary judge** (F1=86%, 100%
case-level accuracy, ~30s/call). gpt-5.5 is the recommended
second-opinion validator (highest precision, ~25s/call). Avoid using
gemini-3.1-pro-preview as primary — it over-flags greeting genitives
(`Доброго дня!`) and has unstable latency under load.

Usage:
    .venv/bin/python scripts/audit/russianism_judge.py \\
        --judge-family claude --judge-model claude-opus-4-7 \\
        --inputs path/to/outputs.jsonl \\
        --out    path/to/judgments-opus47.jsonl

For one-shot interactive testing:
    .venv/bin/python scripts/audit/russianism_judge.py \\
        --judge-family claude --judge-model claude-opus-4-7 \\
        --text "Доброго дня! Чекаю на ваші коментарі у вкладенні."
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
sys.path.insert(0, str(PROJECT_ROOT))

DB = PROJECT_ROOT / "data" / "sources.db"
BRIDGE = PROJECT_ROOT / "scripts" / "ai_agent_bridge" / "__main__.py"
VENV_PY = PROJECT_ROOT / ".venv" / "bin" / "python"

# Per-family subprocess timeout. Calibrated empirically: gemini-judge
# calls can exceed 240s under load; claude/codex consistently land under
# 60s but headroom is cheap.
JUDGE_TIMEOUT_S = 480


def retrieve_antonenko(text: str, k: int = 8) -> list[dict]:
    """Find Antonenko-Davydovych entries whose headwords appear in ``text``.

    Used to ground the judge prompt in the canonical Russianism reference
    rather than relying on the judge's pre-training memory of Antonenko.
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
    """Construct the judge prompt. Identical across families = fair test."""
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


def _bridge_db_conn():
    """Connect to the agent-bridge messages DB (for claude/codex response capture)."""
    from scripts.ai_agent_bridge._db import get_db  # type: ignore

    return get_db()


def _latest_bridge_response(task_id: str, family: str, from_agent: str) -> str | None:
    """Fetch the latest response row for ``task_id`` from the bridge DB.

    Mirrors :func:`scripts.audit.russianism_eval._latest_bridge_response`.
    Used when the bridge does not stream stdout (claude / codex families).
    """
    conn = _bridge_db_conn()
    try:
        row = conn.execute(
            """
            SELECT content FROM messages
            WHERE task_id = ? AND from_llm = ? AND to_llm = ?
              AND message_type IN ('response', 'error')
            ORDER BY id DESC LIMIT 1
            """,
            (task_id, family, from_agent),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    try:
        return str(row["content"])
    except (TypeError, IndexError):
        return str(row[0])


def call_judge(prompt: str, task_id: str, family: str, model: str, from_agent: str) -> dict:
    """Dispatch the judge prompt to the named bridge family. Return parsed verdict.

    Response-capture pattern is family-specific:

      * gemini — supports ``--stdout-only``; capture stdout directly.
      * codex / claude — no stdout passthrough; read from bridge DB after
        subprocess exit.
    """
    t0 = time.time()
    base = [str(VENV_PY), str(BRIDGE)]
    proc: subprocess.CompletedProcess[str]
    raw: str | None
    if family == "gemini":
        argv = [
            *base, "ask-gemini", "-",
            "--task-id", task_id,
            "--from", from_agent,
            "--model", model,
            "--stdout-only",
            "--skip-model-check",
            "--no-github",
        ]
        proc = subprocess.run(
            argv, cwd=str(PROJECT_ROOT), input=prompt,
            capture_output=True, text=True, timeout=JUDGE_TIMEOUT_S,
        )
        raw = proc.stdout.strip() if proc.stdout.strip() else _latest_bridge_response(task_id, "gemini", from_agent)
    elif family == "codex":
        argv = [
            *base, "ask-codex", "-",
            "--task-id", task_id,
            "--from", from_agent,
            "--to-model", model,
            "--new-session",
        ]
        proc = subprocess.run(
            argv, cwd=str(PROJECT_ROOT), input=prompt,
            capture_output=True, text=True, timeout=JUDGE_TIMEOUT_S,
        )
        raw = _latest_bridge_response(task_id, "codex", from_agent)
    elif family == "claude":
        # ask-claude takes content as positional, not stdin.
        argv = [
            *base, "ask-claude", prompt,
            "--task-id", task_id,
            "--from", from_agent,
            "--to-model", model,
            "--new-session",
        ]
        proc = subprocess.run(
            argv, cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=JUDGE_TIMEOUT_S,
        )
        raw = _latest_bridge_response(task_id, "claude", from_agent)
    else:
        raise ValueError(f"unknown judge family {family!r} — expected one of: gemini, codex, claude")
    duration = time.time() - t0

    if raw is None or not raw.strip():
        return {
            "verdict": "judge_error",
            "raw": (proc.stdout or "")[:500],
            "stderr": (proc.stderr or "")[:500],
            "duration_s": duration,
            "note": "no bridge response and no stdout",
        }

    # The judge prompt asks for raw JSON; in practice some judges wrap it
    # in markdown fences or add a preamble. Extract the outermost JSON object.
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {
            "verdict": "judge_error",
            "raw": raw[:500],
            "duration_s": duration,
            "note": "no JSON object in response",
        }
    try:
        verdict = json.loads(m.group(0))
        verdict["_duration_s"] = duration
        return verdict
    except json.JSONDecodeError as e:
        return {
            "verdict": "json_parse_error",
            "raw": m.group(0)[:500],
            "error": str(e),
            "duration_s": duration,
        }


def judge_one(text: str, label: str, family: str, model: str, from_agent: str) -> dict:
    """Score one text. Returns a dict suitable for direct JSONL emission."""
    entries = retrieve_antonenko(text, k=8)
    prompt = build_judge_prompt(text, entries)
    task_id = f"judge-{family}-{label}-{int(time.time())}"
    verdict = call_judge(prompt, task_id, family, model, from_agent)
    return {
        "label": label,
        "judge_model": model,
        "judge_family": family,
        "antonenko_entries_retrieved": len(entries),
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge-family", required=True, choices=["gemini", "codex", "claude"],
                    help="Bridge family for the judge model.")
    ap.add_argument("--judge-model", required=True,
                    help="Exact model ID (e.g. claude-opus-4-7, gpt-5.5, gemini-3.1-pro-preview).")
    ap.add_argument("--from-agent", default=None,
                    help="Sender label for bridge accounting (default: derived from judge-model).")
    ap.add_argument("--inputs", help="Path to outputs.jsonl (eval harness format).")
    ap.add_argument("--text", help="One-shot text mode (interactive testing).")
    ap.add_argument("--label", default="oneshot", help="Label for one-shot mode.")
    ap.add_argument("--out", help="Output JSONL path. Default: <inputs>-judgments-<tag>.jsonl")
    args = ap.parse_args()

    from_agent = args.from_agent or f"russianism-judge-{re.sub(r'[^a-zA-Z0-9-]+', '-', args.judge_model)}"

    if args.text:
        result = judge_one(args.text, args.label, args.judge_family, args.judge_model, from_agent)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.inputs:
        sys.exit("Need --inputs (eval outputs.jsonl) or --text (one-shot mode).")

    inputs_path = Path(args.inputs)
    if args.out:
        out_path = Path(args.out)
    else:
        suffix_tag = re.sub(r"[^a-zA-Z0-9]+", "", args.judge_model)
        out_path = inputs_path.with_name(f"judgments-{suffix_tag}.jsonl")

    inputs = [json.loads(line) for line in inputs_path.read_text().splitlines() if line.strip()]
    inputs = [i for i in inputs if i.get("status") == "ok"]
    print(f"Judging {len(inputs)} cells with {args.judge_family}/{args.judge_model} → {out_path}", file=sys.stderr)

    with out_path.open("w", encoding="utf-8") as f:
        for i, inp in enumerate(inputs, 1):
            label = f"{inp.get('prompt_id', 'x')}-{inp.get('model', 'y')}"
            text = inp.get("output_text", "")
            print(f"  [{i}/{len(inputs)}] {label}", file=sys.stderr, flush=True)
            result = judge_one(text, label, args.judge_family, args.judge_model, from_agent)
            result["prompt_id"] = inp.get("prompt_id")
            result["model"] = inp.get("model")
            result["text_excerpt"] = text[:200]
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()
    print(f"Done — wrote {len(inputs)} judgments to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
