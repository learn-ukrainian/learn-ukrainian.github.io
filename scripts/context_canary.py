#!/usr/bin/env python3
"""Context-integrity canary — a DETERMINISTIC brain-rot monitor for long sessions.

Why this exists
---------------
With autocompact disabled, a single Claude Code session can grow to 700K-1M tokens.
Long-context retrieval degrades ("brain rot") well before the model *notices* — a
dropped instruction or a misremembered SHA is invisible from the inside, because the
model does not reliably self-report rot. Trusting a self-assessment ("I feel fine")
is exactly the failure mode. So we measure instead.

How it works
------------
1. `mint`  — freeze K anchors as (id, question, ground-truth answer). The truth is
             captured EARLY (low context, presumed clean) from real state, then frozen.
2. ...time passes, context grows...
3. `score` — the agent answers the same questions FROM MEMORY/CONTEXT (no scrolling
             back to re-read), writes them to a JSON, and this script diffs them against
             the frozen truth. The SCRIPT computes the match — the agent cannot grade
             itself into a pass. Drift below threshold => hand off NOW, regardless of
             the token count.
4. Each score appends a (context_tokens, score) row to a CSV so we can MAP where rot
   starts for this model on this session shape across runs.

Contract:
  mint --facts  (unique non-empty ids, inline JSON list or file path)
  score uses --threshold (sim via difflib on normalized), --pass-ratio (default 0.75/0.85),
  exact id lookup (no id normalization), rc 0/2.
  The retired strict rollover probe (production-handoff-v2) is rejected, never
  reinterpreted as a --facts probe.

Usage
-----
  .venv/bin/python scripts/context_canary.py mint --facts facts.json --out probe.json
  .venv/bin/python scripts/context_canary.py score --probe probe.json --answers answers.json \
      --context-tokens 500000 --model claude-opus-5-5 --log canary_log.csv \
      [--threshold 0.75] [--pass-ratio 0.85]

`facts.json`   : [{"id": "...", "q": "...", "a": "..."}, ...]
`answers.json` : {"<id>": "<answer-from-memory>", ...}

Exit codes: 0 PASS, 2 FAIL-HANDOFF, 1 usage/insufficient/IO/JSON error.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import sys
from pathlib import Path


def _norm(value: object) -> str:
    """Whitespace/case-insensitive normalization for fuzzy comparison."""
    return " ".join(str(value).strip().lower().split())


def _similarity(truth: str, got: str) -> float:
    return difflib.SequenceMatcher(None, _norm(truth), _norm(got)).ratio()


def _is_exact_legacy_anchors_only(probe: object) -> bool:
    """Legacy probes are ONLY the exact original shape produced by --facts: {"anchors": [{"id":, "q":, "a":}, ...]}.
    Any other shape, including the retired production-handoff-v2 probe, is rejected.
    """
    if not isinstance(probe, dict):
        return False
    if set(probe.keys()) != {"anchors"}:
        return False
    anchors = probe.get("anchors")
    if not isinstance(anchors, list) or len(anchors) == 0:
        return False
    for a in anchors:
        if not isinstance(a, dict):
            return False
        if set(a.keys()) != {"id", "q", "a"}:
            return False
        for k in ("id", "q", "a"):
            val = a.get(k)
            if not isinstance(val, str) or not val.strip():
                return False
    return True


def _load_facts_spec(spec: str) -> object:
    """Load facts from EITHER an inline JSON list OR a path to a JSON file.

    `--facts` accepts both forms: the documented `--facts facts.json` path AND an
    inline `[{...}]` payload (the arg help advertises "JSON list of {id,q,a}").
    A JSON list starts with '[' (an object with '{'); a filesystem path effectively
    never does — a bare name starting with a bracket would need quoting and is an
    edge case — so the leading bracket selects inline vs file for all practical
    inputs. This keeps the CLI help honest and avoids the opaque 'File name too
    long' OSError a caller hit when passing inline JSON to the file-only reader.
    """
    if spec.lstrip()[:1] in ("[", "{"):
        return json.loads(spec)
    return json.loads(Path(spec).read_text(encoding="utf-8"))


def cmd_mint(args: argparse.Namespace) -> int:
    facts_spec = args.facts
    try:
        facts = _load_facts_spec(facts_spec)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: --facts cannot be read as a file: {facts_spec} ({type(exc).__name__})", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: --facts is not valid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(facts, list) or not facts:
        print("error: --facts must be a non-empty JSON list of {id,q,a}", file=sys.stderr)
        return 1
    ids = [f.get("id") for f in facts]
    if len(set(ids)) != len(ids) or not all(ids):
        print("error: every fact needs a unique non-empty 'id'", file=sys.stderr)
        return 1
    probe = {"anchors": [{"id": f["id"], "q": f["q"], "a": f["a"]} for f in facts]}
    Path(args.out).write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"minted {len(facts)} anchors -> {args.out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    try:
        probe = json.loads(Path(args.probe).read_text(encoding="utf-8"))
        answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read probe or answers: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: probe or answers not valid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(probe, dict):
        print("error: probe must be a JSON object", file=sys.stderr)
        return 1
    anchors = probe.get("anchors", [])
    if not isinstance(anchors, list) or not anchors:
        print("error: probe has no anchors", file=sys.stderr)
        return 1

    # Only the exact anchors-only shape {"anchors": [{"id":str,"q":str,"a":str}, ...]} from --facts
    # is scored. The retired strict rollover probe and partial/forged shapes fail closed.
    if not _is_exact_legacy_anchors_only(probe):
        if probe.get("schema") == "production-handoff-v2":
            print(
                "error: the strict production-handoff-v2 rollover probe is retired; only --facts probes are scored",
                file=sys.stderr,
            )
        else:
            print("error: probe must be exactly the --facts shape {anchors: [{id, q, a}, ...]}", file=sys.stderr)
        return 2
    correct = 0
    rows = []
    thresh = args.threshold
    for anchor in anchors:
        aid = anchor.get("id", "")
        truth = anchor.get("a", "")
        got = answers.get(aid, "") if isinstance(answers, dict) else ""
        sim = _similarity(truth, got)
        ok = sim >= thresh
        correct += 1 if ok else 0
        rows.append((aid, ok, sim, anchor.get("q", ""), truth, got))
    k = len(anchors)
    score_val = correct / k if k > 0 else 0.0
    for aid, ok, sim, q, truth, got in rows:
        tag = "PASS " if ok else "DRIFT"
        print(f"  [{tag}] {aid} (sim={sim:.2f}) {q}")
        if not ok:
            print(f"          truth: {truth!r}")
            print(f"          got  : {got!r}")
    verdict = "PASS" if score_val >= args.pass_ratio else "FAIL-HANDOFF"
    print(f"SCORE {correct}/{k} = {score_val:.2f}  ->  {verdict}")
    if args.log:
        log_path = Path(args.log)
        is_new = not log_path.exists()
        with log_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if is_new:
                writer.writerow(["context_tokens", "model", "k", "correct", "score", "verdict"])
            writer.writerow([args.context_tokens, args.model, k, correct, f"{score_val:.3f}", verdict])
    return 0 if verdict == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    mint = sub.add_parser("mint", help="Freeze ground-truth anchors into a probe file.")
    mint.add_argument("--facts", required=True, help="Inline JSON list of {id,q,a}, or a path to a JSON file")
    mint.add_argument("--out", required=True, help="Probe output path")
    mint.set_defaults(func=cmd_mint)

    score = sub.add_parser(
        "score",
        help="Diff from-memory answers against the frozen probe (threshold + pass-ratio).",
    )
    score.add_argument("--probe", required=True)
    score.add_argument("--answers", required=True, help="JSON {id: answer}")
    score.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Per-anchor similarity to count as recalled (default 0.75)",
    )
    score.add_argument(
        "--pass-ratio", type=float, default=0.85, help="Fraction of anchors that must pass (default 0.85)"
    )
    score.add_argument("--context-tokens", type=int, default=0, help="Context size at probe time (for the log)")
    score.add_argument("--model", default="unknown")
    score.add_argument("--log", help="CSV to append the (context_tokens, score) data point")
    score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse usage errors (e.g. missing --facts) must surface as rc 2
        # so tests can assert parser rc 2 while CLI still exits 2. Func returns are normal.
        if isinstance(getattr(exc, "code", None), int):
            return exc.code
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
