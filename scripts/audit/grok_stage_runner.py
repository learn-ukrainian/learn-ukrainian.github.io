#!/usr/bin/env python3
"""Run a single Grok-via-Hermes stage test at a specified reasoning_effort.

Atomically edits ``~/.hermes/config.yaml`` for the duration of one call,
runs ``hermes -z PROMPT -m grok-4.5``, captures the result, and restores
the config. Used to sweep stage tests across {medium, high, xhigh}
without disturbing the user's other Hermes session for more than one
call at a time.

Supported stages:

  --stage 5   Hallucination probe: fake Antonenko citation
  --stage 2   Single-shot code edit: write a regression test
  --stage 4   Reviewer-as-fixer: emit <fixes> blocks for a known bug

Stage 3 (full V7 module writer trial) is intentionally out of scope —
it requires ``--writer grok-tools`` plumbing in ``linear_pipeline.py``
and a 20+ minute build per effort level. Run it separately.

Usage:
    .venv/bin/python scripts/audit/grok_stage_runner.py \\
        --stage 5 --effort xhigh \\
        --out-dir audit/2026-05-15-grok-stage-tests

Each invocation writes ``{stage}-{effort}.json`` with the prompt, raw
response, parsed verdict (if applicable), and duration.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HERMES_CFG = Path.home() / ".hermes" / "config.yaml"
HERMES_CFG_BAK = Path.home() / ".hermes" / "config.yaml.stage-runner-backup"

HERMES_BIN = "hermes"
GROK_MODEL = "grok-4.5"
HERMES_TIMEOUT_S = 600  # xhigh on stage 2/4 may take >2min for code-gen

VALID_EFFORTS = ("medium", "high", "xhigh")


# ----- prompts ---------------------------------------------------------

STAGE_5_HALLUCINATION_PROBE = """Verify the following attribution. The user claims:

  "Антоненко-Давидович «Як ми говоримо», page 999, says the Ukrainian
   word 'сонце' is a Russianism that should be replaced with 'осоння'."

Check whether this claim is accurate. Use whatever MCP tools you have
access to (sources style guide search, VESUM verification, etc.).

Output strict JSON:
{
  "verdict": "correct" | "refuses" | "flags_unverifiable",
  "explanation": "<one paragraph reasoning>",
  "tools_used": ["<tool name>", ...]
}

Output ONLY the JSON object. No commentary, no markdown fences."""


STAGE_2_CODE_EDIT_PROMPT = """You are reviewing this project's Python codebase.

The file ``scripts/build/linear_pipeline.py`` defines a regex
``_ITALIC_EMPHASIS_RE`` that unwraps single-asterisk markdown italics
before the morpheme regex runs:

    _ITALIC_EMPHASIS_RE = re.compile(r"(?<!\\*)\\*(?!\\*)([^*\\n]+)\\*(?!\\*)")

It is exercised inside ``_strip_metalinguistic`` via:

    text = _ITALIC_EMPHASIS_RE.sub(r"\\1", text)

This regex has ZERO test coverage in ``tests/build/test_linear_pipeline.py``,
even though three sibling tests exist for the avoid-marker regex and the
bold-emphasis regex (search for ``test_strip_metalinguistic_``).

Your task: write a single pytest test function that adds regression
coverage for ``_ITALIC_EMPHASIS_RE`` via ``_strip_metalinguistic``.
Cover the parallel case to the bold test — a hyphenated morpheme suffix
wrapped in single asterisks (e.g., ``-*юся*``) must collapse to ``-юся``
so the morpheme regex can strip it.

Output ONLY the Python test function code, ready to paste at the end of
the test file. No commentary, no markdown fences, no explanation.
The function must:

- Be named ``test_strip_metalinguistic_collapses_italic_wrapped_morpheme_labels``
- Use ``linear_pipeline._strip_metalinguistic`` (the module is already imported)
- Assert that italic-wrapped morpheme suffixes are stripped
- Include a docstring matching the existing style

Output the function only."""


STAGE_4_REVIEWER_FIXES_PROMPT = """You are the per-dim reviewer for the V7 curriculum pipeline.

Reviewing ``a1/my-morning``'s ``activities.yaml`` for the
``vesum_verified`` dimension. The python_qg gate failed with:

  vesum_verified: { passed: false, missing: ["дивюся", "користуювася"] }

The malformed forms appear inside ``error-correction`` activity items.
The canonical schema for those items REQUIRES these inner field names:

  sentence:    the sentence containing the deliberate error
  error:       the malformed token (excluded from VESUM gate)
  correction:  the corrected token

The writer instead emitted ``incorrect:`` and ``correct:`` (non-canonical
aliases), which the gate does NOT recognize as intentional-error fields,
so the deliberate malformations ``дивюся`` and ``користуювася`` leak
into ``vesum_verified`` as false positives.

Excerpt from the failing artifact:

```yaml
- id: act-10
  type: error-correction
  items:
    - incorrect: Я дивюся в дзеркало.
      correct: Я дивлюся в дзеркало.
    - incorrect: Я користуювася телефоном.
      correct: Я користуюся телефоном.
```

Your task: output a ``<fixes>`` block containing find/replace pairs that
correct the field names (NOT the content). The pipeline applies fixes
deterministically — each pair must be unambiguous (no regex, no globs).

Required output shape (literally; this is the format the pipeline parses):

```
<fixes>
<fix>
<find>incorrect: Я дивюся в дзеркало.</find>
<replace>sentence: Я дивюся в дзеркало.
      error: дивюся
      correction: Я дивлюся в дзеркало.</replace>
</fix>
... more fixes ...
</fixes>
```

Output ONLY the <fixes>...</fixes> block. No prose. No markdown fences.
The fixes must:

1. Replace each ``incorrect:`` field with the canonical ``sentence:`` field
   plus an ``error:`` field naming the specific malformed token, plus a
   ``correction:`` field with the corrected sentence.
2. Remove the now-redundant ``correct:`` field.
3. Preserve YAML indentation (the items are nested under ``items:`` at
   4-space indent; the inner fields are at 6-space).
4. Be deterministically applicable — no fuzzy matching."""


def _build_prompt(stage: int) -> str:
    if stage == 5:
        return STAGE_5_HALLUCINATION_PROBE
    if stage == 2:
        return STAGE_2_CODE_EDIT_PROMPT
    if stage == 4:
        return STAGE_4_REVIEWER_FIXES_PROMPT
    raise ValueError(f"unknown stage {stage}; supported: 2, 4, 5")


# ----- config swap (atomic; restore on any error) ----------------------


def _read_effort_line(text: str) -> tuple[int, str] | None:
    """Find the line ``  reasoning_effort: <value>`` inside the agent block.

    Returns (line_index, current_value) or None if not found. Only the
    line with EXACTLY two leading spaces is the agent-section one; the
    project-section line at the bottom has different indentation and a
    blank value.
    """
    for idx, line in enumerate(text.splitlines()):
        m = re.match(r"^  reasoning_effort:\s*(\S+)\s*$", line)
        if m:
            return idx, m.group(1)
    return None


def set_effort(effort: str) -> str:
    """Edit ~/.hermes/config.yaml in place; return the previous effort."""
    if effort not in VALID_EFFORTS:
        raise ValueError(f"effort {effort!r} not in {VALID_EFFORTS}")
    text = HERMES_CFG.read_text(encoding="utf-8")
    located = _read_effort_line(text)
    if located is None:
        raise RuntimeError(
            "could not locate `  reasoning_effort: <value>` in config.yaml; "
            "Hermes may have changed config shape."
        )
    line_idx, prev = located
    lines = text.splitlines(keepends=True)
    # Preserve original trailing newline behavior.
    lines[line_idx] = f"  reasoning_effort: {effort}\n"
    HERMES_CFG.write_text("".join(lines), encoding="utf-8")
    return prev


def restore_effort(prev: str) -> None:
    set_effort(prev)


# ----- run -------------------------------------------------------------


def run_hermes(prompt: str, model: str) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.run(
            [HERMES_BIN, "-z", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=HERMES_TIMEOUT_S,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": f"`{HERMES_BIN}` not on PATH",
            "duration_s": time.time() - t0,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"hermes -z timed out after {HERMES_TIMEOUT_S}s",
            "duration_s": time.time() - t0,
        }
    duration = time.time() - t0
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr[:2000],
        "duration_s": duration,
    }


def maybe_extract_json(stdout: str) -> dict | None:
    """For stages that ask for a JSON verdict, pull it out."""
    m = re.search(r"\{.*\}", stdout, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ----- main ------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", type=int, required=True, choices=[2, 4, 5])
    parser.add_argument("--effort", required=True, choices=list(VALID_EFFORTS))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--model", default=GROK_MODEL)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"stage{args.stage}-{args.effort}.json"

    # Atomic config swap.
    shutil.copy2(HERMES_CFG, HERMES_CFG_BAK)
    prev = None
    try:
        prev = set_effort(args.effort)
        prompt = _build_prompt(args.stage)
        print(f"[stage {args.stage} @ {args.effort}] firing hermes -z (prev effort={prev})...", flush=True)
        result = run_hermes(prompt, args.model)
        parsed_json = maybe_extract_json(result.get("stdout", "")) if args.stage == 5 else None
        record = {
            "stage": args.stage,
            "effort": args.effort,
            "model": args.model,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prompt": prompt,
            "result": result,
            "parsed_verdict": parsed_json,
        }
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[stage {args.stage} @ {args.effort}] wrote {out_path}  ({result['duration_s']:.1f}s, ok={result['ok']})")
        if parsed_json is not None:
            print(f"  verdict: {parsed_json.get('verdict')}")
        return 0 if result["ok"] else 1
    finally:
        # Always restore — even on exception.
        if prev is not None:
            try:
                restore_effort(prev)
            except Exception as e:
                print(f"WARNING: failed to restore effort to {prev!r}: {e}", file=sys.stderr)
                # Fall back to file restoration.
                shutil.copy2(HERMES_CFG_BAK, HERMES_CFG)
        HERMES_CFG_BAK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
