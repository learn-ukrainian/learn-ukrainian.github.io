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
import datetime as dt
import difflib
import hashlib
import json
import random
import re
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


# --- Explicit, closed, centralized source_ref grammar and category/kind mapping (per review requirements) ---
# Grammar: kind:repo-relative-path#record-fragment
# Reject: git:, github:, monitor:, arbitrary strings, absolute paths, traversal (..), missing : or #, UNKNOWN, wrong roots.
# Category must map to appropriate kind(s); no inference from answer text.
SOURCE_REF_GRAMMAR = "kind:repo-relative-path#record-fragment"
ALLOWED_KIND_ROOTS: dict[str, tuple[str, ...]] = {
    "handoff": (".agent/thread-rollovers/", "docs/session-state/"),
    "decision": ("docs/decisions/",),
    "pending-decision": ("docs/decisions/",),
    "queue": ("batch_state/orchestrator-runs/",),
}
CATEGORY_KIND_ALLOW: dict[str, tuple[str, ...]] = {
    # goals from handoff
    "goal": ("handoff",),
    # decisions/rationales from decision or handoff (or pending-decision)
    "decision/rationale": ("decision", "pending-decision", "handoff"),
    # constraints/prohibitions from handoff or decision
    "negative-constraint/prohibition": ("handoff", "decision", "pending-decision"),
    # next actions from queue or handoff
    "next-action": ("queue", "handoff"),
}


def _parse_and_validate_source_ref(source_ref: object, category: str) -> bool:
    """Closed validator used identically at mint and score. Returns False on any violation."""
    if not isinstance(source_ref, str):
        return False
    sr = source_ref.strip()
    if not sr or _has_unknowns(sr):
        return False
    if sr.count(":") != 1 or sr.count("#") != 1:
        return False
    try:
        kind, rest = sr.split(":", 1)
        if "#" not in rest:
            return False
        path_part, frag = rest.rsplit("#", 1)
    except ValueError:
        return False
    if not kind or not path_part or not frag:
        return False
    # reject traversal, absolute, weird relatives
    if ".." in path_part or path_part.startswith("/") or path_part.startswith("~"):
        return False
    if kind not in ALLOWED_KIND_ROOTS:
        return False
    roots = ALLOWED_KIND_ROOTS[kind]
    if not any(path_part.startswith(root) for root in roots):
        return False
    allowed_for_cat = CATEGORY_KIND_ALLOW.get(category, ())
    return kind in allowed_for_cat


def _validate_utc_timestamp(v: object) -> bool:
    """Require real UTC timestamp (Z or +00:00 offset)."""
    if not isinstance(v, str):
        return False
    s = v.strip()
    if not s:
        return False
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            return False
        return d.utcoffset() == dt.timedelta(0)
    except Exception:
        return False


def _validate_identity(val: object, kind: str) -> bool:
    """Centralized, closed identity validator aligned with the handoff engine.

    - lineage_id: prefix 'lineage-' + 1+ lowercase alnum/hyphen, total len <=64
    - rollover_id: prefix 'rollover-' + 1+ lowercase alnum/hyphen, total len <=64
    - Full-string match only. Exact raw strings (NO normalization, NO strip, NO casefold).
    - Rejects leading/trailing ws, any ws/control/newline, uppercase, wrong prefix,
      punctuation (except hyphen), / \\ . .. traversal, empty suffix, overlong (>64).
    - Also rejects consecutive path syntax (e.g. '--', '//').
    Applied uniformly to: snapshot mint input, production probe validation at score,
    and --expected-lineage-id/--expected-rollover-id (before any exact == comparison).
    """
    if not isinstance(val, str):
        return False
    # Reject leading/trailing whitespace on the raw value (no normalization performed)
    if val != val.strip():
        return False
    # Reject embedded control chars, newlines, tabs, DEL etc.
    if any(ord(c) < 32 or ord(c) == 127 for c in val):
        return False
    if not val or _has_unknowns(val):
        return False
    if len(val) > 64:
        return False
    if kind == "lineage":
        if not re.fullmatch(r"lineage-[a-z0-9-]+", val):
            return False
    elif kind == "rollover":
        if not re.fullmatch(r"rollover-[a-z0-9-]+", val):
            return False
    else:
        return False
    # Reject consecutive path syntax
    return not ("--" in val or "//" in val or "\\\\" in val or ".." in val or val.endswith("-"))


def _is_exact_legacy_anchors_only(probe: object) -> bool:
    """Legacy probes are ONLY the exact original shape produced by --facts: {"anchors": [{"id":, "q":, "a":}, ...]}.
    Any production marker or extra top-level key forces strict v2 path (and fail if incomplete).
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
    """Build exact shaped anchors or [] on any shape/unknown/empty failure for that batch.
    source_ref validated with closed grammar + category mapping (identical at mint/score).
    """
    anchors: list[dict] = []
    for rec in sel_items:
        if not isinstance(rec, dict):
            return []
        aid = rec.get("id")
        if not isinstance(aid, str) or not aid.strip() or _has_unknowns(aid):
            return []
        src_ref = rec.get("source_ref")
        if not _parse_and_validate_source_ref(src_ref, category):
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
        if not str(q).strip() or _has_unknowns(str(q)):
            return []
        mm = rec.get("match_mode", "exact")
        if mm not in ("exact", "normalized"):
            return []
        anchors.append(
            {
                "id": aid.strip(),
                "q": str(q).strip(),
                "a": str(a_val).strip(),
                "category": category,
                "match_mode": mm,
                "source_ref": str(src_ref).strip(),
            }
        )
    return anchors


def cmd_mint(args: argparse.Namespace) -> int:
    snapshot_path = getattr(args, "snapshot", None)
    facts_spec = getattr(args, "facts", None)
    # Note: both/missing now enforced by mutually_exclusive_group(required=True) -> parser rc 2
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
            # Require explicit complete identity; never synthesize unknown.
            # Use centralized closed validator (exact raw, no normalization) for both.
            lineage_id = snap.get("lineage_id")
            rollover_id = snap.get("rollover_id")
            if not _validate_identity(lineage_id, "lineage"):
                print(
                    "error: --snapshot requires well-formed lineage_id (prefix lineage-[a-z0-9-]+ <=64 chars, exact no ws/upper/punct/slash/control/empty-suffix/overlong)",
                    file=sys.stderr,
                )
                return 1
            if not _validate_identity(rollover_id, "rollover"):
                print(
                    "error: --snapshot requires well-formed rollover_id (prefix rollover-[a-z0-9-]+ <=64 chars, exact no ws/upper/punct/slash/control/empty-suffix/overlong)",
                    file=sys.stderr,
                )
                return 1
            if not _validate_utc_timestamp(snap.get("generated_at")):
                print(
                    "error: --snapshot requires generated_at as a real UTC timestamp (e.g. 2026-07-13T12:00:00Z)",
                    file=sys.stderr,
                )
                return 1
            # Only pull from explicit durable sections. source_ref validated per grammar+cat.
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
                    print(
                        "error: malformed durable artifact record (id/source_ref/a/q or UNKNOWN or bad source_ref grammar/category)",
                        file=sys.stderr,
                    )
                    return 1
                anchors.extend(built)
            id_set = {a["id"] for a in anchors}
            if len(id_set) != 10 or len(anchors) != 10:
                print("error: production anchors must have exactly 10 unique non-empty IDs", file=sys.stderr)
                return 1
            counts: dict[str, int] = {}
            for a in anchors:
                c = a["category"]
                counts[c] = counts.get(c, 0) + 1
            expected = {"goal": 3, "decision/rationale": 3, "negative-constraint/prohibition": 2, "next-action": 2}
            if counts != expected:
                print("error: wrong category composition for production v2", file=sys.stderr)
                return 1
            # Exact metadata keys, no more no less; store explicit lineage_id + rollover_id
            probe = {
                "version": "2",
                "schema": "production-handoff-v2",
                "source": "snapshot",
                "lineage_id": lineage_id,
                "rollover_id": rollover_id,
                "seed": seed,
                "generated_at": snap.get("generated_at").strip(),
                "anchor_counts": expected,
                "strict_production": True,
                "policy": "strict-10/10-only-from-durable-continuity-artifacts",
                "anchors": anchors,
            }
            if _has_unknowns(probe):
                print("error: produced probe contains UNKNOWN after validation", file=sys.stderr)
                return 1
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
            # Should not reach due to group, but keep for safety
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

    if not isinstance(probe, dict):
        print("error: probe must be a JSON object", file=sys.stderr)
        return 1
    anchors = probe.get("anchors", [])
    if not isinstance(anchors, list) or not anchors:
        print("error: probe has no anchors", file=sys.stderr)
        return 1

    # Partial/forged production markers or extra keys MUST fail closed, never fallback to legacy.
    # Legacy = ONLY the exact anchors-only shape {"anchors": [{"id":str,"q":str,"a":str}, ...]} from --facts.
    if _is_exact_legacy_anchors_only(probe):
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
    else:
        # Strict v2 production path: exact metadata, exact anchor keys, source_ref grammar+cat, identity, expected match.
        # Any production marker or extra top key routes here and fails if not complete/valid.
        required_keys = {
            "version",
            "schema",
            "source",
            "lineage_id",
            "rollover_id",
            "seed",
            "generated_at",
            "anchor_counts",
            "strict_production",
            "policy",
            "anchors",
        }
        if set(probe.keys()) != required_keys:
            print(
                "error: production probe must have exactly these top-level keys with no missing/extra: version,schema,source,lineage_id,rollover_id,seed,generated_at,anchor_counts,strict_production,policy,anchors",
                file=sys.stderr,
            )
            return 2
        if probe.get("version") != "2":
            print('error: production probe version must be "2"', file=sys.stderr)
            return 2
        if probe.get("schema") != "production-handoff-v2":
            print("error: production probe schema must be production-handoff-v2", file=sys.stderr)
            return 2
        if probe.get("source") != "snapshot":
            print("error: production probe source must be snapshot", file=sys.stderr)
            return 2
        if probe.get("strict_production") is not True:
            print("error: production probe strict_production must be true", file=sys.stderr)
            return 2
        if probe.get("policy") != "strict-10/10-only-from-durable-continuity-artifacts":
            print("error: production probe policy must be exact", file=sys.stderr)
            return 2
        seed = probe.get("seed")
        if not isinstance(seed, int):
            print("error: production probe seed must be an integer", file=sys.stderr)
            return 2
        if not _validate_utc_timestamp(probe.get("generated_at")):
            print("error: production probe generated_at must be a real UTC timestamp", file=sys.stderr)
            return 2
        expected_counts = {"goal": 3, "decision/rationale": 3, "negative-constraint/prohibition": 2, "next-action": 2}
        if probe.get("anchor_counts") != expected_counts:
            print("error: production probe anchor_counts must be exact 3/3/2/2", file=sys.stderr)
            return 2

        # anchors: exact keys + values validated recursively + source_ref closed
        anchors = probe["anchors"]
        if not isinstance(anchors, list) or len(anchors) != 10:
            print("error: production probe must have exactly 10 anchors", file=sys.stderr)
            return 2
        anchor_keys = {"id", "q", "a", "category", "match_mode", "source_ref"}
        seen: set[str] = set()
        cat_c: dict[str, int] = {
            "goal": 0,
            "decision/rationale": 0,
            "negative-constraint/prohibition": 0,
            "next-action": 0,
        }
        for a in anchors:
            if not isinstance(a, dict) or set(a.keys()) != anchor_keys:
                print(
                    "error: each production anchor must have exactly keys {id,q,a,category,match_mode,source_ref} (no missing/extra)",
                    file=sys.stderr,
                )
                return 2
            for req in ("id", "q", "a", "category", "match_mode", "source_ref"):
                val = a.get(req)
                if val is None or (isinstance(val, str) and not val.strip()) or _has_unknowns(val):
                    print(f"error: production anchor missing/empty/UNKNOWN field: {req}", file=sys.stderr)
                    return 2
            aid = a["id"]
            if not isinstance(aid, str) or not aid.strip() or aid in seen:
                print(
                    "error: v2 anchors require unique non-empty string ids (exact match; do not normalize IDs)",
                    file=sys.stderr,
                )
                return 2
            seen.add(aid)
            cat = a["category"]
            if cat not in cat_c:
                print(f"error: invalid category {cat} for v2 production", file=sys.stderr)
                return 2
            cat_c[cat] += 1
            mm = a["match_mode"]
            if mm not in ("exact", "normalized"):
                print(f"error: invalid match_mode '{mm}' (supported: exact, normalized)", file=sys.stderr)
                return 2
            sr = a["source_ref"]
            if not _parse_and_validate_source_ref(sr, cat):
                print(
                    "error: v2 source_ref must follow kind:repo-relative-path#record-fragment with allowed kinds/roots for its category; reject git:,github:,monitor:,abs,../,arbitrary,wrong-pair,UNKNOWN",
                    file=sys.stderr,
                )
                return 2
        if cat_c != expected_counts:
            print(
                "error: v2 probe must have exactly 3 goals, 3 decisions/rationales, 2 neg constraints, 2 next actions",
                file=sys.stderr,
            )
            return 2

        # Require explicit lineage_id + rollover_id (no unknown). Use centralized validator, exact raw.
        lid = probe.get("lineage_id")
        rid = probe.get("rollover_id")
        if not _validate_identity(lid, "lineage"):
            print("error: v2 probe requires well-formed lineage_id (exact identity)", file=sys.stderr)
            return 2
        if not _validate_identity(rid, "rollover"):
            print("error: v2 probe requires well-formed rollover_id (exact identity)", file=sys.stderr)
            return 2

        # Production score REQUIRES caller-supplied expected ids and exact match before any scoring.
        # Validate with same centralized closed validator (exact raw) BEFORE the == comparison.
        exp_lid = getattr(args, "expected_lineage_id", None)
        exp_rid = getattr(args, "expected_rollover_id", None)
        if not _validate_identity(exp_lid, "lineage"):
            print("error: production score requires --expected-lineage-id (well-formed identity)", file=sys.stderr)
            return 2
        if not _validate_identity(exp_rid, "rollover"):
            print("error: production score requires --expected-rollover-id (well-formed identity)", file=sys.stderr)
            return 2
        if exp_lid != lid or exp_rid != rid:
            print(
                "error: --expected-lineage-id and --expected-rollover-id must exactly match probe identity",
                file=sys.stderr,
            )
            return 2

        # Strict 10/10 scoring. IDs matched exactly. match_mode only for text.
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
            # Stable SHA-256 of the validated probe (canonical form)
            canonical = json.dumps(probe, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            probe_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            vdata = {
                "version": "2",
                "schema": "production-handoff-v2",
                "lineage_id": lid,
                "rollover_id": rid,
                "probe_sha256": probe_sha256,
                "seed": seed,
                "k": k,
                "correct": correct,
                "score": round(correct / k, 3) if k else 0.0,
                "verdict": verdict,
                "model": getattr(args, "model", "unknown"),
                "per_anchor": [{"id": r[0], "match": r[1]} for r in rows],
                # context_tokens removed (was duplicate; not part of binding identity+probe content)
            }
            vpath.write_text(json.dumps(vdata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"verdict written -> {args.verdict}")
        return 0 if is_pass else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    mint = sub.add_parser(
        "mint",
        help="Freeze ground-truth anchors into a probe file. --facts for legacy three-anchor; --snapshot for strict production v2 10-anchor.",
    )
    # Use mutually_exclusive_group(required=True) so missing both or supplying both yield parser rc 2
    # (matches origin/main's --facts required behavior for usage errors).
    mint_src = mint.add_mutually_exclusive_group(required=True)
    mint_src.add_argument(
        "--snapshot",
        help="Path to structured durable handoff snapshot JSON (goals + decision_records + constraint_records + next_actions). Requires lineage_id, rollover_id, UTC generated_at, and valid source_ref per grammar.",
    )
    mint_src.add_argument(
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
    # Production v2 identity (caller-supplied, required+matched exactly in v2 path before scoring; optional in parser to preserve legacy CLI calls)
    score.add_argument(
        "--expected-lineage-id", help="Required for v2 production probes: must exactly match probe lineage_id"
    )
    score.add_argument(
        "--expected-rollover-id", help="Required for v2 production probes: must exactly match probe rollover_id"
    )
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
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse usage errors (e.g. missing required mutually_exclusive_group for mint, or both) must surface as rc 2
        # so tests can assert parser rc 2 while CLI still exits 2. Func returns are normal.
        if isinstance(getattr(exc, "code", None), int):
            return exc.code
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
