"""The fix loop (#8430 r4): layer assignment, budgets, dependency closure, the module verdict.

Reads the findings database (``scripts.review.findings_db``), the engine's provenance file
``lesson-<n>.provenance.yaml`` and closure file ``module.closure.yaml``, and prints a
report for the driver. It performs no repair and takes no automatic branch:

* **Layer of a finding** — from provenance, never from substrings. A defective span the
  engine printed from a record is that record's layer (``pack`` or ``word_store``), except
  the ``incorrect`` side of an ``E-`` record and a writer-typed distractor
  (``option_origin: writer_typed`` with ``is_key: false``), which are defective by design
  and never blamed (layer ``not_blamed``). ``plan_defect`` -> ``plan``; ``evidence_gap`` ->
  ``pack_builder``; ``engine_or_gate`` -> ``engine``; writer prose or an absence finding ->
  ``regenerate_lesson``; several layers implicated -> ``mixed``; a location provenance cannot
  place -> ``unlocated`` (the driver decides).
* **Signal** — the same ``dimension`` + ``sub_dimension`` in two or more lessons of a module.
  Printed; the driver decides whether the style card or the prompt is the cause.
* **Budgets** — counted against ``(level, slug, lesson n)`` in the database, so a change of
  plan, pack, card or prompt never resets them. Every terminal path is named ``operator``.
* **Closure** — regenerating lesson k makes lessons k+1..N (the recap included) stale.
* **Module verdict** — ``module-verdict.yaml``, computed from the lesson verdicts of record,
  the open settle items and the plan's promotion state. A module with an open settle item
  is never APPROVE.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import plan_manifest as pm
from scripts.build.fresh.manifest import changed_inputs
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lock
from scripts.review import findings_db
from scripts.review.validate.validate import fold_quote

REPO_ROOT = Path(__file__).resolve().parents[2]
TREE = "curriculum/l2-uk-en"
PROVENANCE_SCHEMA = REPO_ROOT / "schemas" / "lesson-provenance-v1.schema.json"
CLOSURE_SCHEMA = REPO_ROOT / "schemas" / "module-closure-v1.schema.json"
LIVE_STATUSES = frozenset({"active", "persisting"})

# Layers (see the module docstring).
PACK, WORD_STORE, PLAN, PACK_BUILDER, ENGINE = "pack", "word_store", "plan", "pack_builder", "engine"
REGENERATE, MIXED, NOT_BLAMED, UNLOCATED = "regenerate_lesson", "mixed", "not_blamed", "unlocated"
RECORD_LAYER = {
    "word": WORD_STORE,
    "quote": PACK,
    "example": PACK,
    "exercise_text": PACK,
    "error": PACK,
    "note": PACK,
    "video": PACK,
    "resource": PACK,
}

# Terminal transitions: every path ends at the operator.
TERMINAL = "operator"
REASON_REVISE = "revise_budget_exhausted"
REASON_REGENERATIONS = "regeneration_budget_exhausted"
REASON_REVIEW_FAILURE = "review_failure_after_fallback"
REASON_SETTLE = "settle_needs_operator"
REASON_UNSUPPORTED_LESSONS = "unsupported_claim_in_three_lessons"
REASON_DISPUTED = "verdict_disputed"

MODULE_VERDICT_NAME = "module-verdict.yaml"
MODULE_VERDICT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Fresh module verdict (computed by scripts.review.fixloop)",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "module_verdict_schema",
        "level",
        "slug",
        "verdict",
        "computed_at",
        "plan",
        "lessons",
        "settle_items",
        "holds",
        "terminal",
    ],
    "properties": {
        "module_verdict_schema": {"const": 1},
        "level": {"type": "string", "minLength": 1},
        "slug": {"type": "string", "minLength": 1},
        "verdict": {"enum": ["APPROVE", "REVISE", "HOLD"]},
        "computed_at": {"type": "string", "minLength": 1},
        "plan": {"type": "object", "required": ["state"], "properties": {"state": {"type": "string"}}},
        "lessons": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["n", "kind", "state", "verdict", "attempt_id", "manifest_sha256", "validated_at", "stale"],
                "properties": {
                    "n": {"type": "integer", "minimum": 1},
                    "kind": {"enum": ["lesson", "recap"]},
                    "state": {"enum": ["current", "stale", "unreviewed"]},
                    "verdict": {"enum": ["APPROVE", "REVISE", None]},
                    "attempt_id": {"type": ["string", "null"]},
                    "manifest_sha256": {"type": ["string", "null"]},
                    "validated_at": {"type": ["string", "null"]},
                    "stale": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "settle_items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["open", "waiting_for_operator", "supported_defect_pending"],
            "properties": {
                key: {"type": "array", "items": {"type": "object"}}
                for key in ("open", "waiting_for_operator", "supported_defect_pending")
            },
        },
        "holds": {"type": "array", "items": {"type": "object", "required": ["code", "detail"]}},
        "terminal": {"type": "array", "items": {"type": "object", "required": ["transition", "reason"]}},
    },
}


class FixLoopError(Exception):
    """The loop cannot be computed (missing plan, unreadable closure, a budget that forbids the step)."""


class ProvenanceError(FixLoopError):
    """A provenance file is missing or does not conform to lesson-provenance-v1."""


class TerminalTransition(FixLoopError):
    """A budget is spent: the module goes to the operator instead of another round."""

    def __init__(self, reason: str, detail: str) -> None:
        self.reason, self.detail = reason, detail
        super().__init__(f"{TERMINAL}: {reason}: {detail}")


# --- paths --------------------------------------------------------------------------------


def state_dir(root: Path, level: str, slug: str) -> Path:
    return pm.state_dir(Path(root).resolve(), level, slug)


def plan_lessons(root: Path, level: str, slug: str) -> list[dict[str, Any]]:
    """The module's lessons (``n`` and ``kind``) as its plan lists them."""
    path = Path(root).resolve() / TREE / "lesson-plans" / level / f"{slug}.yaml"
    try:
        plan = yaml.safe_load(path.read_bytes())
        lessons = plan["lessons"]
        return [{"n": int(item["n"]), "kind": "recap" if item.get("kind") == "recap" else "lesson"} for item in lessons]
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as error:
        raise FixLoopError(f"the plan of {level}/{slug} is unreadable: {error}") from error


# --- layer assignment -----------------------------------------------------------------------


def load_provenance(directory: Path, n: int) -> dict[str, Any]:
    """``lesson-<n>.provenance.yaml`` validated against its schema; ProvenanceError when it is not usable."""
    path = Path(directory) / f"lesson-{n}.provenance.yaml"
    try:
        document = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as error:
        raise ProvenanceError(f"{path.name} is unreadable: {error}") from error
    schema = json.loads(PROVENANCE_SCHEMA.read_text(encoding="utf-8"))
    problems = [error.message for error in Draft202012Validator(schema).iter_errors(document)]
    if problems:
        raise ProvenanceError(f"{path.name} does not conform to lesson-provenance-v1: {problems[0]}")
    return document


def span_layer(span: dict[str, Any]) -> str:
    """The layer one provenance span is blamed on; ``not_blamed`` for a span that is defective by design."""
    if span.get("record_side") == "incorrect":
        return NOT_BLAMED
    if span.get("option_origin") == "writer_typed" and span.get("is_key") is False:
        return NOT_BLAMED
    if span["source"] == "record":
        return RECORD_LAYER[span["record_kind"]]
    return REGENERATE


def _unit_texts(provenance: dict[str, Any]) -> dict[tuple, list[dict[str, Any]]]:
    units: dict[tuple, list[dict[str, Any]]] = {}
    for span in provenance["spans"]:
        key = (span["tab"], span["step"], span["activity"], span["item"], span["block"])
        units.setdefault(key, []).append(span)
    for spans in units.values():
        spans.sort(key=lambda item: item["span"])
    return units


def _spans_of_quote(units: dict[tuple, list[dict[str, Any]]], location: dict[str, Any]) -> list[dict[str, Any]]:
    """Every provenance span a location's quote overlaps, across the units the location names."""
    quote = fold_quote(location["quote"])
    found: list[dict[str, Any]] = []
    for key, spans in units.items():
        if key[0] != location.get("tab"):
            continue
        if "activity" in location and key[2] != location["activity"]:
            continue
        if "item" in location and key[3] != location["item"]:
            continue
        text, owners = "", []
        for index, span in enumerate(spans):
            folded = fold_quote(span["text"])
            text += folded
            owners.extend([index] * len(folded))
        start = text.find(quote)
        while start != -1:
            for index in sorted(set(owners[start : start + len(quote)])):
                if spans[index] not in found:
                    found.append(spans[index])
            start = text.find(quote, start + 1)
    return found


def layer_for_finding(finding: dict[str, Any], provenance: dict[str, Any] | None, *, kind: str) -> str | None:
    """The layer a finding is fixed at (None for a resolved finding, which is history).

    ``provenance`` is the lesson's provenance document, or None when it cannot be used, in
    which case a finding that depends on provenance is ``unlocated``.
    """
    if finding["status"] not in LIVE_STATUSES:
        return None
    dimension = finding["dimension"]
    if dimension == "evidence_gap":
        return PACK_BUILDER
    if dimension == "plan_defect" or kind == "plan":
        return PLAN
    if dimension == "engine_or_gate":
        return ENGINE
    locations = finding.get("locations") or []
    if not locations:
        return REGENERATE  # an absence: the lesson lacks something its writer owed
    if provenance is None:
        return UNLOCATED
    units = _unit_texts(provenance)
    spans = [span for location in locations for span in _spans_of_quote(units, location)]
    if not spans:
        return UNLOCATED
    layers = {span_layer(span) for span in spans}
    blamed = layers - {NOT_BLAMED}
    if not blamed:
        return NOT_BLAMED
    return next(iter(blamed)) if len(blamed) == 1 else MIXED


# --- the signal, the gate list and the level-wide claim count ----------------------------------


def same_dimension_signal(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """``dimension`` + ``sub_dimension`` pairs found in two or more lessons of the module's live findings."""
    lessons: dict[tuple[str, str], set[int]] = {}
    for row in rows:
        if row["kind"] != "lesson" or row["status"] not in LIVE_STATUSES or row["lesson_n"] is None:
            continue
        lessons.setdefault((row["dimension"], row["sub_dimension"] or ""), set()).add(row["lesson_n"])
    return [
        {"dimension": dimension, "sub_dimension": sub or None, "lessons": sorted(found)}
        for (dimension, sub), found in sorted(lessons.items())
        if len(found) >= 2
    ]


def gate_candidates(rows: list[sqlite3.Row], pattern: str) -> list[dict[str, Any]]:
    """Live findings whose ``could_be_a_gate`` matches ``pattern`` (the schema's ``^yes .+$``), for the driver to file."""
    matcher = re.compile(pattern)
    return [
        {
            "finding_ref": findings_db.finding_ref(row["review_id"], row["attempt_id"], row["finding_id"]),
            "lesson_n": row["lesson_n"],
            "dimension": row["dimension"],
            "could_be_a_gate": row["could_be_a_gate"],
        }
        for row in rows
        if row["status"] in LIVE_STATUSES and row["could_be_a_gate"] and matcher.search(row["could_be_a_gate"])
    ]


def unsupported_claim_counts(conn: sqlite3.Connection, level_threshold: int) -> list[dict[str, Any]]:
    """Unsupported claims that recur across lessons of the level, keyed by dimension, sub-dimension and quote.

    A claim's identity is its dimension, sub-dimension and the first located quote (folded);
    an absence finding is keyed by its claim text. ``to_operator`` is set at the threshold.
    """
    rows = conn.execute(
        "SELECT f.finding_json, a.slug, a.lesson_n FROM findings f JOIN attempts a"
        " ON a.review_id = f.review_id AND a.attempt_id = f.attempt_id"
        " WHERE f.evidence_kind = 'unsupported_by_source' AND f.status = 'active' AND a.seed_id IS NULL"
        " AND a.role = 'first' AND a.verdict IN ('APPROVE', 'REVISE')"
    ).fetchall()
    groups: dict[tuple, set[tuple[str, int]]] = {}
    for row in rows:
        finding = json.loads(row["finding_json"])
        located = [item.get("quote") for item in finding.get("locations") or [] if isinstance(item, dict)]
        anchor = fold_quote(located[0]) if located and located[0] else finding["claim"]
        key = (finding["dimension"], finding.get("sub_dimension") or "", anchor)
        groups.setdefault(key, set()).add((row["slug"], row["lesson_n"]))
    return [
        {
            "dimension": key[0],
            "sub_dimension": key[1] or None,
            "anchor": key[2],
            "lessons": sorted(found),
            "to_operator": len(found) >= level_threshold,
        }
        for key, found in sorted(groups.items())
        if len(found) >= 2
    ]


# --- closure and lesson freshness ----------------------------------------------------------------


def read_closure(directory: Path) -> dict[str, Any] | None:
    """``module.closure.yaml`` (schema-checked), or None when the engine has not written it."""
    path = Path(directory) / "module.closure.yaml"
    if not path.is_file():
        return None
    document = yaml.safe_load(path.read_bytes())
    Draft202012Validator(json.loads(CLOSURE_SCHEMA.read_text(encoding="utf-8"))).validate(document)
    return document


def dependents(closure: dict[str, Any], k: int) -> list[int]:
    """Lessons whose manifests go stale when lesson ``k`` is regenerated: k+1..N, the recap included.

    Every later lesson's digest reads lesson k; the closure's own stale records that name lesson
    ``k`` as the upstream are added, so a lesson the row list omits still shows.
    """
    later = {row["n"] for row in closure["lessons"] if row["n"] > k}
    later |= {record["n"] for record in closure["stale"] if record.get("upstream") == k}
    return sorted(later)


def lesson_review_state(
    root: Path, directory: Path, n: int, kind: str, closure: dict[str, Any] | None
) -> dict[str, Any]:
    """The lesson verdict of record and whether it is still current.

    The verdict file names the manifest reviewed. It is stale when that manifest's pinned
    inputs changed (every pin, found structurally, like the closure does), when the history copy
    of the manifest is gone or altered, when the engine's closure records a stale input for it,
    or when a newer manifest of the lesson exists.
    """
    row: dict[str, Any] = {
        "n": n,
        "kind": kind,
        "state": "unreviewed",
        "verdict": None,
        "attempt_id": None,
        "manifest_sha256": None,
        "validated_at": None,
        "stale": [],
    }
    path = Path(directory) / f"lesson-{n}.verdict.yaml"
    if not path.is_file():
        return row
    try:
        record = yaml.safe_load(path.read_bytes())
    except yaml.YAMLError:
        record = None
    if (
        not isinstance(record, dict)
        or record.get("verdict") not in ("APPROVE", "REVISE")
        or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("manifest_sha256", "")))
    ):
        row.update(state="stale", stale=[f"{path.name} is not a lesson verdict"])
        return row
    digest = record["manifest_sha256"]
    row.update(
        verdict=record["verdict"],
        attempt_id=record.get("attempt_id"),
        manifest_sha256=digest,
        validated_at=record.get("validated_at"),
    )
    reasons: list[str] = []
    history = Path(directory) / "manifests" / f"lesson-{n}" / f"{digest}.yaml"
    manifest = None
    try:
        content = history.read_bytes()
        if pm.sha256_bytes(content) != digest:
            reasons.append("the manifest of record does not hash to its name")
        else:
            manifest = yaml.safe_load(content)
    except OSError:
        reasons.append("the manifest of record is missing")
    if manifest is not None:
        for change in changed_inputs(manifest, Path(root)):
            reasons.append(f"{change['input']} ({change['entry']['path']}) changed since the review")
    if closure is not None:
        entry = next((item for item in closure["lessons"] if item["n"] == n), None)
        if entry is not None and entry["current_manifest_sha256"] not in (None, digest):
            reasons.append("a newer manifest exists; the review is of a superseded one")
        for record_ in closure["stale"]:
            if record_["n"] == n and record_["manifest_sha256"] == digest:
                text = f"{record_['input']} ({record_['path']}) is stale in the closure"
                if not any(record_["input"] in reason for reason in reasons):
                    reasons.append(text)
    row.update(state="stale" if reasons else "current", stale=reasons)
    return row


# --- budgets and transitions ------------------------------------------------------------------------


def latest_first_attempts(conn: sqlite3.Connection, level: str, slug: str) -> dict[int, sqlite3.Row]:
    """The first-seat, accepted, non-seeded lesson attempt of record per lesson: the latest recorded."""
    latest: dict[int, sqlite3.Row] = {}
    for attempt in findings_db.module_attempts(conn, level, slug):
        if attempt["kind"] == "lesson":
            latest[attempt["lesson_n"]] = attempt
    return latest


def terminal_transitions(
    conn: sqlite3.Connection,
    level: str,
    slug: str,
    lesson_ns: list[int],
    params: dict[str, Any],
    *,
    needs_regeneration: bool,
) -> list[dict[str, Any]]:
    """Every terminal transition the database's counters and settle items imply for the module (all: ``operator``)."""
    found: list[dict[str, Any]] = []
    budgets = findings_db.module_budgets(conn, level, slug)
    for n, row in sorted(budgets.items()):
        where = "the plan review" if n == findings_db.PLAN_LESSON_N else f"lesson {n}"
        if row["revise_rounds"] > params["max_revise_rounds"]:
            found.append(
                _terminal(
                    REASON_REVISE,
                    f"{where}: REVISE round {row['revise_rounds']} exceeds {params['max_revise_rounds']}",
                    n,
                )
            )
        if row["review_failures"] >= params["review_failures_terminal_at"]:
            found.append(
                _terminal(
                    REASON_REVIEW_FAILURE,
                    f"{where}: {row['review_failures']} failed reviews (retry and fallback spent)",
                    n,
                )
            )
        if row["disputed"]:
            found.append(_terminal(REASON_DISPUTED, f"{where}: {row['disputed']}", n))
    limit = params["regeneration_factor"] * len(lesson_ns)
    spent = sum(row["regenerations"] for row in budgets.values())
    if spent >= limit and needs_regeneration:
        found.append(
            _terminal(
                REASON_REGENERATIONS, f"{spent} of {limit} regenerations spent and a lesson still needs one", None
            )
        )
    for item in findings_db.module_settle_items(conn, level, slug):
        if findings_db.is_waiting_for_operator(item):
            found.append(
                _terminal(REASON_SETTLE, f"settle item {item['item_id']} ended {item['outcome']}", item["lesson_n"])
            )
    return found


def _terminal(reason: str, detail: str, lesson_n: int | None) -> dict[str, Any]:
    return {"transition": TERMINAL, "reason": reason, "detail": detail, "lesson": lesson_n}


def regenerate(
    conn: sqlite3.Connection,
    level: str,
    slug: str,
    n: int,
    lesson_ns: list[int],
    params: dict[str, Any],
    closure: dict[str, Any] | None,
) -> dict[str, Any]:
    """Spend one regeneration of lesson ``n``; raises TerminalTransition when a budget forbids it.

    Returns the count and the lessons that are stale until they are re-reviewed on new manifests.
    """
    if n not in lesson_ns:
        raise FixLoopError(f"lesson {n} is not a lesson of {level}/{slug}")
    budgets = findings_db.module_budgets(conn, level, slug)
    if budgets.get(n, {}).get("revise_rounds", 0) > params["max_revise_rounds"]:
        raise TerminalTransition(
            REASON_REVISE, f"lesson {n} has had more than {params['max_revise_rounds']} REVISE rounds"
        )
    limit = params["regeneration_factor"] * len(lesson_ns)
    spent = sum(row["regenerations"] for row in budgets.values())
    if spent >= limit:
        raise TerminalTransition(REASON_REGENERATIONS, f"{spent} of {limit} regenerations are spent")
    with findings_db.transaction(conn):
        findings_db.bump_budget(conn, level, slug, n, "regenerations")
    stale = dependents(closure, n) if closure is not None else [m for m in lesson_ns if m > n]
    return {"lesson": n, "regenerations": spent + 1, "limit": limit, "stale_until_re_reviewed": stale}


# --- the module verdict -----------------------------------------------------------------------


def _item_view(item: sqlite3.Row) -> dict[str, Any]:
    return {
        "item_id": item["item_id"],
        "finding_ref": item["finding_ref"],
        "kind": item["kind"],
        "lesson_n": item["lesson_n"],
        "outcome": item["outcome"],
    }


def compute_module_verdict(
    conn: sqlite3.Connection, level: str, slug: str, *, root: Path, params: dict[str, Any], now: str | None = None
) -> dict[str, Any]:
    """The module verdict document. APPROVE only when nothing holds it (see ``holds``)."""
    root = Path(root).resolve()
    directory = state_dir(root, level, slug)
    lessons = plan_lessons(root, level, slug)
    lesson_ns = [item["n"] for item in lessons]
    closure = read_closure(directory)
    holds: list[dict[str, Any]] = []
    if closure is None:
        holds.append({"code": "closure_missing", "detail": "module.closure.yaml has not been written by the engine"})
    plan = pm.plan_review_status(level, slug, repo_root=root)
    if plan["state"] != "reviewed_promoted":
        holds.append({"code": "plan_not_promoted", "detail": f"the plan review is {plan['state']}"})
    rows = [lesson_review_state(root, directory, item["n"], item["kind"], closure) for item in lessons]
    for row in rows:
        if row["state"] == "unreviewed":
            holds.append({"code": "lesson_unreviewed", "detail": f"lesson {row['n']} has no review of record"})
        elif row["state"] == "stale":
            holds.append({"code": "lesson_review_stale", "detail": f"lesson {row['n']}: " + "; ".join(row["stale"])})
        elif row["verdict"] == "REVISE":
            holds.append({"code": "lesson_revise", "detail": f"lesson {row['n']} is REVISE"})
    by_lesson = {row["n"]: row for row in rows}
    open_items, waiting, pending_fix = [], [], []
    for item in findings_db.module_settle_items(conn, level, slug):
        view = _item_view(item)
        if findings_db.is_open(item):
            open_items.append(view)
        elif findings_db.is_waiting_for_operator(item):
            waiting.append(view)
        elif item["outcome"] == "supported_defect":
            reviewed = by_lesson.get(item["lesson_n"], {})
            if reviewed.get("manifest_sha256") == item["manifest_sha256"]:
                pending_fix.append(view)  # the defect is confirmed and the lesson has not been rebuilt since
    holds += [
        {"code": "settle_open", "detail": f"settle item {item['item_id']} ({item['finding_ref']}) is open"}
        for item in open_items
    ]
    holds += [
        {
            "code": "settle_operator_pending",
            "detail": f"settle item {item['item_id']} ended {item['outcome']}: the operator decides",
        }
        for item in waiting
    ]
    holds += [
        {
            "code": "settle_supported_defect",
            "detail": f"settle item {item['item_id']} confirmed the defect; lesson {item['lesson_n']} is not rebuilt",
        }
        for item in pending_fix
    ]
    needs_regeneration = any(row["state"] == "current" and row["verdict"] == "REVISE" for row in rows) or bool(
        pending_fix
    )
    terminal = terminal_transitions(conn, level, slug, lesson_ns, params, needs_regeneration=needs_regeneration)
    if terminal:
        holds.append(
            {
                "code": "terminal_operator",
                "detail": "; ".join(f"{item['reason']} ({item['detail']})" for item in terminal),
            }
        )
    if not holds:
        verdict = "APPROVE"
    elif needs_regeneration and not terminal:
        verdict = "REVISE"
    else:
        verdict = "HOLD"
    document = {
        "module_verdict_schema": 1,
        "level": level,
        "slug": slug,
        "verdict": verdict,
        "computed_at": now or findings_db.now_iso(),
        "plan": {key: value for key, value in plan.items() if key in ("state", "attempt_id", "manifest_sha256")},
        "lessons": rows,
        "settle_items": {"open": open_items, "waiting_for_operator": waiting, "supported_defect_pending": pending_fix},
        "holds": holds,
        "terminal": terminal,
    }
    Draft202012Validator(MODULE_VERDICT_SCHEMA).validate(document)
    return document


def write_module_verdict(root: Path, document: dict[str, Any]) -> Path:
    directory = state_dir(root, document["level"], document["slug"])
    path = checked_existing_path(Path(root).resolve(), directory / MODULE_VERDICT_NAME, f"{TREE}/evidence")
    lock.atomic_write(path, lock.yaml_bytes(document))
    return path


# --- the report -------------------------------------------------------------------------------


def build_report(
    conn: sqlite3.Connection, level: str, slug: str, *, root: Path, params: dict[str, Any]
) -> dict[str, Any]:
    """Everything the driver reads: verdict, layers of live findings, signal, gate candidates, budgets, transitions."""
    root = Path(root).resolve()
    directory = state_dir(root, level, slug)
    module = compute_module_verdict(conn, level, slug, root=root, params=params)
    latest = latest_first_attempts(conn, level, slug)
    plan_attempt = [a for a in findings_db.module_attempts(conn, level, slug) if a["kind"] == "plan"][-1:]
    rows = findings_db.module_findings(conn, level, slug)
    layers: dict[str, list[dict[str, Any]]] = {}
    provenance_cache: dict[int, dict[str, Any] | None] = {}
    problems: list[str] = []
    for attempt in [*plan_attempt, *latest.values()]:
        for row in conn.execute(
            "SELECT * FROM findings WHERE review_id = ? AND attempt_id = ? ORDER BY rowid",
            (attempt["review_id"], attempt["attempt_id"]),
        ):
            if row["status"] not in LIVE_STATUSES:
                continue
            layer = row["layer"]
            if layer in (None, UNLOCATED) and attempt["kind"] == "lesson":
                n = attempt["lesson_n"]
                if n not in provenance_cache:
                    try:
                        provenance_cache[n] = load_provenance(directory, n)
                    except ProvenanceError as error:
                        provenance_cache[n] = None
                        problems.append(str(error))
                layer = layer_for_finding(json.loads(row["finding_json"]), provenance_cache[n], kind="lesson")
            layers.setdefault(layer or UNLOCATED, []).append(
                {
                    "finding_ref": findings_db.finding_ref(row["review_id"], row["attempt_id"], row["finding_id"]),
                    "lesson_n": attempt["lesson_n"],
                    "severity": row["severity"],
                    "dimension": row["dimension"],
                    "sub_dimension": row["sub_dimension"],
                    "claim": row["claim"],
                }
            )
    lesson_ns = [item["n"] for item in plan_lessons(root, level, slug)]
    budgets = findings_db.module_budgets(conn, level, slug)
    return {
        "level": level,
        "slug": slug,
        "verdict": module["verdict"],
        "holds": module["holds"],
        "lessons": module["lessons"],
        "layers": dict(sorted(layers.items())),
        "signal": same_dimension_signal(rows),
        "gate_candidates": gate_candidates(rows, params["gate_candidate_pattern"]),
        "unsupported_claims": unsupported_claim_counts(conn, params["unsupported_claim_lessons_to_operator"]),
        "budgets": {
            "per_lesson": {str(n): row for n, row in sorted(budgets.items())},
            "regenerations": sum(row["regenerations"] for row in budgets.values()),
            "regeneration_limit": params["regeneration_factor"] * len(lesson_ns),
            "max_revise_rounds": params["max_revise_rounds"],
        },
        "terminal": module["terminal"]
        + [
            _terminal(
                REASON_UNSUPPORTED_LESSONS,
                f"{item['dimension']} {item['anchor']!r} in {len(item['lessons'])} lessons",
                None,
            )
            for item in unsupported_claim_counts(conn, params["unsupported_claim_lessons_to_operator"])
            if item["to_operator"]
        ],
        "problems": problems,
    }


def render_report(report: dict[str, Any]) -> str:
    lines = [f"module {report['level']}/{report['slug']}: {report['verdict']}"]
    for hold in report["holds"]:
        lines.append(f"  hold {hold['code']}: {hold['detail']}")
    for row in report["lessons"]:
        lines.append(f"  lesson {row['n']} ({row['kind']}): {row['state']} {row['verdict'] or '-'}")
    for layer, items in report["layers"].items():
        lines.append(f"layer {layer}: {len(items)} finding(s)")
        lines += [
            f"  {item['finding_ref']} lesson {item['lesson_n']} {item['severity']} {item['dimension']}"
            for item in items
        ]
    for item in report["signal"]:
        sub = f"/{item['sub_dimension']}" if item["sub_dimension"] else ""
        lines.append(
            f"SIGNAL (no automatic branch): {item['dimension']}{sub} in lessons {item['lessons']}: "
            "the driver decides whether the style card or the prompt is the cause and records why"
        )
    for item in report["gate_candidates"]:
        lines.append(f"GATE CANDIDATE {item['finding_ref']}: {item['could_be_a_gate']} (file a tracked gate issue)")
    budgets = report["budgets"]
    lines.append(f"regenerations {budgets['regenerations']}/{budgets['regeneration_limit']}")
    lines += [f"  lesson {n}: {row}" for n, row in budgets["per_lesson"].items()]
    lines += [f"TERMINAL -> {item['transition']}: {item['reason']}: {item['detail']}" for item in report["terminal"]]
    lines += [f"note: {problem}" for problem in report["problems"]]
    return "\n".join(lines)


# --- CLI --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.fixloop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "The fix loop of the fresh build's review (#8430): report a module's review state, write its\n"
            "module verdict, spend a regeneration, record a dispute or the operator's settle decision.\n"
            "Use after scripts.review.record has recorded reviews. It repairs nothing and branches on nothing:\n"
            "it prints the layer of every live finding, the same-dimension signal, the gate candidates and the\n"
            "terminal transitions (always to the operator), and the driver acts.\n"
            "Do NOT use it to run a review or to change a plan, pack or lesson."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.fixloop report a1 my-module\n"
            "  .venv/bin/python -m scripts.review.fixloop verdict a1 my-module\n"
            "  .venv/bin/python -m scripts.review.fixloop regenerate a1 my-module 2\n"
            "  .venv/bin/python -m scripts.review.fixloop dispute a1 my-module 2 --reason 'writer lane disputes'\n"
            "  .venv/bin/python -m scripts.review.fixloop operator-decision a1 7 --decision 'keep: attested'\n"
            "\nOutputs: report prints text (--json: one object); verdict writes\n"
            "curriculum/l2-uk-en/evidence/<level>/_state/<slug>/module-verdict.yaml; regenerate, dispute and\n"
            "operator-decision update batch_state/review-findings/<level>.sqlite.\n"
            "Exit codes: 0 done; 3 a terminal transition (the module goes to the operator); 2 usage or data error."
        ),
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="repository root (default: this repository)")
    parser.add_argument(
        "--db", type=Path, default=None, help="findings database (default: batch_state/review-findings/<level>.sqlite)"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("report", "print the module's review state"),
        ("verdict", "compute and write module-verdict.yaml"),
    ):
        item = sub.add_parser(name, help=help_text)
        item.add_argument("level")
        item.add_argument("slug")
        item.add_argument("--json", action="store_true", help="print the report as one JSON object")
    regen = sub.add_parser("regenerate", help="spend one regeneration of a lesson (refused past the budget)")
    regen.add_argument("level")
    regen.add_argument("slug")
    regen.add_argument("n", type=int)
    dispute = sub.add_parser("dispute", help="record that the writer's lane disputes a verdict (terminal: operator)")
    dispute.add_argument("level")
    dispute.add_argument("slug")
    dispute.add_argument("n", type=int)
    dispute.add_argument("--reason", required=True)
    decision = sub.add_parser("operator-decision", help="record the operator's decision on a settle item sent to them")
    decision.add_argument("level")
    decision.add_argument("item_id", type=int)
    decision.add_argument("--decision", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else REPO_ROOT
    params = findings_db.load_parameters()
    conn = findings_db.connect(args.db or findings_db.db_path(args.level, root))
    try:
        if args.command == "report":
            report = build_report(conn, args.level, args.slug, root=root, params=params)
            print(
                json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) if args.json else render_report(report)
            )
            return 0
        if args.command == "verdict":
            document = compute_module_verdict(conn, args.level, args.slug, root=root, params=params)
            path = write_module_verdict(root, document)
            print(
                json.dumps(
                    {
                        "verdict": document["verdict"],
                        "path": path.relative_to(root).as_posix(),
                        "holds": document["holds"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "regenerate":
            lesson_ns = [item["n"] for item in plan_lessons(root, args.level, args.slug)]
            closure = read_closure(state_dir(root, args.level, args.slug))
            try:
                result = regenerate(conn, args.level, args.slug, args.n, lesson_ns, params, closure)
            except TerminalTransition as error:
                print(
                    json.dumps({"transition": TERMINAL, "reason": error.reason, "detail": error.detail}, sort_keys=True)
                )
                return 3
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "dispute":
            with findings_db.transaction(conn):
                findings_db.mark_disputed(conn, args.level, args.slug, args.n, args.reason)
            print(
                json.dumps({"transition": TERMINAL, "reason": REASON_DISPUTED, "detail": args.reason}, sort_keys=True)
            )
            return 3
        findings_db.record_operator_decision(conn, args.item_id, args.decision)
        print(json.dumps({"item_id": args.item_id, "operator_decision": args.decision}, sort_keys=True))
        return 0
    except (FixLoopError, findings_db.FindingsDbError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
