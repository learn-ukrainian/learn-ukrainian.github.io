"""Inventory gate on built lesson (Brief #8414 Part 2, plan schema §6).

Fails when:
- a resolved record is outside base_ids ∪ core_ids ∪ name_ids ∪ this lesson's core ∪ incidental
  (lemma_outside_state, quoting the token, its sentence, the record and the tab)
- a core id of this lesson never appears (core_not_introduced)
- a recycled id never appears (recycled_not_used)
- a form listed in the plan's forms for a core lemma does not appear in a teaching position
  (taught_form_absent: paradigm table, activity item, or the step introducing the word)
- a token has an unresolved failure class in the stream (token_unresolved)
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
from scripts.curriculum.resolver import codes as resolver_codes
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
        unit = token.get("unit")
        if isinstance(unit, dict) and units is not None:
            loc = (unit.get("tab"), unit.get("activity"), unit.get("item"), unit.get("block"))
            for u in units:
                if (u.tab, u.activity, u.item, u.block) == loc and u.text:
                    return str(u.text)

    # Search in stream failures
    t_tok = token.get("token")
    t_offset = token.get("offset")
    for f in stream_failures:
        if (
            isinstance(f, dict)
            and f.get("token") == t_tok
            and (t_offset is None or f.get("offset") == t_offset)
            and f.get("text")
        ):
            return str(f["text"])

    return str(t_tok or "")


def _is_record_stress_pending(rec: dict[str, Any]) -> bool:
    """Check whether a record's own stress is pending in _words.yaml."""
    if rec.get("stress") == "pending" or rec.get("stress_status") == "pending":
        return True
    lemma = rec.get("lemma")
    forms = rec.get("forms") or []
    lemma_forms = [f for f in forms if isinstance(f, dict) and f.get("form") == lemma]
    if lemma_forms:
        return any(f.get("stress_source") == "pending" or f.get("stressed") in (None, "pending") for f in lemma_forms)
    if forms:
        return any(
            isinstance(f, dict) and (f.get("stress_source") == "pending" or f.get("stressed") in (None, "pending"))
            for f in forms
        )
    return False


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
    expanded_path: Path | None = None,
    resolutions_path: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
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

    # Map each introduced word to the step(s) that introduce it
    rec_introducing_steps: dict[str, set[str]] = {}
    for step in lesson.get("steps") or []:
        if isinstance(step, dict):
            s_id = step.get("id")
            s_intro = step.get("introduces") or {}
            for w_id in s_intro.get("vocabulary") or []:
                if isinstance(w_id, str) and s_id:
                    rec_introducing_steps.setdefault(w_id, set()).add(s_id)

    # Finding 5: Recycled IDs are not included in total_allowed_ids
    total_allowed_ids = base_ids | core_ids | name_ids | this_lesson_core_ids | this_lesson_incidental_ids

    # Not checked reporting: missing prior waiver
    not_checked: list[str] = []
    if allow_missing_prior and planned.waiver:
        not_checked.append(codes.WAIVER_PRIOR_PLANS_MISSING)

    # Load word store for gloss stress checks
    words_file = words_path or (evidence_root / "_words.yaml")
    store_words: dict[str, dict[str, Any]] = {}
    if not words_file.is_file():
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=codes.BASE_LAYER_MISSING,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="store",
                    token=None,
                    sentence=None,
                    record=None,
                    message=f"word store file {words_file} not found",
                ),
            ),
            not_checked=tuple(not_checked),
        )
    try:
        w_data = yaml.safe_load(words_file.read_text(encoding="utf-8"))
        if not isinstance(w_data, dict) or not isinstance(w_data.get("words"), list):
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=codes.BASE_LAYER_MISSING,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="store",
                        token=None,
                        sentence=None,
                        record=None,
                        message=f"word store file {words_file} has missing or malformed words list",
                    ),
                ),
                not_checked=tuple(not_checked),
            )
        for w in w_data["words"]:
            if isinstance(w, dict) and "id" in w:
                store_words[w["id"]] = w
    except Exception as err:
        return GateReport(
            level=level,
            slug=slug,
            lesson_n=lesson_n,
            failures=(
                GateFailure(
                    code=codes.BASE_LAYER_MISSING,
                    level=level,
                    slug=slug,
                    lesson=lesson_n,
                    tab="store",
                    token=None,
                    sentence=None,
                    record=None,
                    message=f"word store file {words_file} could not be loaded: {err}",
                ),
            ),
            not_checked=tuple(not_checked),
        )

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
                not_checked=tuple(not_checked),
            )
        try:
            from scripts.curriculum.resolver.inputs import ResolverError
            from scripts.curriculum.resolver.receipts import check_receipts

            res_doc = check_receipts(res_file)
            tokens = res_doc.get("tokens") or []
        except ResolverError as err:
            fail_code = codes.LOCK_MISMATCH if err.code == resolver_codes.LOCK_MISMATCH else codes.RESOLUTIONS_INVALID
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=fail_code,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="resolutions",
                        token=None,
                        sentence=None,
                        record=None,
                        message=f"resolutions file {res_file} failed check_receipts: {err.message}",
                    ),
                ),
                not_checked=tuple(not_checked),
            )
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
                not_checked=tuple(not_checked),
            )

    if stream is not None:
        stream_inputs = getattr(stream, "inputs", None) or (stream.get("inputs") if isinstance(stream, dict) else {})
        expected_expanded_sha256 = stream_inputs.get("expanded_sha256") if isinstance(stream_inputs, dict) else None
    else:
        res_inputs = res_doc.get("inputs") if isinstance(res_doc, dict) else {}
        expected_expanded_sha256 = res_inputs.get("expanded_sha256") if isinstance(res_inputs, dict) else None

    expanded_doc = expanded
    if stream is None or expected_expanded_sha256 is not None:
        if expanded_doc is None:
            exp_file = expanded_path or (evidence_root / "_state" / slug / f"lesson-{lesson_n}.expanded.yaml")
            if not exp_file.is_file():
                return GateReport(
                    level=level,
                    slug=slug,
                    lesson_n=lesson_n,
                    failures=(
                        GateFailure(
                            code=codes.EXPANDED_DOCUMENT_MISSING,
                            level=level,
                            slug=slug,
                            lesson=lesson_n,
                            tab="expanded",
                            token=None,
                            sentence=None,
                            record=None,
                            message=f"expanded document {exp_file} not found",
                        ),
                    ),
                    not_checked=tuple(not_checked),
                )
            if Path(f"{exp_file}.lock").exists() and not lock.check(exp_file):
                return GateReport(
                    level=level,
                    slug=slug,
                    lesson_n=lesson_n,
                    failures=(
                        GateFailure(
                            code=codes.EXPANDED_DOCUMENT_MISMATCH,
                            level=level,
                            slug=slug,
                            lesson=lesson_n,
                            tab="expanded",
                            token=None,
                            sentence=None,
                            record=None,
                            message=f"expanded document {exp_file} failed lock check",
                        ),
                    ),
                    not_checked=tuple(not_checked),
                )
            try:
                from scripts.curriculum.resolver.inputs import ExpandedDocument, ResolverError

                expanded_doc = ExpandedDocument.load(exp_file)
            except ResolverError as err:
                fail_code = (
                    codes.EXPANDED_DOCUMENT_MISMATCH
                    if err.code == resolver_codes.LOCK_MISMATCH
                    else codes.EXPANDED_DOCUMENT_MISSING
                )
                return GateReport(
                    level=level,
                    slug=slug,
                    lesson_n=lesson_n,
                    failures=(
                        GateFailure(
                            code=fail_code,
                            level=level,
                            slug=slug,
                            lesson=lesson_n,
                            tab="expanded",
                            token=None,
                            sentence=None,
                            record=None,
                            message=f"expanded document {exp_file} failed to load: {err.message}",
                        ),
                    ),
                    not_checked=tuple(not_checked),
                )
            except Exception as err:
                return GateReport(
                    level=level,
                    slug=slug,
                    lesson_n=lesson_n,
                    failures=(
                        GateFailure(
                            code=codes.EXPANDED_DOCUMENT_MISSING,
                            level=level,
                            slug=slug,
                            lesson=lesson_n,
                            tab="expanded",
                            token=None,
                            sentence=None,
                            record=None,
                            message=f"expanded document {exp_file} failed to load: {err}",
                        ),
                    ),
                    not_checked=tuple(not_checked),
                )

        doc_sha256 = getattr(expanded_doc, "sha256", None) or (
            expanded_doc.get("sha256") if isinstance(expanded_doc, dict) else None
        )
        if expected_expanded_sha256 is not None and doc_sha256 != expected_expanded_sha256:
            origin = "stream inputs" if stream is not None else "receipts inputs"
            return GateReport(
                level=level,
                slug=slug,
                lesson_n=lesson_n,
                failures=(
                    GateFailure(
                        code=codes.EXPANDED_DOCUMENT_MISMATCH,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab="expanded",
                        token=None,
                        sentence=None,
                        record=None,
                        message=(
                            f"expanded document sha256 {doc_sha256!r} differs from "
                            f"{origin} {expected_expanded_sha256!r}"
                        ),
                    ),
                ),
                not_checked=tuple(not_checked),
            )
    else:
        # stream is not None and expected_expanded_sha256 is None
        if expanded_doc is None:
            exp_file = expanded_path or (evidence_root / "_state" / slug / f"lesson-{lesson_n}.expanded.yaml")
            if exp_file.is_file():
                if Path(f"{exp_file}.lock").exists() and not lock.check(exp_file):
                    return GateReport(
                        level=level,
                        slug=slug,
                        lesson_n=lesson_n,
                        failures=(
                            GateFailure(
                                code=codes.EXPANDED_DOCUMENT_MISMATCH,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab="expanded",
                                token=None,
                                sentence=None,
                                record=None,
                                message=f"expanded document {exp_file} failed lock check",
                            ),
                        ),
                        not_checked=tuple(not_checked),
                    )
                try:
                    from scripts.curriculum.resolver.inputs import ExpandedDocument, ResolverError

                    expanded_doc = ExpandedDocument.load(exp_file)
                except ResolverError as err:
                    fail_code = (
                        codes.EXPANDED_DOCUMENT_MISMATCH
                        if err.code == resolver_codes.LOCK_MISMATCH
                        else codes.EXPANDED_DOCUMENT_MISSING
                    )
                    return GateReport(
                        level=level,
                        slug=slug,
                        lesson_n=lesson_n,
                        failures=(
                            GateFailure(
                                code=fail_code,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab="expanded",
                                token=None,
                                sentence=None,
                                record=None,
                                message=f"expanded document {exp_file} failed to load: {err.message}",
                            ),
                        ),
                        not_checked=tuple(not_checked),
                    )
                except Exception as err:
                    return GateReport(
                        level=level,
                        slug=slug,
                        lesson_n=lesson_n,
                        failures=(
                            GateFailure(
                                code=codes.EXPANDED_DOCUMENT_MISSING,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab="expanded",
                                token=None,
                                sentence=None,
                                record=None,
                                message=f"expanded document {exp_file} failed to load: {err}",
                            ),
                        ),
                        not_checked=tuple(not_checked),
                    )

    units_by_locator: dict[tuple[Any, Any, Any, Any], Any] = {}
    if expanded_doc is not None:
        for u in getattr(expanded_doc, "units", ()):
            units_by_locator[(u.tab, u.activity, u.item, u.block)] = u

    # Keep introducing_step_not_locatable when no unit has a step
    has_any_step = False
    if expanded_doc is not None:
        has_any_step = any(getattr(u, "step", None) is not None for u in getattr(expanded_doc, "units", ()))
    if not has_any_step and tokens:
        has_any_step = any(
            isinstance(tok, dict) and isinstance(tok.get("unit"), dict) and tok["unit"].get("step") is not None
            for tok in tokens
        )
    if not has_any_step:
        not_checked.append(codes.INTRODUCING_STEP_NOT_LOCATABLE)

    # 5. Check tokens
    failures: list[GateFailure] = []
    reports: list[dict[str, Any]] = []
    seen_records: set[str] = set()
    seen_teaching_forms: set[tuple[str, str]] = set()

    for token in tokens:
        if not isinstance(token, dict):
            continue

        klass = str(token.get("class", ""))
        surface = str(token.get("surface", ""))

        # Ignore skipped tokens
        if klass.startswith(resolver_codes.SKIPPED_PREFIX) or surface == resolver_codes.SKIPPED:
            continue
        if klass == resolver_codes.LETTER_OR_SYLLABLE:
            continue

        unit = token.get("unit") or {}
        tab = str(unit.get("tab", "unknown"))
        token_text = str(token.get("token", ""))
        sentence = _get_sentence_text(token, expanded_doc, stream_failures)

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

        role = token.get("role") or (unit_obj.role if unit_obj is not None else (unit.get("role") or ""))

        selected = token.get("selected")

        # Check resolver failure classes
        if klass in resolver_codes.FAILURE_CLASSES:
            if klass == resolver_codes.LEMMA_OUTSIDE_STATE:
                failures.append(
                    GateFailure(
                        code=codes.LEMMA_OUTSIDE_STATE,
                        level=level,
                        slug=slug,
                        lesson=lesson_n,
                        tab=tab,
                        token=token_text,
                        sentence=sentence,
                        record=selected.get("record") if isinstance(selected, dict) else None,
                        message=f"token {token_text!r} in {sentence!r} is outside allowed learner state",
                    )
                )
            elif klass == resolver_codes.PENDING_STRESS:
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
            else:
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

        # Check open tokens
        if selected is None:
            if klass == resolver_codes.STRESS_CERTAIN_IDENTITY_OPEN:
                reports.append(
                    {
                        "code": resolver_codes.STRESS_CERTAIN_IDENTITY_OPEN,
                        "tab": tab,
                        "token": token_text,
                        "sentence": sentence,
                        "message": f"open identity question for token {token_text!r} in {sentence!r} is non-blocking",
                    }
                )
                continue
            elif klass == resolver_codes.STRESS_OPEN or klass in resolver_codes.OPEN_CLASSES:
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
                continue

        # Selected tokens
        if isinstance(selected, dict):
            rec = selected.get("record")
            is_gloss = surface == resolver_codes.GLOSS_REF or token.get("surface") == resolver_codes.GLOSS_REF
            if is_gloss:
                if rec:
                    w_rec = store_words.get(rec)
                    if w_rec is None:
                        failures.append(
                            GateFailure(
                                code=codes.TOKEN_UNRESOLVED,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab=tab,
                                token=token_text,
                                sentence=sentence,
                                record=rec,
                                message=f"gloss token {token_text!r} refers to record {rec!r} absent from word store",
                            )
                        )
                        continue
                    if _is_record_stress_pending(w_rec):
                        failures.append(
                            GateFailure(
                                code=codes.PENDING_STRESS,
                                level=level,
                                slug=slug,
                                lesson=lesson_n,
                                tab=tab,
                                token=token_text,
                                sentence=sentence,
                                record=rec,
                                message=f"gloss token {token_text!r} refers to record {rec!r} with pending stress in word store",
                            )
                        )
                        continue
            else:
                # Surface tokens: check pending stress
                if selected.get("stressed") is None or selected.get("stressed") == "pending":
                    failures.append(
                        GateFailure(
                            code=codes.PENDING_STRESS,
                            level=level,
                            slug=slug,
                            lesson=lesson_n,
                            tab=tab,
                            token=token_text,
                            sentence=sentence,
                            record=rec,
                            message=f"token {token_text!r} in {sentence!r} selected reading has pending stress",
                        )
                    )
                    continue

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
                # Teaching position: record_print, item_prompt, item_answer, or introducing step
                step_id = unit.get("step") or (unit_obj.step if unit_obj is not None else None)
                is_intro_step = bool(step_id and step_id in rec_introducing_steps.get(rec, set()))
                if is_intro_step or role in ("record_print", "item_prompt", "item_answer"):
                    for ftag in selected.get("forms") or []:
                        seen_teaching_forms.add((rec, ftag))

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
                                    f"(record_print, item_prompt, item_answer, or introducing step)"
                                ),
                            )
                        )

    return GateReport(
        level=level,
        slug=slug,
        lesson_n=lesson_n,
        failures=tuple(failures),
        reports=tuple(reports),
        not_checked=tuple(not_checked),
    )
