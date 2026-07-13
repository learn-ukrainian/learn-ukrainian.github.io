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

Legacy behavior (fully preserved for backward compatibility):
  mint --facts  (original three-anchor flow, unique non-empty ids, inline or file)
  score uses --threshold (sim via difflib on normalized), --pass-ratio (default 0.75/0.85),
  exact id lookup (no id normalization), rc 0/2.

New production v2 (for handoff snapshots):
  mint --snapshot  produces strict schema v2: exactly 10 unique anchors ONLY from
  durable handoff artifacts (goals, decision/rationale records, negative constraint/
  prohibition records, next actions). Never from git/SHAs/commits/modified/monitor/github.
  Anchors shaped exactly {id, q, a, category, match_mode, source_ref} where source_ref
  is durable artifact locator. Selection uses random.Random(seed) for lineage-randomized
  but reproducible order. Seed persisted (generated from snapshot if absent).
  All validation (no empty/UNKNOWN/dup/malformed/wrong-cat) happens before derivation.
  score for v2: strict 10/10 only, exact ID match (no normalization of ids), match_mode
  (exact|normalized) controls answer text only. Full schema + provenance + category
  checks. rc 2 on any failure to confirm. Legacy probes never treated as v2.

Usage
-----
  .venv/bin/python scripts/context_canary.py mint --facts facts.json --out probe.json
  .venv/bin/python scripts/context_canary.py mint --snapshot handoff-snapshot.json --out probe.json
  .venv/bin/python scripts/context_canary.py score --probe probe.json --answers answers.json \
      --context-tokens 500000 --model claude-opus-4-8 --log canary_log.csv \
      [--threshold 0.75] [--pass-ratio 0.85] [--verdict v.json]

`facts.json`   : [{"id": "...", "q": "...", "a": "..."}, ...]  (legacy)
`snapshot.json`: handoff with "goals", "decision_records", "constraint_records", "next_actions"
`answers.json` : {"<id>": "<answer-from-memory>", ...}

Exit codes: 0 PASS, 2 FAIL-HANDOFF, 1 usage/insufficient/IO/JSON error.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any


def _norm(value: object) -> str:
    """Whitespace/case-insensitive normalization for fuzzy comparison."""
    return " ".join(str(value).strip().lower().split())


def _similarity(truth: str, got: str) -> float:
    return difflib.SequenceMatcher(None, _norm(truth), _norm(got)).ratio()


def _matches_v2(truth: object, got: object, mode: str = "exact") -> bool:
    """Boolean match used only for v2 production anchors. match_mode controls text comparison."""
    if mode == "exact":
        return str(truth) == str(got)
    return _norm(truth) == _norm(got)


def _has_unknowns(v: Any) -> bool:
    """Recursively reject empty/UNKNOWN/unavailable/_error/malformed before any derivation."""
    if v is None:
        return True
    if isinstance(v, str):
        sl = v.strip().lower()
        return not sl or sl in {"unknown", "unavailable", "n/a", "none", "null", "missing"}
    if isinstance(v, (int, float, bool)):
        return False
    if isinstance(v, dict):
        if "_error" in v:
            return True
        return any(_has_unknowns(val) for val in v.values())
    if isinstance(v, list):
        return any(_has_unknowns(item) for item in v)
    return False


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


def _select_with_seed(items: list[Any], n: int, rng: random.Random) -> list[dict]:
    """Shuffle and take first n (or all if ==n) using provided seeded rng. Returns [] if insufficient."""
    if not isinstance(items, list) or len(items) < n:
        return []
    clean = [x for x in items if isinstance(x, dict)]
    if len(clean) < n:
        return []
    c = list(clean)
    rng.shuffle(c)
    return c[:n]


def _build_v2_anchors(sel_items: list[dict], category: str, text_key: str, q_tmpl: str) -> list[dict]:
    """Build exact shaped anchors or [] on any shape/unknown/empty failure for that batch."""
    anchors: list[dict] = []
    for rec in sel_items:
        if not isinstance(rec, dict):
            return []
        aid = rec.get("id")
        if not isinstance(aid, str) or not aid.strip() or _has_unknowns(aid):
            return []
        src_ref = rec.get("source_ref")
        if not isinstance(src_ref, str) or not src_ref.strip() or _has_unknowns(src_ref):
            return []
        a_val = (
            rec.get(text_key)
            or rec.get("text")
            or rec.get("statement")
            or rec.get("rationale")
            or rec.get("action")
            or rec.get("prohibition")
            or rec.get("a")
            or ""
        )
        if not str(a_val).strip() or _has_unknowns(str(a_val)):
            return []
        q = rec.get("q") or rec.get("question") or q_tmpl.format(id=aid)
        mm = rec.get("match_mode", "exact")
        if mm not in ("exact", "normalized"):
            return []
        anchors.append(
            {
                "id": aid,
                "q": str(q).strip(),
                "a": str(a_val).strip(),
                "category": category,
                "match_mode": mm,
                "source_ref": src_ref.strip(),
            }
        )
    return anchors


def cmd_mint(args: argparse.Namespace) -> int:
    snapshot_path = getattr(args, "snapshot", None)
    facts_spec = getattr(args, "facts", None)
    if snapshot_path and facts_spec:
        print("error: mint accepts only one of --snapshot or --facts, not both", file=sys.stderr)
        return 1
    try:
        if snapshot_path:
            snap = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            if not isinstance(snap, dict):
                print("error: --snapshot must be a JSON object", file=sys.stderr)
                return 1
            if _has_unknowns(snap):
                print(
                    "error: --snapshot contains UNKNOWN/unavailable or malformed values (rejected before derivation)",
                    file=sys.stderr,
                )
                return 1
            # Only pull from explicit durable handoff sections. Never git/monitor/github/SHAs etc.
            goals = snap.get("goals") or snap.get("handoff_goals") or []
            decs = snap.get("decision_records") or snap.get("decisions") or snap.get("decision_rationale_records") or []
            negs = (
                snap.get("constraint_records")
                or snap.get("constraints")
                or snap.get("negative_constraints")
                or snap.get("prohibitions")
                or []
            )
            nexts = snap.get("next_actions") or snap.get("queued_next_actions") or snap.get("actions") or []
            seed = snap.get("seed")
            if seed is None:
                # generate and persist a stable seed when absent (reproducible for same snapshot)
                snap_wo_seed = {k: v for k, v in snap.items() if k != "seed"}
                h = hashlib.sha256(json.dumps(snap_wo_seed, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                seed = int(h[:16], 16) & 0xFFFFFFFF
            else:
                try:
                    seed = int(seed)
                except Exception:
                    print("error: seed must be an integer", file=sys.stderr)
                    return 1
            rng = random.Random(seed)
            sel_g = _select_with_seed(goals, 3, rng)
            sel_d = _select_with_seed(decs, 3, rng)
            sel_n = _select_with_seed(negs, 2, rng)
            sel_na = _select_with_seed(nexts, 2, rng)
            if len(sel_g) != 3 or len(sel_d) != 3 or len(sel_n) != 2 or len(sel_na) != 2:
                print(
                    "error: insufficient evidence from durable handoff artifacts (need >=3 goals, 3 decision/rationale, 2 negative-constraint/prohibition, 2 next-action; no padding)",
                    file=sys.stderr,
                )
                return 1
            anchors: list[dict] = []
            for items, cat, tkey, qt in [
                (sel_g, "goal", "statement", "What is the goal '{id}' as of this handoff?"),
                (sel_d, "decision/rationale", "decision", "What is the decision/rationale '{id}' as of this handoff?"),
                (
                    sel_n,
                    "negative-constraint/prohibition",
                    "prohibition",
                    "What is the negative constraint/prohibition '{id}' as of this handoff?",
                ),
                (sel_na, "next-action", "action", "What is the next action '{id}' as of this handoff?"),
            ]:
                built = _build_v2_anchors(items, cat, tkey, qt)
                if len(built) != len(items):
                    print("error: malformed durable artifact record (id/source_ref/a/q or UNKNOWN)", file=sys.stderr)
                    return 1
                anchors.extend(built)
            id_set = {a["id"] for a in anchors}
            if len(id_set) != 10 or len(anchors) != 10:
                print("error: production anchors must have exactly 10 unique non-empty IDs", file=sys.stderr)
                return 1
            counts = {}
            for a in anchors:
                c = a["category"]
                counts[c] = counts.get(c, 0) + 1
            expected = {"goal": 3, "decision/rationale": 3, "negative-constraint/prohibition": 2, "next-action": 2}
            if counts != expected:
                print("error: wrong category composition for production v2", file=sys.stderr)
                return 1
            probe = {
                "version": "2",
                "schema": "production-handoff-v2",
                "lineage": snap.get("lineage") or snap.get("handoff_id") or "lineage:unknown",
                "source": "snapshot",
                "seed": seed,
                "generated_at": snap.get("generated_at"),
                "anchor_counts": expected,
                "strict_production": True,
                "policy": "strict-10/10-only-from-durable-continuity-artifacts",
                "anchors": anchors,
            }
            Path(args.out).write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"minted {len(anchors)} anchors -> {args.out}")
            return 0
        elif facts_spec:
            # LEGACY PATH - behavior and error messages identical to origin/main
            facts = _load_facts_spec(facts_spec)
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
        else:
            print("error: mint requires --snapshot (for production v2) or --facts (legacy)", file=sys.stderr)
            return 1
    except (OSError, UnicodeDecodeError) as exc:
        if snapshot_path:
            print(f"error: cannot read --snapshot: {snapshot_path} ({type(exc).__name__})", file=sys.stderr)
        else:
            print(f"error: --facts cannot be read as a file: {facts_spec} ({type(exc).__name__})", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        if snapshot_path:
            print(f"error: --snapshot is not valid JSON: {exc}", file=sys.stderr)
        else:
            print(f"error: --facts is not valid JSON: {exc}", file=sys.stderr)
        return 1


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

    anchors = probe.get("anchors", [])
    if not isinstance(anchors, list) or not anchors:
        print("error: probe has no anchors", file=sys.stderr)
        return 1

    is_v2_prod = bool(
        probe.get("version") == "2"
        and probe.get("schema") == "production-handoff-v2"
        and probe.get("strict_production") is True
        and len(anchors) == 10
        and probe.get("source") == "snapshot"
    )

    if is_v2_prod:
        # Strict validation for T1 confirmation: schema, provenance, categories, uniqueness, exact shape, source_ref
        seen: set[str] = set()
        cat_c: dict[str, int] = {
            "goal": 0,
            "decision/rationale": 0,
            "negative-constraint/prohibition": 0,
            "next-action": 0,
        }
        for a in anchors:
            if not isinstance(a, dict):
                print("error: v2 production anchor must be object", file=sys.stderr)
                return 1
            for req in ("id", "q", "a", "category", "match_mode", "source_ref"):
                val = a.get(req)
                if val is None or (isinstance(val, str) and not val.strip()):
                    print(f"error: v2 anchor missing/empty field: {req}", file=sys.stderr)
                    return 1
            aid = a["id"]
            if not isinstance(aid, str) or aid in seen:
                print(
                    "error: v2 anchors require unique non-empty string ids (exact match; do not normalize IDs)",
                    file=sys.stderr,
                )
                return 1
            seen.add(aid)
            cat = a["category"]
            if cat not in cat_c:
                print(f"error: invalid category {cat} for v2 production", file=sys.stderr)
                return 1
            cat_c[cat] += 1
            mm = a["match_mode"]
            if mm not in ("exact", "normalized"):
                print(f"error: invalid match_mode '{mm}' (supported: exact, normalized)", file=sys.stderr)
                return 1
            sr = a["source_ref"]
            if not isinstance(sr, str) or _has_unknowns(sr):
                print("error: v2 source_ref must be durable non-UNKNOWN artifact locator", file=sys.stderr)
                return 1
            if _has_unknowns(a.get("q")) or _has_unknowns(a.get("a")):
                print("error: v2 anchor q/a contains UNKNOWN value", file=sys.stderr)
                return 1
        if cat_c != {"goal": 3, "decision/rationale": 3, "negative-constraint/prohibition": 2, "next-action": 2}:
            print(
                "error: v2 probe must have exactly 3 goals, 3 decisions/rationales, 2 neg constraints, 2 next actions",
                file=sys.stderr,
            )
            return 1
        if (
            not probe.get("lineage")
            or probe.get("lineage") in ("lineage:unknown",)
            or _has_unknowns(probe.get("lineage"))
        ):
            print("error: v2 probe requires valid lineage/rollover identity from snapshot", file=sys.stderr)
            return 1

        # Strict 10/10 scoring. IDs matched exactly (answers.get uses raw id). match_mode only for text.
        correct = 0
        rows: list[tuple] = []
        for anchor in anchors:
            aid = anchor["id"]
            truth = anchor["a"]
            mm = anchor.get("match_mode", "exact")
            got = answers.get(aid, "") if isinstance(answers, dict) else ""
            ok = _matches_v2(truth, got, mm)
            if ok:
                correct += 1
            rows.append((aid, ok, anchor.get("q", ""), str(truth), str(got)))
        k = len(anchors)
        is_pass = correct == 10 and k == 10
        verdict = "PASS" if is_pass else "FAIL-HANDOFF"
        for aid, ok, q, truth, got in rows:
            tag = "PASS " if ok else "DRIFT"
            print(f"  [{tag}] {aid} {q}")
            if not ok:
                print(f"          truth: {truth!r}")
                print(f"          got  : {got!r}")
        print(f"SCORE {correct}/{k} = {correct / k:.3f}  ->  {verdict} (strict 10/10)")
        if args.log:
            log_path = Path(args.log)
            is_new = not log_path.exists()
            with log_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if is_new:
                    writer.writerow(["context_tokens", "model", "k", "correct", "score", "verdict"])
                writer.writerow(
                    [
                        getattr(args, "context_tokens", 0),
                        getattr(args, "model", "unknown"),
                        k,
                        correct,
                        f"{(correct / k):.3f}",
                        verdict,
                    ]
                )
        if getattr(args, "verdict", None):
            vpath = Path(args.verdict)
            vdata = {
                "version": "2",
                "schema": "production-handoff-v2",
                "lineage": probe.get("lineage"),
                "seed": probe.get("seed"),
                "k": k,
                "correct": correct,
                "score": round(correct / k, 3) if k else 0.0,
                "verdict": verdict,
                "context_tokens": getattr(args, "context_tokens", 0),
                "model": getattr(args, "model", "unknown"),
                "per_anchor": [{"id": r[0], "match": r[1]} for r in rows],
            }
            vpath.write_text(json.dumps(vdata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"verdict written -> {args.verdict}")
        return 0 if is_pass else 2
    else:
        # LEGACY scoring semantics (preserved exactly; do not weaken)
        correct = 0
        rows = []
        for anchor in anchors:
            aid = anchor.get("id", "")
            truth = anchor.get("a", "")
            got = answers.get(aid, "") if isinstance(answers, dict) else ""
            sim = _similarity(truth, got)
            thresh = getattr(args, "threshold", 0.75)
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
        pass_ratio = getattr(args, "pass_ratio", 0.85)
        verdict = "PASS" if score_val >= pass_ratio else "FAIL-HANDOFF"
        print(f"SCORE {correct}/{k} = {score_val:.2f}  ->  {verdict}")
        if args.log:
            log_path = Path(args.log)
            is_new = not log_path.exists()
            with log_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if is_new:
                    writer.writerow(["context_tokens", "model", "k", "correct", "score", "verdict"])
                writer.writerow(
                    [
                        getattr(args, "context_tokens", 0),
                        getattr(args, "model", "unknown"),
                        k,
                        correct,
                        f"{score_val:.3f}",
                        verdict,
                    ]
                )
        return 0 if verdict == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    mint = sub.add_parser(
        "mint",
        help="Freeze ground-truth anchors into a probe file. --facts for legacy three-anchor; --snapshot for strict production v2 10-anchor.",
    )
    mint.add_argument(
        "--snapshot",
        help="Path to structured durable handoff snapshot JSON (goals + decision_records + constraint_records + next_actions)",
    )
    mint.add_argument(
        "--facts", help="Legacy inline JSON list of {id,q,a}, or a path to a JSON file (original behavior)"
    )
    mint.add_argument("--out", required=True, help="Probe output path")
    mint.set_defaults(func=cmd_mint)

    score = sub.add_parser(
        "score",
        help="Diff from-memory answers against the frozen probe. Legacy: threshold+pass-ratio. v2: strict 10/10 + exact ID + match_mode per anchor.",
    )
    score.add_argument("--probe", required=True)
    score.add_argument("--answers", required=True, help="JSON {id: answer}")
    score.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Per-anchor similarity to count as recalled (legacy only, default 0.75)",
    )
    score.add_argument(
        "--pass-ratio", type=float, default=0.85, help="Fraction of anchors that must pass (legacy only, default 0.85)"
    )
    score.add_argument("--context-tokens", type=int, default=0, help="Context size at probe time (for the log)")
    score.add_argument("--model", default="unknown")
    score.add_argument("--log", help="CSV to append the (context_tokens, score) data point")
    score.add_argument(
        "--text-match",
        choices=["normalized", "exact"],
        default="normalized",
        help="Legacy only (v2 uses per-anchor match_mode; IDs always exact)",
    )
    score.add_argument("--verdict", help="Write machine-readable JSON verdict to this path")
    score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
