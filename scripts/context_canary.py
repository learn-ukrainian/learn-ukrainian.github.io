#!/usr/bin/env python3
"""Context-integrity canary — DETERMINISTIC brain-rot monitor using tool-backed snapshots.

Implements #5055 (under epic #5054): deterministic probe derivation from supplied
tool-backed snapshot; exactly 10 unique anchors with validated composition
(3 fact, 3 decision/rationale, 2 negative-constraint, 2 goal/next-action);
UNKNOWN/unavailable/non-tool-backed values excluded (insufficient evidence fails);
versioned metadata; strict 10/10 production scoring (rc 2 on drift);
exact normalized matching for identifiers + explicit normalized-text mode;
machine-readable JSON verdict; deterministic logging; complete focused tests.
Do not invent anchor answers — all ground truth comes from the snapshot.

Usage
-----
  .venv/bin/python scripts/context_canary.py mint --snapshot snapshot.json --out probe.json
  .venv/bin/python scripts/context_canary.py score --probe probe.json --answers answers.json \
      --context-tokens 500000 --model claude-opus-4-8 --log canary_log.csv [--verdict v.json] \
      [--text-match normalized]

`snapshot.json` : output of orchestration/thread_handoff.gather_snapshot (git + monitor + github sections)
`answers.json`  : {"<id>": "<answer-recalled-from-memory>", ...}

The SCRIPT (not the agent) computes pass/fail by normalized diff against frozen truth.
Only 10/10 normalized match under production rules yields PASS (rc 0); any drift -> rc 2 (handoff).

Exit codes: 0 PASS, 2 FAIL-HANDOFF, 1 usage/insufficient/IO/JSON error.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


def _norm(value: object) -> str:
    """Whitespace/case-insensitive normalization for exact normalized matching."""
    return " ".join(str(value).strip().lower().split())


def _matches(truth: object, got: object, mode: str = "normalized") -> bool:
    """Normalized (ws/case collapsed) or exact (byte-strict, no strip) text match."""
    if mode == "exact":
        return str(truth) == str(got)
    return _norm(truth) == _norm(got)


def _is_available(v: Any) -> bool:
    """True only for tool-backed, present, non-UNKNOWN/unavailable values.

    dicts with _error, None, empty-str after strip, and magic unknown tokens are excluded.
    Empty list (e.g. no modified files) is allowed (represents clean state).
    """
    if v is None:
        return False
    if isinstance(v, dict) and "_error" in v:
        return False
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True  # e.g. modified_files: [] is valid "clean"
    sv = str(v).strip()
    if not sv:
        return False
    sl = sv.lower()
    return sl not in {"unknown", "unavailable", "n/a", "none", "null"}


def _derive_probe_anchors(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministically derive anchors from tool-backed snapshot.

    Only includes values that pass _is_available (excludes non-tool-backed/UNKNOWN).
    Returns 0..N ; caller enforces exactly 10 + 3/3/2/2 composition.
    All "a" (answers) come from snapshot; never invented.
    """
    anchors: list[dict[str, Any]] = []
    git: dict[str, Any] = snapshot.get("git") or {}
    _ = snapshot.get("github") or {}  # present for future extension / snapshot fidelity; not used in derivation yet
    _ = snapshot.get("monitor") or {}  # present for future extension / snapshot fidelity; not used in derivation yet

    def get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
        cur: Any = d
        for k in keys:
            if isinstance(cur, dict):
                cur = cur.get(k, default)
            else:
                return default
        return cur if cur is not None else default

    last_commits: list[Any] = get(git, "last_commits") or []
    mod_files: list[Any] = get(git, "modified_files") or []
    ahead_behind: dict[str, Any] = get(git, "ahead_behind") or {}

    # 3 FACT
    fact_specs = [
        ("git_branch", "What is the git branch name from the tool-backed snapshot?"),
        ("git_head", "What is the short HEAD SHA from the tool-backed snapshot?"),
        ("git_modified_count", "Number of modified files reported in the tool-backed snapshot's git status?"),
    ]
    for cid, q in fact_specs:
        if sum(1 for a in anchors if a.get("category") == "fact") >= 3:
            break
        if cid == "git_branch":
            raw = get(git, "branch")
        elif cid == "git_head":
            raw = get(git, "head")
        else:
            raw = len(mod_files)
        if _is_available(raw) or raw == 0:
            anchors.append(
                {
                    "id": cid,
                    "category": "fact",
                    "q": q,
                    "a": str(raw).strip(),
                }
            )

    # 3 DECISION/RATIONALE (commit subjects = captured decisions/rationale)
    for i in range(3):
        if sum(1 for a in anchors if a.get("category") == "decision/rationale") >= 3:
            break
        if i < len(last_commits):
            entry = last_commits[i] if isinstance(last_commits[i], dict) else {}
            raw = entry.get("subject") if isinstance(entry, dict) else None
            if _is_available(raw):
                anchors.append(
                    {
                        "id": f"commit_{i}_subject",
                        "category": "decision/rationale",
                        "q": f"What is the subject of commit index {i} (0=most recent) in the tool-backed snapshot (captures decision/rationale)?",
                        "a": str(raw).strip(),
                    }
                )

    # 2 NEGATIVE-CONSTRAINT
    neg_specs = [
        (
            "git_modified_status",
            "The git status --short summary from the snapshot (''/clean encodes negative constraint: no uncommitted changes at mint)?",
            lambda: (
                ";".join(f"{m.get('status', '')}{m.get('path', '')}" for m in mod_files if isinstance(m, dict))
                or "clean"
            ),
        ),
        (
            "ahead_count",
            "The 'ahead' count vs upstream from snapshot (0 encodes negative constraint of no pending divergence)?",
            lambda: get(ahead_behind, "ahead"),
        ),
    ]
    for cid, q, getter in neg_specs:
        if sum(1 for a in anchors if a.get("category") == "negative-constraint") >= 2:
            break
        raw = getter()
        if _is_available(raw) or raw in (0, "0"):
            av = "0" if raw in (0, "0") else str(raw).strip()
            if _is_available(av) or av == "0":
                anchors.append(
                    {
                        "id": cid,
                        "category": "negative-constraint",
                        "q": q,
                        "a": av,
                    }
                )

    # 2 GOAL/NEXT-ACTION
    goal_specs = [
        (
            "head_sha_next_ref",
            "HEAD SHA from snapshot (base reference for goal/next-action state at mint)?",
            lambda: get(git, "head") or get(git, "full_head"),
        ),
        (
            "recent_commit_sha_goal",
            "Most recent commit SHA from snapshot (advancement reference for goals)?",
            lambda: last_commits[0].get("sha") if last_commits and isinstance(last_commits[0], dict) else None,
        ),
    ]
    for cid, q, getter in goal_specs:
        if sum(1 for a in anchors if a.get("category") == "goal/next-action") >= 2:
            break
        raw = getter()
        if _is_available(raw):
            anchors.append(
                {
                    "id": cid,
                    "category": "goal/next-action",
                    "q": q,
                    "a": str(raw).strip(),
                }
            )

    return anchors


def _load_facts_spec(spec: str) -> object:
    """Legacy support for --facts (inline or path)."""
    if spec.lstrip()[:1] in ("[", "{"):
        return json.loads(spec)
    return json.loads(Path(spec).read_text(encoding="utf-8"))


def cmd_mint(args: argparse.Namespace) -> int:
    snapshot_path = getattr(args, "snapshot", None)
    facts_spec = getattr(args, "facts", None)
    try:
        if snapshot_path:
            snap = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            if not isinstance(snap, dict):
                print("error: --snapshot must be a JSON object", file=sys.stderr)
                return 1
            anchors = _derive_probe_anchors(snap)
            counts = {
                c: sum(1 for a in anchors if a.get("category") == c)
                for c in ("fact", "decision/rationale", "negative-constraint", "goal/next-action")
            }
            if len(anchors) != 10 or counts != {
                "fact": 3,
                "decision/rationale": 3,
                "negative-constraint": 2,
                "goal/next-action": 2,
            }:
                print(
                    "error: insufficient evidence from tool-backed snapshot (UNKNOWN/unavailable/non-tool-backed excluded; need validated 3 fact, 3 decision/rationale, 2 negative-constraint, 2 goal/next-action)",
                    file=sys.stderr,
                )
                return 1
            probe = {
                "version": "1",
                "source": "snapshot",
                "generated_at": snap.get("generated_at"),
                "anchor_counts": counts,
                "anchors": anchors,
            }
        elif facts_spec:
            facts = _load_facts_spec(facts_spec)
            if not isinstance(facts, list) or not facts:
                print("error: --facts must be a non-empty JSON list of {id,q,a}", file=sys.stderr)
                return 1
            ids = [f.get("id") for f in facts]
            if len(set(ids)) != len(ids) or not all(ids):
                print("error: every fact needs a unique non-empty 'id'", file=sys.stderr)
                return 1
            anchors = [{"id": f["id"], "q": f["q"], "a": f["a"]} for f in facts]
            probe = {"version": "1", "source": "facts", "anchors": anchors}
        else:
            print("error: mint requires --snapshot (for 10-anchor derivation) or --facts", file=sys.stderr)
            return 1
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: input is not valid JSON: {exc}", file=sys.stderr)
        return 1

    Path(args.out).write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"minted {len(anchors)} anchors -> {args.out}")
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

    anchors = probe.get("anchors", [])
    if not isinstance(anchors, list) or len(anchors) != 10:
        print(
            f"error: probe must have exactly 10 anchors (got {len(anchors) if isinstance(anchors, list) else 0}); derive via --snapshot for production canary",
            file=sys.stderr,
        )
        return 1

    # exact normalized matching for identifiers
    id_map: dict[str, dict[str, Any]] = {}
    for a in anchors:
        nid = _norm(a.get("id", ""))
        if nid:
            id_map[nid] = a

    text_mode = getattr(args, "text_match", "normalized")
    correct = 0
    rows: list[tuple[str, bool, str, str, str]] = []
    for anchor in anchors:
        aid = anchor.get("id", "")
        truth = anchor.get("a", "")
        nid = _norm(aid)
        got: Any = ""
        if isinstance(answers, dict):
            for ak, av in answers.items():
                if _norm(ak) == nid:
                    got = av
                    break
        ok = _matches(truth, got, text_mode)
        if ok:
            correct += 1
        rows.append((aid, ok, str(anchor.get("q", "")), str(truth), str(got)))

    k = len(anchors)
    # strict 10/10 production scoring
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
            "version": probe.get("version", "1"),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    mint = sub.add_parser(
        "mint", help="Derive deterministic 10-anchor probe from tool-backed snapshot (or legacy facts)."
    )
    mint.add_argument(
        "--snapshot",
        help="Path to tool-backed snapshot JSON (git/monitor/github); derives exactly 10 anchors with categories",
    )
    mint.add_argument("--facts", help="Legacy inline JSON list or path to [{id,q,a},...] (for non-production)")
    mint.add_argument("--out", required=True, help="Probe output path")
    mint.set_defaults(func=cmd_mint)

    score = sub.add_parser(
        "score", help="Diff answers vs probe (normalized id match + configurable text match). Strict 10/10 rc=2."
    )
    score.add_argument("--probe", required=True)
    score.add_argument("--answers", required=True, help="JSON object {id: recalled-answer}")
    score.add_argument("--context-tokens", type=int, default=0, help="Context size for the log row")
    score.add_argument("--model", default="unknown")
    score.add_argument("--log", help="Append deterministic row to this CSV")
    score.add_argument(
        "--text-match",
        choices=["normalized", "exact"],
        default="normalized",
        help="normalized (default): ignore ws/case; exact: strict string",
    )
    score.add_argument("--verdict", help="Write machine-readable JSON verdict to this path")
    score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
