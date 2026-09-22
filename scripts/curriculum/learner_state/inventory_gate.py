"""Inventory gate on built lesson (Brief #8414 Part 2, plan schema §6).

Fails when:
- a resolved record is outside base_ids ∪ core_ids ∪ name_ids ∪ this lesson's core ∪ incidental
  (lemma_outside_state, quoting the token, its sentence, the record and the tab)
- a core id of this lesson never appears (core_not_introduced)
- a recycled id never appears (recycled_not_used)
- a form listed in the plan's forms for a core lemma does not appear in a teaching position
  (taught_form_absent: paradigm table, activity item, or the step introducing the word)
- a token is outside_allowlist or unclassifiable in the stream (token_unresolved)
- tokens marked skipped:<field> are ignored by every check here
- a resolved form's stress is pending (pending_stress).

Any learner: true form of an allowed record passes (revision 8); the resolver has already
excluded marked forms. Speaker and place names pass through name_ids; an undeclared name
is lemma_outside_state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lock
from scripts.curriculum.validate.loader import PlanError, load_plan

from . import codes
from .planned import PlannedStateError, planned_state

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class GateFailure:
    code: str
    level: str
    slug: str
    lesson: int
    tab: str
    token: str | None
    sentence: str | None
    record: str | None
    message: str


@dataclass(frozen=True)
class GateReport:
    level: str
    slug: str
    lesson_n: int
    failures: tuple[GateFailure, ...]
    reports: tuple[dict[str, Any], ...] = ()
    not_checked: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return len(self.failures) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "level": self.level,
            "slug": self.slug,
            "lesson_n": self.lesson_n,
            "failures": [
                {
                    "code": f.code,
                    "level": f.level,
                    "slug": f.slug,
                    "lesson": f.lesson,
                    "tab": f.tab,
                    "token": f.token,
                    "sentence": f.sentence,
                    "record": f.record,
                    "message": f.message,
                }
                for f in self.failures
            ],
            "reports": list(self.reports),
            "not_checked": list(self.not_checked),
        }

    def render_text(self) -> str:
        if self.ok:
            return f"PASS: inventory gate passed for {self.level}/{self.slug} lesson {self.lesson_n}"
        lines = [
            f"FAIL: inventory gate failed with {len(self.failures)} error(s) for {self.level}/{self.slug} lesson {self.lesson_n}:"
        ]
        for f in self.failures:
            lines.append(
                f"  [{f.code}] tab={f.tab} token={f.token!r} in {f.sentence!r} (record={f.record}): {f.message}"
            )
        return "\n".join(lines)


def _get_sentence_text(token: dict[str, Any], expanded_doc: Any, stream_failures: list[dict[str, Any]]) -> str:
    """Extract sentence text from token, expanded document, or stream failures."""
    if token.get("sentence"):
        return str(token["sentence"])
    if token.get("text"):
        return str(token["text"])

    unit_idx = token.get("unit_index")

    if expanded_doc is not None:
        units = getattr(expanded_doc, "units", None)
        if units is not None and isinstance(unit_idx, int) and 0 <= unit_idx < len(units):
            u_text = getattr(units[unit_idx], "text", None)
            if u_text:
                return str(u_text)

    # Search in stream failures
    t_tok = token.get("token")
    t_offset = token.get("offset")
    for f in stream_failures:
        if isinstance(f, dict) and f.get("token") == t_tok and f.get("offset") == t_offset and f.get("text"):
            return str(f["text"])

    return str(t_tok or "")


def check_lesson(
    level: str,
    slug: str,
    lesson_n: int,
    stream: Any = None,
    *,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
    words_path: Path | None = None,
    base_request_path: Path | None = None,
    expanded: Any = None,
    resolutions_path: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
    **kwargs: Any,
) -> GateReport:
    """Validate a built lesson's resolution stream against inventory rules."""
    plans_root = plans_dir or (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}")
    evidence_root = evidence_dir or (REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}")

    # 1. Load module plan
    plan_file = plans_root / f"{slug}.yaml"
    if not plan_file.is_file():
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=codes.PLAN_NOT_FOUND,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="plan",
                    token=None,
                    sentence=None,
                    record=None,
                    message=f"plan file {plan_file} not found",
                ),
            ),
        )
    try:
        plan = load_plan(plan_file)
    except PlanError as err:
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=err.code,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="plan",
                    token=None,
                    sentence=None,
                    record=None,
                    message=err.message,
                ),
            ),
        )

    arc_ref = plan.get("arc_ref") or {}
    position = arc_ref.get("position")
    if not isinstance(position, int):
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=codes.PLAN_YAML_INVALID,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="plan",
                    token=None,
                    sentence=None,
                    record=None,
                    message=f"plan {plan_file} missing arc_ref.position",
                ),
            ),
        )

    lesson = next((l for l in plan.get("lessons", []) if isinstance(l, dict) and l.get("n") == lesson_n), None)
    if lesson is None:
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=codes.LESSON_NOT_FOUND,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="plan",
                    token=None,
                    sentence=None,
                    record=None,
                    message=f"lesson {lesson_n} not found in plan {slug}",
                ),
            ),
        )

    # 2. Planned state
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
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=err.code,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="plan",
                    token=None,
                    sentence=None,
                    record=None,
                    message=err.message,
                ),
            ),
        )

    # 3. Allowlist composition
    base_ids = set(planned.base_ids)
    core_ids = set(planned.core_ids.keys())
    name_ids = set(planned.name_ids.keys())

    inv = lesson.get("inventory") or {}
    vocab = inv.get("vocabulary") or {}
    this_lesson_core_items = vocab.get("core") or []
    this_lesson_core_ids = {
        item["evidence"]
        for item in this_lesson_core_items
        if isinstance(item, dict) and isinstance(item.get("evidence"), str)
    }
    this_lesson_incidental_ids = {
        item["evidence"]
        for item in (vocab.get("incidental") or [])
        if isinstance(item, dict) and isinstance(item.get("evidence"), str)
    }
    this_lesson_recycled_ids = {item for item in (vocab.get("recycled") or []) if isinstance(item, str)}

    # Add dialogue names
    dial = lesson.get("dialogue") or {}
    for spk in dial.get("speakers", []):
        if isinstance(spk, dict) and "evidence" in spk:
            name_ids.add(spk["evidence"])
    for plc in dial.get("places", []):
        if isinstance(plc, dict) and "evidence" in plc:
            name_ids.add(plc["evidence"])

    total_allowed_ids = (
        base_ids | core_ids | name_ids | this_lesson_core_ids | this_lesson_incidental_ids | this_lesson_recycled_ids
    )

    # Map core items to the steps that introduce them
    step_intro_vocab: dict[str, set[str]] = {}
    for step in lesson.get("steps", []):
        if isinstance(step, dict):
            s_id = str(step.get("id", ""))
            intro = (step.get("introduces") or {}).get("vocabulary") or []
            step_intro_vocab[s_id] = {str(v) for v in intro}

    # 4. Stream and tokens
    stream_failures: list[dict[str, Any]] = []
    tokens: list[dict[str, Any]] = []

    if stream is not None:
        tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
        stream_failures = getattr(stream, "failures", None) or (
            stream.get("failures") if isinstance(stream, dict) else []
        )
    else:
        res_file = resolutions_path or (evidence_root / "_state" / slug / f"lesson-{lesson_n}.resolutions.yaml")
        if not res_file.is_file():
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=codes.RESOLUTIONS_NOT_FOUND,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="resolutions",
                        token=None,
                        sentence=None,
                        record=None,
                        message=f"resolutions file {res_file} not found",
                    ),
                ),
            )
        if not lock.check(res_file):
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=codes.LOCK_MISMATCH,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="resolutions",
                        token=None,
                        sentence=None,
                        record=None,
                        message=f"resolutions file {res_file} failed lock check",
                    ),
                ),
            )
        try:
            res_doc = yaml.safe_load(res_file.read_text(encoding="utf-8"))
            tokens = res_doc.get("tokens") or []
        except Exception as err:
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=codes.RESOLUTIONS_INVALID,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="resolutions",
                        token=None,
                        sentence=None,
                        record=None,
                        message=f"failed loading resolutions YAML in {res_file}: {err}",
                    ),
                ),
            )

    expanded_doc = expanded
    if expanded_doc is None:
        exp_file = evidence_root / "_state" / slug / f"lesson-{lesson_n}.expanded.yaml"
        if exp_file.is_file():
            try:
                from scripts.curriculum.resolver.inputs import ExpandedDocument

                expanded_doc = ExpandedDocument.load(exp_file)
            except Exception:
                pass

    # 5. Check tokens
    failures: list[GateFailure] = []
    seen_records: set[str] = set()
    seen_teaching_forms: set[tuple[str, str]] = set()

    for token in tokens:
        if not isinstance(token, dict):
            continue

        klass = str(token.get("class", ""))
        surface = str(token.get("surface", ""))

        # Ignore skipped tokens
        if klass.startswith("skipped:") or surface == "skipped":
            continue
        if klass == "letter_or_syllable":
            continue

        unit = token.get("unit") or {}
        tab = str(unit.get("tab", "unknown"))
        token_text = str(token.get("token", ""))
        sentence = _get_sentence_text(token, expanded_doc, stream_failures)

        # Check outside_allowlist / unclassifiable in stream
        if klass in ("outside_allowlist", "unclassifiable", "token_unresolved"):
            failures.append(
                GateFailure(
                    code=codes.TOKEN_UNRESOLVED,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab=tab,
                    token=token_text,
                    sentence=sentence,
                    record=None,
                    message=f"token {token_text!r} in {sentence!r} is {klass} in stream",
                )
            )
            continue

        selected = token.get("selected")

        # Check pending stress
        if klass == "pending_stress":
            failures.append(
                GateFailure(
                    code=codes.PENDING_STRESS,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab=tab,
                    token=token_text,
                    sentence=sentence,
                    record=selected.get("record") if isinstance(selected, dict) else None,
                    message=f"token {token_text!r} in {sentence!r} has pending stress",
                )
            )
            continue

        if isinstance(selected, dict) and (selected.get("stressed") is None or selected.get("stressed") == "pending"):
            failures.append(
                GateFailure(
                    code=codes.PENDING_STRESS,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab=tab,
                    token=token_text,
                    sentence=sentence,
                    record=selected.get("record"),
                    message=f"token {token_text!r} in {sentence!r} selected reading has pending stress",
                )
            )
            continue

        # Check lemma outside state
        if klass == codes.LEMMA_OUTSIDE_STATE:
            failures.append(
                GateFailure(
                    code=codes.LEMMA_OUTSIDE_STATE,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab=tab,
                    token=token_text,
                    sentence=sentence,
                    record=None,
                    message=f"token {token_text!r} in {sentence!r} is outside allowed learner state",
                )
            )
            continue

        if selected is not None and isinstance(selected, dict):
            rec = selected.get("record")
            if rec and rec not in total_allowed_ids:
                failures.append(
                    GateFailure(
                        code=codes.LEMMA_OUTSIDE_STATE,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab=tab,
                        token=token_text,
                        sentence=sentence,
                        record=rec,
                        message=f"token {token_text!r} in {sentence!r} resolves to record {rec!r} outside allowed learner state",
                    )
                )
                continue

            if rec:
                seen_records.add(rec)

                # Check if this token is in a teaching position:
                # 1. paradigm table
                # 2. activity item
                # 3. the step that introduces the word
                block = unit.get("block")
                role = str(unit.get("role", ""))
                act_id = unit.get("activity")
                item_idx = unit.get("item")

                is_teaching = False
                if (
                    block == "paradigm"
                    or "paradigm" in str(block).lower()
                    or role == "paradigm"
                    or act_id is not None
                    or item_idx is not None
                    or role.startswith("item_")
                ):
                    is_teaching = True
                else:
                    # Check if unit block corresponds to the step introducing rec
                    for s_id, s_vocab in step_intro_vocab.items():
                        if rec in s_vocab and (
                            block == s_id or str(block).startswith(s_id) or unit.get("step") == s_id
                        ):
                            is_teaching = True
                            break

                if is_teaching:
                    for ftag in selected.get("forms") or []:
                        seen_teaching_forms.add((rec, ftag))
        elif klass in codes.OPEN_CLASSES:
            # An open token that was never answered / selected
            failures.append(
                GateFailure(
                    code=codes.TOKEN_UNRESOLVED,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab=tab,
                    token=token_text,
                    sentence=sentence,
                    record=None,
                    message=f"token {token_text!r} in {sentence!r} is open ({klass}) without selection",
                )
            )

    # 6. Check lesson-level requirements
    # Core vocabulary of this lesson must appear
    for core_id in sorted(this_lesson_core_ids):
        if core_id not in seen_records:
            failures.append(
                GateFailure(
                    code=codes.CORE_NOT_INTRODUCED,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="lesson",
                    token=None,
                    sentence=None,
                    record=core_id,
                    message=f"core vocabulary record {core_id} declared in plan was not introduced in lesson",
                )
            )

    # Recycled vocabulary of this lesson must appear
    for rec_id in sorted(this_lesson_recycled_ids):
        if rec_id not in seen_records:
            failures.append(
                GateFailure(
                    code=codes.RECYCLED_NOT_USED,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="lesson",
                    token=None,
                    sentence=None,
                    record=rec_id,
                    message=f"recycled vocabulary record {rec_id} declared in plan was not used in lesson",
                )
            )

    # Forms listed in the plan's forms for core lemmas must appear in a teaching position
    for c_item in this_lesson_core_items:
        if isinstance(c_item, dict):
            c_id = c_item.get("evidence")
            if isinstance(c_id, str):
                for ftag in c_item.get("forms") or []:
                    if (c_id, ftag) not in seen_teaching_forms:
                        failures.append(
                            GateFailure(
                                code=codes.TAUGHT_FORM_ABSENT,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab="lesson",
                                token=None,
                                sentence=None,
                                record=c_id,
                                message=(
                                    f"taught form {ftag!r} for core record {c_id} does not appear in a teaching position "
                                    f"(paradigm table, activity item, or introducing step)"
                                ),
                            )
                        )

    return GateReport(
        level=level,
        slug=slug,
        lesson_n=lesson_n,
        failures=tuple(failures),
    )
