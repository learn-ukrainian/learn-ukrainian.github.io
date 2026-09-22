"""Observed learner state index (Brief #8414 Part 2, plan schema §4).

After a lesson is built: reads the resolution receipts
(curriculum/l2-uk-en/evidence/<level>/_state/<slug>/lesson-<n>.resolutions.yaml)
and writes curriculum/l2-uk-en/evidence/<level>/_state/<slug>/lesson-<n>.observed.yaml
with a deterministic YAML format and a lock sidecar.

Schema: schemas/learner-observed-v1.schema.json
Roles:
- core -> taught (or drilled if in drilling activity / forms list drilled)
- drilled: form in forms list or drilling activity
- recycled: recycled in this lesson
- incidental: incidental in this lesson
- name: speaker or place name id
- exposed: anything else in planned state

Untaught forms:
- exposed forms whose grammar category is not yet taught at this position.
"""

from __future__ import annotations

import contextlib
import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver import codes as resolver_codes
from scripts.curriculum.resolver.inputs import ExpandedDocument, ResolverError
from scripts.curriculum.resolver.receipts import check_receipts, validate_receipts
from scripts.curriculum.validate.loader import PlanError, load_plan

from . import codes
from .planned import PlannedStateError, planned_state

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas/learner-observed-v1.schema.json"
VALID_TABS = resolver_codes.TABS


class ObservedError(Exception):
    """Failure outcome in observed state computation or validation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def validate_observed(doc: Any) -> None:
    """Validate document against schemas/learner-observed-v1.schema.json."""
    if not SCHEMA_PATH.is_file():
        raise ObservedError(codes.OBSERVED_SCHEMA_INVALID, f"schema file not found: {SCHEMA_PATH}")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path_str = ".".join(str(p) for p in first.absolute_path) or "root"
        raise ObservedError(codes.OBSERVED_SCHEMA_INVALID, f"at {path_str}: {first.message}")


def check_observed(path: Path) -> dict[str, Any]:
    """Verify observed state YAML and lock sidecar, returning parsed dict."""
    path = Path(path)
    if not path.is_file():
        raise ObservedError(codes.OBSERVED_YAML_INVALID, f"observed file {path} not found")
    if not lock.check(path):
        raise ObservedError(codes.LOCK_MISMATCH, f"observed file {path} failed lock check")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as err:
        raise ObservedError(codes.OBSERVED_YAML_INVALID, f"failed parsing YAML in {path}: {err}") from err
    validate_observed(doc)
    return doc


def _sort_key(word_id: str) -> tuple[int, int, str]:
    """Deterministic sort key for word store IDs."""
    m = re.fullmatch(r"W-([0-9]+)", word_id)
    if m:
        return (0, int(m[1]), word_id)
    return (1, 0, word_id)


def extract_grammar_category(tag: str, known_categories: set[str] | None = None) -> str:
    """Extract primary grammatical category from VESUM tag string."""
    parts = tag.split(":")
    if known_categories:
        for cat in known_categories:
            if cat in parts or cat == tag:
                return cat
    # Check for case
    for c in ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly"):
        if c in parts:
            return c
    # Check for verb tense/mood
    for v in ("past", "pres", "futr", "impr", "inf"):
        if v in parts:
            return v
    return parts[0] if parts else "other"


def build_observed_index(
    level: str,
    slug: str,
    lesson_n: int,
    *,
    resolutions_doc: dict[str, Any] | None = None,
    resolutions_path: Path | None = None,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
    words_path: Path | None = None,
    base_request_path: Path | None = None,
    grammar_path: Path | None = None,
    expanded: Any = None,
    expanded_path: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    """Compute post-build observed index for level, slug, lesson_n."""
    plans_root = plans_dir or (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}")
    evidence_root = evidence_dir or (REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}")

    # 1. Load module plan
    plan_file = plans_root / f"{slug}.yaml"
    if not plan_file.is_file():
        raise ObservedError(codes.PLAN_NOT_FOUND, f"plan file {plan_file} not found")
    try:
        plan = load_plan(plan_file)
    except PlanError as err:
        raise ObservedError(err.code, err.message) from err
    except Exception as err:
        raise ObservedError(codes.PLAN_YAML_INVALID, f"failed loading {plan_file}: {err}") from err

    arc_ref = plan.get("arc_ref") or {}
    position = arc_ref.get("position")
    if not isinstance(position, int):
        raise ObservedError(codes.PLAN_YAML_INVALID, f"plan {plan_file} missing arc_ref.position")

    lesson = next((l for l in plan.get("lessons", []) if isinstance(l, dict) and l.get("n") == lesson_n), None)
    if lesson is None:
        raise ObservedError(codes.LESSON_NOT_FOUND, f"lesson {lesson_n} not found in plan {slug}")

    # 2. Load resolution receipts via check_receipts
    res_path = resolutions_path or (evidence_root / "_state" / slug / f"lesson-{lesson_n}.resolutions.yaml")
    if resolutions_doc is not None:
        res_data = resolutions_doc
        try:
            validate_receipts(res_data)
        except ResolverError as err:
            raise ObservedError(codes.RESOLUTIONS_INVALID, f"in-memory resolutions invalid: {err.message}") from err
    else:
        if not res_path.is_file():
            raise ObservedError(codes.RESOLUTIONS_NOT_FOUND, f"resolutions file {res_path} not found")
        try:
            res_data = check_receipts(res_path)
        except ResolverError as err:
            if err.code == resolver_codes.LOCK_MISMATCH:
                raise ObservedError(codes.LOCK_MISMATCH, err.message) from err
            raise ObservedError(codes.RESOLUTIONS_INVALID, err.message) from err
        except Exception as err:
            raise ObservedError(codes.RESOLUTIONS_INVALID, f"failed parsing YAML in {res_path}: {err}") from err

    expanded_doc = expanded
    if expanded_doc is None:
        exp_file = expanded_path or (evidence_root / "_state" / slug / f"lesson-{lesson_n}.expanded.yaml")
        if exp_file.is_file():
            with contextlib.suppress(Exception):
                expanded_doc = ExpandedDocument.load(exp_file)

    units_by_locator: dict[tuple[Any, Any, Any, Any], Any] = {}
    if expanded_doc is not None:
        for u in getattr(expanded_doc, "units", ()):
            units_by_locator[(u.tab, u.activity, u.item, u.block)] = u

    # 3. Planned state
    try:
        planned = planned_state(
            level,
            position,
            lesson_n,
            allow_missing_prior=allow_missing_prior,
            strict=strict,
            plans_dir=plans_root,
            evidence_dir=evidence_root,
            words_path=words_path,
            base_request_path=base_request_path,
        )
    except PlannedStateError as err:
        raise ObservedError(err.code, err.message) from err

    # 4. Taught grammar categories
    taught_categories: set[str] = set()
    # From planned grammar IDs
    for g_id in planned.grammar_ids:
        taught_categories.add(g_id)
    # From grammar file if present
    g_file = grammar_path or (plans_root / "_grammar.yaml")
    if g_file.is_file():
        try:
            g_data = yaml.safe_load(g_file.read_text(encoding="utf-8"))
            if isinstance(g_data, list):
                for entry in g_data:
                    if isinstance(entry, dict):
                        gid = entry.get("id")
                        cat = entry.get("category")
                        cats = entry.get("categories") or []
                        if gid in planned.grammar_ids:
                            if cat:
                                taught_categories.add(cat)
                            for c in cats:
                                taught_categories.add(c)
        except Exception:
            pass

    # From this lesson's grammar inventory
    inv = lesson.get("inventory") or {}
    for g_item in inv.get("grammar", []):
        if isinstance(g_item, dict):
            if "id" in g_item:
                taught_categories.add(str(g_item["id"]))
            if "category" in g_item:
                taught_categories.add(str(g_item["category"]))
            for c in g_item.get("categories") or []:
                taught_categories.add(str(c))
            # Also if point mentions a case/tense
            point_text = str(g_item.get("point", "")).lower()
            for c in ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly", "past", "pres", "futr"):
                if c in point_text:
                    taught_categories.add(c)

    # 5. Extract role sets from plan
    vocab = inv.get("vocabulary") or {}
    core_items = vocab.get("core") or []
    core_by_id = {
        item["evidence"]: item
        for item in core_items
        if isinstance(item, dict) and isinstance(item.get("evidence"), str)
    }
    incidental_ids = {
        item["evidence"]
        for item in (vocab.get("incidental") or [])
        if isinstance(item, dict) and isinstance(item.get("evidence"), str)
    }
    recycled_ids = {item for item in (vocab.get("recycled") or []) if isinstance(item, str)}

    name_ids = set(planned.name_ids.keys())
    dial = lesson.get("dialogue") or {}
    for spk in dial.get("speakers", []):
        if isinstance(spk, dict) and "evidence" in spk:
            name_ids.add(spk["evidence"])
    for plc in dial.get("places", []):
        if isinstance(plc, dict) and "evidence" in plc:
            name_ids.add(plc["evidence"])

    # Ground drilled role in plan data without string heuristics.
    # Plan field names verified in scripts/curriculum/validate/validate.py (lines 445-455):
    # `step.get("practice")`, `lesson.get("consolidation")`, `(lesson.get("practice") or {}).get("patterns")`
    practice_or_consolidation_acts: set[str] = set()
    for step in lesson.get("steps", []):
        if isinstance(step, dict):
            for act_id in step.get("practice") or []:
                if isinstance(act_id, str):
                    practice_or_consolidation_acts.add(act_id)
    for act_id in lesson.get("consolidation") or []:
        if isinstance(act_id, str):
            practice_or_consolidation_acts.add(act_id)
    lesson_practice = lesson.get("practice")
    if isinstance(lesson_practice, list):
        for act_id in lesson_practice:
            if isinstance(act_id, str):
                practice_or_consolidation_acts.add(act_id)
    elif isinstance(lesson_practice, dict):
        for act_id in lesson_practice.get("patterns") or []:
            if isinstance(act_id, str):
                practice_or_consolidation_acts.add(act_id)

    # 6. Aggregate tokens
    record_forms: dict[str, dict[str, dict[str, int]]] = {}
    drilled_records: set[str] = set()

    tokens = res_data.get("tokens") or []
    for token in tokens:
        if not isinstance(token, dict):
            continue
        klass = str(token.get("class", ""))
        surface = str(token.get("surface", ""))
        if klass.startswith("skipped:") or surface == "skipped":
            continue
        if klass == "letter_or_syllable":
            continue

        unit = token.get("unit") or {}
        tab = unit.get("tab")
        if tab not in VALID_TABS:
            raise ObservedError(
                codes.UNKNOWN_TAB,
                f"token {token.get('token')!r} has unknown tab {tab!r}; must be one of {sorted(VALID_TABS)}",
            )

        selected = token.get("selected")
        if not selected or not isinstance(selected, dict):
            continue
        rec_id = selected.get("record")
        if not rec_id:
            continue

        forms = selected.get("forms") or []
        if not forms:
            forms = ["base"]

        if rec_id not in record_forms:
            record_forms[rec_id] = {}
        for ftag in forms:
            if ftag not in record_forms[rec_id]:
                record_forms[rec_id][ftag] = {"urok": 0, "slovnyk": 0, "vpravy": 0, "resursy": 0}
            record_forms[rec_id][ftag][tab] += 1

        unit_obj = None
        unit_idx = token.get("unit_index")
        if (
            expanded_doc is not None
            and isinstance(unit_idx, int)
            and 0 <= unit_idx < len(getattr(expanded_doc, "units", ()))
        ):
            unit_obj = expanded_doc.units[unit_idx]
        elif expanded_doc is not None:
            unit_loc = (unit.get("tab"), unit.get("activity"), unit.get("item"), unit.get("block"))
            unit_obj = units_by_locator.get(unit_loc)

        role = unit_obj.role if unit_obj is not None else (token.get("role") or unit.get("role") or "")
        act_id = unit.get("activity")
        if rec_id in core_by_id and act_id in practice_or_consolidation_acts and role in ("item_prompt", "item_answer"):
            core_item = core_by_id[rec_id]
            plan_forms = set(core_item.get("forms") or [])
            if any(f in plan_forms for f in forms):
                drilled_records.add(rec_id)

    # 7. Build records list and untaught forms
    records_list = []
    untaught_forms_list = []
    untaught_count = 0
    total_exposed_tokens = 0

    sorted_rec_ids = sorted(record_forms.keys(), key=_sort_key)

    for rec_id in sorted_rec_ids:
        # Determine role
        if rec_id in name_ids:
            role = "name"
        elif rec_id in incidental_ids:
            role = "incidental"
        elif rec_id in recycled_ids:
            role = "recycled"
        elif rec_id in core_by_id:
            role = "drilled" if rec_id in drilled_records else "taught"
        else:
            role = "exposed"

        forms_list = []
        for ftag, tab_counts in sorted(record_forms[rec_id].items()):
            forms_list.append({"tags": ftag, "count_by_tab": dict(sorted(tab_counts.items()))})

            if role == "exposed":
                form_total = sum(tab_counts.values())
                total_exposed_tokens += form_total
                cat = extract_grammar_category(ftag, known_categories=taught_categories)
                if cat not in taught_categories:
                    untaught_count += form_total
                    untaught_forms_list.append({"record": rec_id, "tags": ftag, "category": cat})

        records_list.append({"id": rec_id, "role": role, "forms": forms_list})

    share = round(untaught_count / total_exposed_tokens, 4) if total_exposed_tokens > 0 else 0.0

    # Sort untaught forms list
    untaught_forms_sorted = sorted(
        untaught_forms_list,
        key=lambda item: (_sort_key(item["record"]), item["tags"], item["category"]),
    )

    doc: dict[str, Any] = {
        "observed_schema": 1,
        "lesson": {
            "level": level,
            "slug": slug,
            "n": lesson_n,
        },
        "records": records_list,
        "untaught_forms": {
            "count": untaught_count,
            "share": share,
            "forms": untaught_forms_sorted,
        },
    }

    validate_observed(doc)
    return doc


def write_observed(
    level: str,
    slug: str,
    lesson_n: int,
    *,
    resolutions_doc: dict[str, Any] | None = None,
    resolutions_path: Path | None = None,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
    words_path: Path | None = None,
    base_request_path: Path | None = None,
    grammar_path: Path | None = None,
    expanded: Any = None,
    expanded_path: Path | None = None,
    out_dir: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
) -> tuple[Path, str]:
    """Compute and atomically write observed index and lock sidecar."""
    doc = build_observed_index(
        level,
        slug,
        lesson_n,
        resolutions_doc=resolutions_doc,
        resolutions_path=resolutions_path,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
        words_path=words_path,
        base_request_path=base_request_path,
        grammar_path=grammar_path,
        expanded=expanded,
        expanded_path=expanded_path,
        allow_missing_prior=allow_missing_prior,
        strict=strict,
    )
    evidence_root = out_dir or evidence_dir or (REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}")
    state_dir = Path(evidence_root) / "_state" / slug
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / f"lesson-{lesson_n}.observed.yaml"
    digest = lock.write(out_path, lock.yaml_bytes(doc))
    return out_path, digest
