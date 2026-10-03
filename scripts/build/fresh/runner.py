"""Ordered, fail-closed checks 1-12 for one fresh lesson.

Per-Type Key Rule Table (Check 4):
+--------------------+------------------------+-----------------------+---------------------------------------+
| Activity Type      | Choice Container       | Key Source            | Key Rule / Validation                 |
+--------------------+------------------------+-----------------------+---------------------------------------+
| quiz               | items[].options        | correct (int),        | Exactly 1 key. int in bounds; str in  |
| / multiple-choice  |                        | answer (str), or      | options; exactly 1 dict correct: true.|
|                    |                        | opt.correct == true   | Multi-spec must resolve to same opt.  |
| fill-in            | items[].options        | answer (str) or       | form-choice: tags form in options;    |
|                    |                        | answer_tags (str)     | orthography: answer in options x 1.   |
| error-correction   | items[].options        | correction / answer   | error == E-.incorrect & in sentence x1|
|                    | (optional)             | (str) from E- record  | corr == E-.correct & in options if opt|
| image-to-letter    | items[].options        | letter (str)          | letter in options x 1.                |
| translate          | items[].options        | opt.correct == true   | Exactly 1 dict with correct: true, or |
|                    |                        | or answer (str)       | answer in options x 1.                |
| odd-one-out        | items[].words          | correct (int) or      | Exactly 1 odd word. int in bounds;    |
|                    |                        | answer (str)          | answer in words x 1. Must match if    |
|                    |                        |                       | both specified.                       |
| pick-syllables     | act.syllables          | correctIndices (list) | Non-empty list of unique int indices; |
|                    | (or items[].syllables) |                       | all indices within bounds.            |
| select             | items[].options        | opt.correct == true   | >= max(floor, min_correct) correct    |
|                    |                        |                       | opts; floor is 1 at A2/B1, else 2.    |
+--------------------+------------------------+-----------------------+---------------------------------------+

Named Failure Reasons for Check 4:
- error_text_mismatch: item's error != record's incorrect, or incorrect not in sentence
- error_text_ambiguous: record's incorrect occurs more than once in sentence
- error_ref_mismatch: error_ref missing, not planned, or correction != record's correct
- answer_key_missing: no answer key specified for choices
- answer_key_ambiguous: key matches multiple options, duplicate options match key, or duplicate correctIndices
- answer_key_conflict: conflicting answer keys specified on same item
- answer_index_out_of_range: 0-based key index out of bounds
- answer_not_in_options: key text not found in offered options/words
- form_choice_options_invalid: form-choice options not unique, not in record, or answer tag mismatch
- form_sentence_missing: A1 form-choice item has no rendered sentence for its requirement receipt
- a1_case_contrast_under_negated_verb: A1 case-choice sentence contains the negation particle (A1 word-store
  record W-061) followed by a finite verb, without an adjacent preposition or agreeing adjective exemption
- a1_negation_particle_record_invalid: the A1 word store lacks W-061, or W-061 is not a particle bound to
  VESUM entry 226767 (store defect)
- select_correct_set_invalid: select activity has fewer correct options than required
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import unicodedata
import uuid
from collections import Counter
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.assemble import (
    check_5_assembly,
    check_9_stress_and_render,
    check_11_render,
)
from scripts.build.fresh.candidates import classify_form_analyses, item_candidates, option_record_bindings
from scripts.build.fresh.draft_schema import validate_draft
from scripts.build.fresh.listening import choice_error as listening_choice_error
from scripts.build.fresh.listening import model_target as listening_model_target
from scripts.build.fresh.manifest import unlink_current, write_manifest, write_manifest_error
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.build.fresh.regeneration import invalidate_lesson_resolution, load_ledger, record_failure, record_success
from scripts.build.fresh.writer import strip_markdown_fence
from scripts.curriculum.evidence import lock
from scripts.curriculum.evidence.tags import to_oracle
from scripts.curriculum.learner_state import codes as learner_codes
from scripts.curriculum.learner_state.inventory_gate import check_lesson
from scripts.curriculum.learner_state.observed import ObservedError, write_observed
from scripts.curriculum.resolver import codes, questions, receipts
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.narrow import learner_usable
from scripts.curriculum.resolver.stream import resolve
from scripts.curriculum.resolver.tokenize import Token, lookup_form, tokenize
from scripts.curriculum.validate.activity_report import draft_report
from scripts.review.digest.error import DigestError

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "fresh-lesson-gates-v1.schema.json"
QuestionDispatch = Callable[[dict[str, Any], str], dict[str, Any]]


def failure(
    check: int,
    reason: str,
    layer: str,
    *,
    code: str | None = None,
    step: str | None = None,
    activity: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "check": check,
        "status": "failed",
        "code": code or str(check),
        "reason": reason,
        "layer": layer,
    }
    for key, value in (("step", step), ("activity", activity), ("token", token)):
        if value is not None:
            row[key] = str(value)
    return row


def _pass(number: int, details: dict[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"check": number, "status": "passed"}
    if details is not None:
        row["details"] = details
    return row


def _inventory_layer(code: str) -> str:
    if code in {
        learner_codes.PLAN_NOT_FOUND,
        learner_codes.PLAN_YAML_INVALID,
        learner_codes.PRIOR_PLANS_MISSING,
        learner_codes.POSITION_NOT_FOUND,
        learner_codes.LESSON_NOT_FOUND,
        learner_codes.LEMMA_OUTSIDE_STATE,
    }:
        return "plan"
    if code in {
        learner_codes.BASE_LAYER_MISSING,
        learner_codes.BASE_LAYER_UNRESOLVED,
        learner_codes.PENDING_STRESS,
        learner_codes.LOCK_MISMATCH,
    }:
        return "pack"
    if code in {
        learner_codes.EXPANDED_DOCUMENT_MISSING,
        learner_codes.EXPANDED_DOCUMENT_MISMATCH,
        learner_codes.RESOLUTIONS_NOT_FOUND,
        learner_codes.RESOLUTIONS_INVALID,
        learner_codes.UNKNOWN_TAB,
    }:
        return "engine"
    return "writer"


def _lesson(plan: dict[str, Any], n: int) -> dict[str, Any]:
    return next(item for item in plan["lessons"] if item["n"] == n)


def _gap_layer(gaps: list[dict[str, Any]], lesson: dict[str, Any]) -> str:
    """A missing record belongs to the pack; a quote host outside the plan requires replanning.

    A dialogue or T-record cited on the gap's own step is a possible host. Availability/rights gaps in
    that record stay with the pack; this mapping never decides semantic host adequacy.
    """
    steps = lesson.get("steps") or []
    for gap in gaps:
        if gap["need"] not in {"quote", "publication_right"}:
            continue
        step = next(step for step in steps if step["id"] == gap["step"])
        dialogue_step = (lesson.get("dialogue") or {}).get("step")
        if dialogue_step == gap["step"]:
            continue
        if not any(ref.startswith("T-") for ref in step.get("evidence") or []):
            return "plan"
    return "pack"


def check_3_structure(draft: dict[str, Any], lesson: dict[str, Any]) -> dict[str, Any]:
    steps = lesson.get("steps") or []
    dsteps = draft.get("steps") or []
    if [s["id"] for s in dsteps] != [s["id"] for s in steps]:
        return failure(3, "step_ids_or_order", "writer")
    plan_acts = {a["id"]: a for a in lesson.get("activities") or []}
    if [a["id"] for a in draft.get("activities") or []] != list(plan_acts):
        return failure(3, "activity_ids_or_order", "writer")
    expected_consolidation = lesson.get("consolidation") or []
    if draft["consolidation"]["activities"] != expected_consolidation:
        return failure(3, "consolidation_activities", "writer")
    for activity in draft.get("activities") or []:
        # Only quiz has listening items in the A1 schema. Other families may
        # have non-object items, and their shape is owned by schema/check 4.
        if plan_acts[activity["id"]]["type"] != "quiz":
            continue
        for index, item in enumerate(activity.get("items") or []):
            if item.get("kind") == "listening" and (
                (item.get("host") or {}).get("kind") != "video"
                or not _host_eligible(item.get("host"), draft, lesson, activity["id"])
            ):
                return failure(
                    3,
                    "listening_host_ineligible",
                    "writer",
                    code="listening_host_ineligible",
                    activity=activity["id"],
                    token=str(index),
                )
    used: set[str] = set()
    for planned, actual in zip(steps, dsteps, strict=True):
        sid = planned["id"]
        blocks = actual.get("blocks") or []
        refs = [b.get("ref") for b in blocks if b["kind"] == "activity"]
        if refs != (planned.get("practice") or []):
            return failure(3, "step_practice_order", "writer", step=sid)
        host = (lesson.get("dialogue") or {}).get("step")
        if sum(b["kind"] == "dialogue" for b in blocks) != int(host == sid):
            return failure(3, "dialogue_placement", "writer", step=sid)
        expected = set(planned.get("evidence") or [])
        cited = set()
        text_seen = False
        for block in blocks:
            kind = block["kind"]
            if kind in {"dialogue", "quote"}:
                text_seen = True
            if kind == "activity":
                aid = block["ref"]
                if plan_acts.get(aid, {}).get("type") == "true-false" and not text_seen:
                    return failure(3, "true_false_before_text", "writer", step=sid, activity=aid)
                continue
            cited.update(block.get("explains") or [])
            if block.get("ref"):
                cited.add(block["ref"])
        if not expected <= cited:
            return failure(3, f"evidence_missing: {sorted(expected - cited)}", "writer", step=sid)
        used |= cited
    allowed = {e for s in steps for e in s.get("evidence") or []}
    allowed.update(v["evidence"] for v in lesson.get("videos") or [] if isinstance(v, dict) and "evidence" in v)
    if used - allowed:
        return failure(3, f"evidence_not_in_plan: {sorted(used - allowed)}", "writer")
    return _pass(3)


def _forms(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["form"]: f for f in record.get("forms") or [] if f.get("learner") is True}


_VOWELS = frozenset(chr(code) for code in (0x430, 0x435, 0x438, 0x456, 0x457, 0x43E, 0x443, 0x44F, 0x44E, 0x454))
_A1_GROUPS = frozenset({"Gender", "Number", "Case", "Person", "VerbForm"})
_CHOICE_TYPES = frozenset(
    {"quiz", "multiple-choice", "fill-in", "odd-one-out", "error-correction", "translate", "image-to-letter"}
)
# Every activities-a1.schema.json family has an explicit check-7 owner/container.
# check_4 delegates schema/structural/key validation; these families have no
# per-item kind or single-choice semantics (order.items, for example, are strings).
_A1_CHECK_7_RULES = {
    "anagram": "check_4",
    "classify": "check_4",  # Schema-allowed, but forbidden by the fresh A1 contract.
    "count-syllables": "check_4",
    "divide-words": "check_4",
    "error-correction": "options",
    "fill-in": "options",
    "group-sort": "groups",
    "image-to-letter": "options",
    "letter-grid": "check_4",
    "match-up": "check_4",
    "observe": "check_4",
    "odd-one-out": "words",
    "order": "check_4",
    "phrase-table": "check_4",
    "pick-syllables": "check_4",  # Multiple indices, not one choice key.
    "quiz": "options",
    "translate": "options",  # Free production without options stays with check 4/review.
    "true-false": "boolean",
    "unjumble": "check_4",
    "watch-and-repeat": "check_4",
    "multiple-choice": "options",  # Existing resolved-plan alias of quiz.
}


def _normal_letters(value: str) -> str:
    """Use the build's apostrophe folding, then ignore case, stress and punctuation."""
    from scripts.build.linear_pipeline import _VESUM_APOSTROPHE_TRANSLATION

    folded = unicodedata.normalize("NFD", value.translate(_VESUM_APOSTROPHE_TRANSLATION).casefold())
    return "".join(char for char in folded if unicodedata.category(char)[0] in {"L", "N"})


def _choice_text(option: Any) -> str | None:
    value = option.get("text") if isinstance(option, dict) else option
    return value if isinstance(value, str) else None


def _choice_key(item: dict[str, Any], typ: str, options: list[Any]) -> int | None:
    if typ in {"quiz", "multiple-choice"} and isinstance(item.get("_resolved_key_index"), int):
        return item["_resolved_key_index"]
    if typ in {"quiz", "multiple-choice"} and type(item.get("correct")) is int:
        return item["correct"]
    if typ == "true-false":
        answer = next((item[k] for k in ("correct", "is_true", "isTrue", "answer") if k in item), None)
        return (0 if answer else 1) if isinstance(answer, bool) else None
    marked = [i for i, option in enumerate(options) if isinstance(option, dict) and option.get("correct") is True]
    if len(marked) == 1:
        return marked[0]
    if typ == "odd-one-out" and isinstance(item.get("correct"), int):
        return item["correct"]
    answer = next((item[k] for k in ("answer", "correction", "letter") if isinstance(item.get(k), str)), None)
    matches = [i for i, option in enumerate(options) if _choice_text(option) == answer]
    return matches[0] if len(matches) == 1 else None


def _analyses(record: dict[str, Any] | None, surface: str) -> list[set[str]]:
    """Keep all learner analyses of one bound record and surface."""
    if record is None:
        return []
    return [
        set(to_oracle(form["tags"]))
        for form in record.get("forms") or []
        if learner_usable(form) and lookup_form(form["form"]) == lookup_form(surface)
    ]


# The verbal negation particle, named by two identities because the engine types no Ukrainian
# and its tags (`part`) do not distinguish it from other particles. The A1 word-store id is
# stable within the store (the registry allocates W- ids once and never reuses them); the
# record's own VESUM binding pins which particle it is, so a W-061 rebound to another
# particle refuses instead of silently missing negation. words-verify re-checks that binding
# against VESUM; this check reads only the store record.
NEGATION_PARTICLE_RECORD = "W-061"
NEGATION_PARTICLE_ENTRY = {"source": "vesum", "entry_id": 226767}


class NegationParticleRecordInvalid(LookupError):
    """The word store's NEGATION_PARTICLE_RECORD is missing or not the negation particle: a store defect."""


def negation_particle(records: dict[str, dict[str, Any]]) -> str:
    """Return the casefolded negation particle, copied from its word-store record's lemma."""
    record = records.get(NEGATION_PARTICLE_RECORD)
    lemma = record.get("lemma") if isinstance(record, dict) else None
    if not isinstance(record, dict) or record.get("pos") != "part" or not isinstance(lemma, str) or not lemma.strip():
        raise NegationParticleRecordInvalid(f"word store record {NEGATION_PARTICLE_RECORD} is not a particle")
    if record.get("entry") != NEGATION_PARTICLE_ENTRY:
        raise NegationParticleRecordInvalid(
            f"word store record {NEGATION_PARTICLE_RECORD} is not bound to VESUM entry "
            f"{NEGATION_PARTICLE_ENTRY['entry_id']}"
        )
    return lookup_form(lemma).casefold()


@dataclass(frozen=True)
class _WordTag:
    pos: str
    tags: str
    atoms: frozenset[str]


def _extract_word_tags(
    surface: str,
    records: dict[str, dict[str, Any]],
    vesum_lookup: Callable[[list[str]], dict[str, list[dict[str, Any]]]],
) -> list[_WordTag]:
    surface_norm = lookup_form(surface).casefold()
    seen: set[tuple[str, str]] = set()
    out: list[_WordTag] = []

    for record in records.values():
        if not isinstance(record, dict):
            continue
        for form in record.get("forms") or []:
            if (
                isinstance(form, dict)
                and learner_usable(form)
                and lookup_form(form.get("form", "")).casefold() == surface_norm
            ):
                tags = str(form.get("tags") or "")
                pos = str(form.get("pos") or record.get("pos") or (tags.split(":")[0] if tags else ""))
                key = (pos, tags)
                if key not in seen:
                    seen.add(key)
                    out.append(_WordTag(pos=pos, tags=tags, atoms=frozenset(tags.split(":"))))

    found = vesum_lookup([surface_norm])
    entries = found.get(surface_norm) or found.get(surface) or []
    for entry in entries:
        tags = str(entry.get("tags") or "")
        pos = str(entry.get("pos") or (tags.split(":")[0] if tags else ""))
        key = (pos, tags)
        if key not in seen:
            seen.add(key)
            out.append(_WordTag(pos=pos, tags=tags, atoms=frozenset(tags.split(":"))))

    return out


def _option_word_tags(
    record: dict[str, Any] | None,
    surface: str,
    records: dict[str, dict[str, Any]],
    vesum_lookup: Callable[[list[str]], dict[str, list[dict[str, Any]]]],
) -> list[_WordTag]:
    if record is not None:
        surface_norm = lookup_form(surface).casefold()
        res: list[_WordTag] = []
        for form in record.get("forms") or []:
            if (
                isinstance(form, dict)
                and learner_usable(form)
                and lookup_form(form.get("form", "")).casefold() == surface_norm
            ):
                tags = str(form.get("tags") or "")
                pos = str(form.get("pos") or record.get("pos") or (tags.split(":")[0] if tags else ""))
                res.append(_WordTag(pos=pos, tags=tags, atoms=frozenset(tags.split(":"))))
        if res:
            return res
    return _extract_word_tags(surface, records, vesum_lookup)


def _analysis_features(analysis: _WordTag) -> dict[str, str | None]:
    atoms = analysis.atoms
    case = None
    if "v_naz" in atoms:
        case = "Nom"
    elif "v_rod" in atoms:
        case = "Gen"
    elif "v_dav" in atoms:
        case = "Dat"
    elif "v_zna" in atoms:
        case = "Acc"
    elif "v_oru" in atoms:
        case = "Ins"
    elif "v_mis" in atoms:
        case = "Loc"
    elif "v_kly" in atoms:
        case = "Voc"

    number = None
    if atoms & {"p", "ns"}:
        number = "Plur"
    elif atoms & {"s", "m", "f", "n"}:
        number = "Sing"

    gender = None
    if number != "Plur":
        if "m" in atoms:
            gender = "Masc"
        elif "f" in atoms:
            gender = "Fem"
        elif "n" in atoms:
            gender = "Neut"

    animacy = None
    if "ranim" in atoms:
        animacy = "ranim"
    elif "rinanim" in atoms:
        animacy = "rinanim"
    elif "unanim" in atoms:
        animacy = "unanim"
    elif "anim" in atoms:
        animacy = "anim"
    elif "inanim" in atoms:
        animacy = "inanim"

    return {
        "case": case,
        "number": number,
        "gender": gender,
        "animacy": animacy,
    }


def _animacy_matches_accusative(mod_anim: str | None, noun_anim: str | None) -> bool:
    if mod_anim == "unanim" or noun_anim == "unanim":
        return True
    if mod_anim in {"ranim", "anim"}:
        return noun_anim in {"anim", "unanim"}
    if mod_anim in {"rinanim", "inanim"}:
        return noun_anim in {"inanim", "unanim"}
    return True


def _analysis_agrees(mod_feat: dict[str, str | None], noun_feat: dict[str, str | None], case_target: str) -> bool:
    if mod_feat["case"] != case_target or noun_feat["case"] != case_target:
        return False
    if mod_feat["number"] != noun_feat["number"] or mod_feat["number"] is None:
        return False
    if mod_feat["number"] == "Sing" and (mod_feat["gender"] != noun_feat["gender"] or mod_feat["gender"] is None):
        return False
    return case_target != "Acc" or _animacy_matches_accusative(mod_feat["animacy"], noun_feat["animacy"])


def _option_agrees_with_run(
    option_analyses: list[dict[str, str | None]],
    run_token_analyses: list[list[dict[str, str | None]]],
) -> bool:
    for case_target in ("Gen", "Acc"):
        for noun_feat in option_analyses:
            if noun_feat["case"] != case_target:
                continue
            if all(
                any(_analysis_agrees(mod_feat, noun_feat, case_target) for mod_feat in mod_analyses)
                for mod_analyses in run_token_analyses
            ):
                return True
    return False


def _is_unambiguous_adj(tags_list: list[_WordTag]) -> bool:
    if not tags_list:
        return False
    for t in tags_list:
        if t.pos == "numr":
            return False
        if not ("adj" in t.atoms or t.pos == "adj"):
            return False
        if t.atoms & {"adv", "noun", "predic", "verb"}:
            return False
    return True


def a1_case_contrast_under_negated_verb(
    item: dict[str, Any],
    records: dict[str, dict[str, Any]],
    activity_type: str,
    *,
    vesum_lookup: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
) -> bool:
    """Refuse an A1 case contrast under a negated finite verb unless E1 or E3 applies.

    Rule rev 6.5 (closes Sol blocker 1 and adopts E1/E3 exemptions).
    """
    options = item.get("options") or []
    bindings = option_record_bindings(item, activity_type)
    if len(bindings) != len(options) or len(options) < 2:
        return False
    case_sets = []
    for record_id, option in zip(bindings, options, strict=True):
        text = _choice_text(option)
        analyses = _analyses(records.get(record_id), text) if isinstance(text, str) else []
        case_sets.append(frozenset(atom for analysis in analyses for atom in analysis if atom.startswith("Case=")))
    if not all(case_sets) or len(set(case_sets)) <= 1:
        return False

    sentence = receipts.requirement_sentence(item)
    tokens = tokenize(sentence)
    if len(tokens) < 2:
        return False
    particle = negation_particle(records)
    successors = [
        tokens[index + 1].lookup.casefold()
        for index, token in enumerate(tokens[:-1])
        if token.lookup.casefold() == particle and sentence[token.end : tokens[index + 1].start].isspace()
    ]
    if not successors:
        return False

    if vesum_lookup is None:
        from scripts.verification.vesum import verify_words

        def vesum_lookup(words: list[str]) -> dict[str, list[dict[str, Any]]]:
            return verify_words(words, db_path=os.environ.get("VESUM_DB_PATH"))

    has_negated_verb = False
    for surface in successors:
        tags_list = _extract_word_tags(surface, records, vesum_lookup)
        if any("VerbForm=Fin" in to_oracle(t.tags) for t in tags_list):
            has_negated_verb = True
            break
    if not has_negated_verb:
        return False

    # Check exemptions E1 and E3
    blank_match = re.search(r"_{2,}|\[blank\]", sentence)
    if blank_match is None:
        return True
    blank_start = blank_match.start()

    tokens_before = [t for t in tokens if t.end <= blank_start]
    if not tokens_before:
        return True

    t_last = tokens_before[-1]
    gap_to_blank = sentence[t_last.end : blank_start]
    if gap_to_blank.strip() != "" or not (not gap_to_blank or gap_to_blank.isspace()):
        return True

    # E1 — adjacent preposition
    t_last_surface = t_last.lookup.casefold()
    t_last_tags = _extract_word_tags(t_last_surface, records, vesum_lookup)
    if t_last_tags and all(t.pos == "prep" or "prep" in t.atoms for t in t_last_tags):
        return False

    # E3 — adjacent unambiguous adjectives
    run_tokens: list[tuple[Token, list[_WordTag]]] = []
    for i in range(len(tokens_before) - 1, -1, -1):
        tok = tokens_before[i]
        if run_tokens:
            next_tok = run_tokens[0][0]
            gap = sentence[tok.end : next_tok.start]
            if gap.strip() != "" or not (not gap or gap.isspace()):
                break
        surface = tok.lookup.casefold()
        tags_list = _extract_word_tags(surface, records, vesum_lookup)
        if not _is_unambiguous_adj(tags_list):
            break
        run_tokens.insert(0, (tok, tags_list))

    if run_tokens:
        run_features = [[_analysis_features(tag) for tag in tags_list] for _, tags_list in run_tokens]
        agreeing_options: list[Any] = []
        for option, record_id in zip(options, bindings, strict=True):
            opt_text = _choice_text(option)
            if not isinstance(opt_text, str):
                continue
            opt_tags = _option_word_tags(records.get(record_id), opt_text, records, vesum_lookup)
            opt_features = [_analysis_features(t) for t in opt_tags]
            if _option_agrees_with_run(opt_features, run_features):
                agreeing_options.append(option)
        if len(agreeing_options) == 1:
            return False

    return True


def _admitted(analyses: list[set[str]], demand: dict[str, str]) -> bool:
    required = {f"{group}={value}" for group, value in demand.items()}
    return any(required <= analysis for analysis in analyses)


def _independent_language_question(provenance: Any, state_dir: Path, lesson_n: int) -> bool:
    """A question receipt counts only when its language seat differs from the writer's family."""
    from scripts.review.second_seat import IdentityError, writer_family

    if not isinstance(provenance, str):
        return False
    match = re.fullmatch(r"question:([^:]+):Q-[0-9]{3,}", provenance)
    if match is None:
        return False
    try:
        return receipts.language_seat_family(match.group(1), what="question") != writer_family(state_dir, lesson_n)
    except (ResolverError, IdentityError):
        return False


def _host_eligible(host: Any, draft: dict[str, Any], lesson: dict[str, Any], activity_id: str) -> bool:
    if not isinstance(host, dict) or host.get("kind") not in {"dialogue", "quote", "video"}:
        return False
    if host["kind"] == "video" and host.get("ref") not in {
        v.get("evidence") for v in lesson.get("videos") or [] if isinstance(v, dict)
    }:
        return False
    if host["kind"] == "dialogue" and not lesson.get("dialogue"):
        return False
    for step in draft.get("steps") or []:
        for block in step.get("blocks") or []:
            if block.get("kind") == "activity" and block.get("ref") == activity_id:
                return False
            if block.get("kind") != host["kind"]:
                continue
            if host["kind"] == "dialogue" or block.get("ref") == host.get("ref"):
                return True
    return False


def check_7_a1_choices(
    draft: dict[str, Any],
    lesson: dict[str, Any],
    words: dict[str, Any],
    stream: Any,
    *,
    state_dir: Path,
    lesson_n: int,
    requirement_inputs: dict[str, Any] | None = None,
    vesum_lookup: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    sources: Any = None,
    pack: dict[str, Any] | None = None,
    allowlist: Allowlist | None = None,
) -> dict[str, Any]:
    """Check A1 choice uniqueness after resolution; never infer a slot's demand."""
    if sources is None:
        from scripts.curriculum.evidence.sources import Sources

        with Sources() as client:
            return check_7_a1_choices(
                draft,
                lesson,
                words,
                stream,
                state_dir=state_dir,
                lesson_n=lesson_n,
                requirement_inputs=requirement_inputs,
                vesum_lookup=vesum_lookup,
                sources=client,
                pack=pack,
                allowlist=allowlist,
            )
    by_id = {record["id"]: record for record in words.get("words") or []}
    receipt_doc = receipts.read_requirement_receipts(
        receipts.requirement_receipt_path(state_dir, lesson_n), sources=sources
    )
    completeness: list[dict[str, Any]] = []
    if vesum_lookup is None:
        from scripts.verification.vesum import verify_words

        def vesum_lookup(words: list[str]) -> dict[str, list[dict[str, Any]]]:
            return verify_words(words, db_path=os.environ.get("VESUM_DB_PATH"))

    def bad(reason: str, aid: str, index: int) -> dict[str, Any]:
        return failure(7, reason, "writer", code=reason, activity=aid, token=str(index))

    for activity in draft.get("activities") or []:
        aid = activity["id"]
        typ = activity.get("type") or next(
            (act["type"] for act in lesson.get("activities") or [] if act["id"] == aid), None
        )
        rule = _A1_CHECK_7_RULES.get(typ)
        if rule is None:
            return failure(
                7, "choice_activity_type_invalid", "writer", code="choice_activity_type_invalid", activity=aid
            )
        if rule == "check_4":
            continue
        if rule == "groups" and activity.get("grouping_feature"):
            feature = activity["grouping_feature"]
            for group_idx, group in enumerate(activity.get("groups") or []):
                value = group.get("value")
                for entry_idx, entry in enumerate(group.get("items") or []):
                    index = sum(len(g.get("items") or []) for g in activity["groups"][:group_idx]) + entry_idx
                    if not isinstance(entry, dict):
                        return bad("group_entry_record_missing", aid, index)
                    record = by_id.get(entry.get("record"))
                    analyses = _analyses(record, entry.get("text", ""))
                    if not analyses or not _admitted(analyses, {feature: value}):
                        return bad("group_entry_not_admitted", aid, index)
                    other_values = {g.get("value") for g in activity["groups"] if g is not group}
                    if any(_admitted(analyses, {feature: other}) for other in other_values):
                        # An ambiguous form needs an independent language judgement.
                        confirmed = any(
                            token.get("unit", {}).get("activity") == aid
                            and token.get("unit", {}).get("block") == f"group_{group_idx}_{entry_idx}"
                            and _independent_language_question(token.get("provenance"), state_dir, lesson_n)
                            for token in stream.tokens
                        )
                        if not confirmed:
                            return bad("group_entry_ambiguous_without_receipt", aid, index)
        if rule == "groups":
            continue
        for index, item in enumerate(activity.get("items") or []):
            kind = item.get("kind")
            if kind is None:
                continue
            options = [True, False] if rule == "boolean" else item.get(rule)
            if kind == "comprehension" and (
                (item.get("host") or {}).get("kind") not in {"dialogue", "quote"}
                or not _host_eligible(item.get("host"), draft, lesson, aid)
            ):
                return bad("comprehension_host_ineligible", aid, index)
            if kind == "listening":
                if typ != "quiz":
                    return bad("listening_type_invalid", aid, index)
                if (item.get("host") or {}).get("kind") != "video" or not _host_eligible(
                    item.get("host"), draft, lesson, aid
                ):
                    return bad("listening_host_ineligible", aid, index)
            if not isinstance(options, list) or not options:
                if kind == "listening":
                    return bad("listening_options_missing", aid, index)
                continue
            key = _choice_key(item, typ, options)
            if key is None or key >= len(options):
                return bad("answer_key_missing", aid, index)
            texts = [_choice_text(option) for option in options]
            if kind == "listening":
                target_ref = item.get("target_record")
                planned_letters = (
                    set(allowlist.letters)
                    if allowlist
                    else {
                        letter.casefold()
                        for letter in (lesson.get("inventory", {}).get("phonetics") or {}).get("letters") or []
                    }
                )
                if (
                    isinstance(target_ref, str)
                    and not target_ref.startswith("W-")
                    and target_ref.casefold() not in planned_letters
                ):
                    return bad("listening_target_not_planned", aid, index)
                target, error = listening_model_target(target_ref, item["host"]["ref"], pack or {}, words)
                if error:
                    return failure(7, error, "pack", code=error, activity=aid, token=str(index))
                error = listening_choice_error(
                    item,
                    texts,
                    key,
                    target,
                    words,
                    letters=planned_letters,
                    record_ids=set(allowlist.records) if allowlist else set(by_id),
                )
                if error:
                    return bad(error, aid, index)
                continue
            if kind in {"form", "vocabulary"}:
                ids = [item.get("record")] * len(options) if typ == "fill-in" else item.get("option_records")
                if not isinstance(ids, list) or len(ids) != len(options) or any(rid not in by_id for rid in ids):
                    return bad("option_record_missing", aid, index)
                bound = [by_id[rid] for rid in ids]
            else:
                bound = []
            if kind != "form" and all(isinstance(text, str) for text in texts):
                common = None
                spellings = [lookup_form(text).casefold() for text in texts]
                verified = vesum_lookup(spellings)
                for spelling in spellings:
                    lemmas = {analysis.get("lemma") for analysis in verified.get(spelling, [])}
                    common = lemmas if common is None else common & lemmas
                if common:
                    return bad("same_lemma_requires_form_kind", aid, index)
            if kind == "form":
                demand = item.get("requires") or {}
                if item.get("tests_feature") not in demand or not set(demand) <= _A1_GROUPS:
                    return bad("form_requires_invalid", aid, index)
                if any(
                    not isinstance(text, str) or not _analyses(rec, text)
                    for rec, text in zip(bound, texts, strict=True)
                ):
                    return bad("form_option_without_analysis", aid, index)
                classifications = [
                    classify_form_analyses(_analyses(rec, text), demand) for rec, text in zip(bound, texts, strict=True)
                ]
                if "undecidable" in classifications:
                    return bad("form_option_missing_required_group", aid, index)
                if [state == "admitted" for state in classifications] != [i == key for i in range(len(options))]:
                    return bad("form_not_unique_for_requires", aid, index)
                sentence = receipts.requirement_sentence(item)
                if not sentence and (
                    (typ == "fill-in" and item.get("mode") == "form-choice") or typ in {"quiz", "multiple-choice"}
                ):
                    return bad("form_sentence_missing", aid, index)
                status = receipts.requirement_status(
                    receipt_doc,
                    lesson=stream.lesson,
                    state_dir=state_dir,
                    inputs=requirement_inputs if requirement_inputs is not None else stream.inputs,
                    activity=aid,
                    item=index,
                    payload_sha256=receipts.requirement_payload_sha256(sentence, texts, key, demand),
                    options=texts,
                    key_index=key,
                    requires=demand,
                    sources=sources,
                )
                if status != "confirmed":
                    return bad(status, aid, index)
                completeness.append({"activity": aid, "item": index, "requirement": status})
            elif kind == "vocabulary":
                target = item.get("target_record")
                lemmas = [record.get("lemma") for record in bound]
                if (
                    ids[key] != target
                    or len(set(lemmas)) != len(lemmas)
                    or any(
                        not isinstance(text, str) or not _analyses(record, text)
                        for record, text in zip(bound, texts, strict=True)
                    )
                ):
                    return bad("vocabulary_target_not_unique", aid, index)
            elif kind == "orthography":
                if typ != "fill-in" or item.get("mode") != "orthography":
                    return bad("orthography_mode_invalid", aid, index)
                sentence = item.get("sentence", "")
                target = by_id.get(item.get("target_record"))
                # The target is the completed word, not the whole sentence.
                slot = re.search(r"_{3,}|\[blank\]", sentence)
                if slot is None:
                    return bad("orthography_slot_missing", aid, index)
                start, end = slot.span()
                while start and (sentence[start - 1].isalpha() or sentence[start - 1] in "'’ʼ`‘"):
                    start -= 1
                while end < len(sentence) and (sentence[end].isalpha() or sentence[end] in "'’ʼ`‘"):
                    end += 1
                left, right = sentence[start : slot.start()], sentence[slot.end() : end]
                completed = [lookup_form(left + text + right) for text in texts]
                if not _analyses(target, completed[key]):
                    return bad("orthography_target_invalid", aid, index)
                found = vesum_lookup(completed)
                if any(found.get(word) for i, word in enumerate(completed) if i != key):
                    return bad("orthography_distractor_is_word", aid, index)
            elif kind != "comprehension":
                return bad("choice_kind_invalid", aid, index)
    details = {"requirement_receipts": completeness}
    if receipt_doc is not None:
        evidence = receipts.resolve_requirement_evidence(receipt_doc, sources=sources)
        details["requirement_evidence"] = {"sha256": evidence.content_hash, "sources": evidence.metadata}
    return _pass(7, details)


def _structural_activity_error(activity: dict[str, Any], typ: str, records: dict[str, dict[str, Any]]) -> str | None:
    """Checks that do not depend on resolution or a contextual language judgement."""
    if typ == "classify":
        return "classify_forbidden"
    if typ == "order":
        order = activity.get("correct_order")
        items = activity.get("items")
        if (
            not isinstance(items, list)
            or not isinstance(order, list)
            or any(type(index) is not int for index in order)
            or sorted(order) != list(range(len(items)))
        ):
            return "order_index_coverage"
    if typ == "pick-syllables" and not activity.get("explanation"):
        return "pick_syllables_explanation_missing"
    if typ == "match-up":
        if activity.get("left_role") not in {"form", "gloss", "question", "answer"} or activity.get(
            "right_role"
        ) not in {"form", "gloss", "question", "answer"}:
            return "match_up_role_invalid"
        for pair in activity.get("pairs") or []:
            if not isinstance(pair, dict) or not pair.get("why"):
                return "match_up_why_missing"
            for side in ("left", "right"):
                if activity[f"{side}_role"] == "form":
                    record = records.get(pair.get(f"{side}_record"))
                    if record is None or not any(
                        form.get("learner") is True and form.get("form") == pair.get(side)
                        for form in record.get("forms") or []
                    ):
                        return "match_up_form_record_invalid"
    for item in activity.get("items") or []:
        if not isinstance(item, dict):
            continue
        if typ == "divide-words":
            parts = item.get("answer", "").split("-")
            if (
                len(parts) < 2
                or any(not part or sum(char.casefold() in _VOWELS for char in part) != 1 for part in parts)
                or "".join(parts).casefold() != str(item.get("word", "")).casefold()
            ):
                return "divide_words_parts_invalid"
        if typ == "count-syllables":
            count = sum(char.casefold() in _VOWELS for char in str(item.get("word", "")))
            if type(item.get("correct")) is not int or item["correct"] != count:
                return "count_syllables_key_invalid"
        if typ in {"anagram", "unjumble"}:
            from scripts.build.activity_renderer import unjumble_tokens

            pieces = item.get("letters") if typ == "anagram" else unjumble_tokens(item)
            answer = item.get("answer")
            if (
                not isinstance(pieces, list)
                or not isinstance(answer, str)
                or Counter(_normal_letters("".join(map(str, pieces)))) != Counter(_normal_letters(answer))
            ):
                return f"{typ.replace('-', '_')}_multiset_mismatch"
            if typ == "anagram" and not any(
                form.get("learner") is True and _normal_letters(form.get("form", "")) == _normal_letters(answer)
                for record in records.values()
                for form in record.get("forms") or []
            ):
                return "anagram_key_not_store_form"
        if typ == "translate" and item.get("options") and item.get("alternatives"):
            return "translate_alternatives_forbidden"
        if typ in _CHOICE_TYPES or typ == "true-false":
            options = item.get("words") if typ == "odd-one-out" else item.get("options")
            options = [True, False] if typ == "true-false" else options
            if not isinstance(options, list) or not options:
                continue  # The fresh constraint and per-type key checks own missing options.
            why = item.get("option_why")
            if (
                not isinstance(why, list)
                or len(why) != len(options)
                or any(not isinstance(entry, str) or not entry.strip() for entry in why)
            ):
                return "option_why_alignment"
            if _choice_key(item, typ, options) is None:
                return "answer_key_missing"
    return None


def check_4_activities(
    draft: dict[str, Any],
    lesson: dict[str, Any],
    words: dict[str, Any],
    pack: dict[str, Any],
    *,
    level: str | None = None,
    vesum_lookup: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
) -> tuple[dict[str, Any], dict[tuple[str, int], list[dict[str, Any]]]]:
    mod_level = (
        (level or "").lower()
        or draft.get("lesson", {}).get("module", "").split("/")[0].lower()
        or lesson.get("level", "").lower()
    )
    records = {w["id"]: w for w in words.get("words") or []}
    errors = {e["id"]: e for e in pack.get("errors") or []}
    planned = {a["id"]: a for a in lesson.get("activities") or []}
    for step in draft.get("steps") or []:
        for block in step.get("blocks") or []:
            if block.get("kind") == "video" and block.get("target_record"):
                ref = block.get("ref")
                if ref not in {v.get("evidence") for v in lesson.get("videos") or []}:
                    return failure(4, "listening_host_ineligible", "writer", code="listening_host_ineligible"), {}
                _, error = listening_model_target(block["target_record"], ref, pack, words)
                if error:
                    return failure(4, error, "pack", code=error, step=step.get("id")), {}
    form_options: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for activity in draft.get("activities") or []:
        aid = activity["id"]
        typ = planned[aid]["type"]

        if typ == "pick-syllables" and "syllables" in activity:
            syls = activity.get("syllables") or []
            if "correctIndices" not in activity or activity.get("correctIndices") is None:
                return failure(4, "answer_key_missing", "writer", activity=aid), {}
            corr_indices = activity.get("correctIndices") or []
            if len(corr_indices) == 0:
                return failure(4, "answer_key_missing", "writer", activity=aid), {}
            for ci in corr_indices:
                if not isinstance(ci, int) or not (0 <= ci < len(syls)):
                    return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(ci)), {}
            if len(corr_indices) != len(set(corr_indices)):
                return failure(4, "answer_key_ambiguous", "writer", activity=aid), {}

        # order.items are strings; its permutation is checked below rather
        # than by the per-object answer-key and choice rules.
        items = [] if typ == "order" else activity.get("items") or []
        for idx, item in enumerate(items):
            if typ == "fill-in" and item.get("mode") == "form-choice":
                record = records.get(item.get("record"))
                forms = _forms(record) if record else {}
                options = item.get("options") or []
                selected = [forms.get(opt) for opt in options]
                answer_form = (
                    next((f for f in record.get("forms") or [] if f.get("tags") == item.get("answer_tags")), None)
                    if record
                    else None
                )
                if (
                    len(options) != len(set(options))
                    or any(f is None for f in selected)
                    or answer_form is None
                    or answer_form.get("form") not in options
                    or item.get("answer") != answer_form.get("form")
                ):
                    return failure(4, "form_choice_options_invalid", "writer", activity=aid, token=str(idx)), {}
                form_options[(aid, idx)] = selected

            elif typ == "fill-in" and item.get("options") and item.get("mode") != "form-choice":
                ans = item.get("answer")
                opts = item.get("options") or []
                if ans is None or not isinstance(ans, str):
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                matched = [i for i, opt in enumerate(opts) if opt == ans]
                if len(matched) == 0:
                    return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                if len(matched) > 1:
                    return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

            if typ == "error-correction":
                er = errors.get(item.get("error_ref"))
                if er is None or item.get("error_ref") not in (planned[aid].get("error_refs") or []):
                    return failure(4, "error_ref_mismatch", "writer", activity=aid, token=str(idx)), {}
                rec_incorrect = er.get("incorrect")
                if item.get("error") != rec_incorrect:
                    return failure(4, "error_text_mismatch", "writer", activity=aid, token=str(idx)), {}
                sentence = item.get("sentence", "")
                if rec_incorrect not in sentence:
                    return failure(4, "error_text_mismatch", "writer", activity=aid, token=str(idx)), {}
                if sentence.count(rec_incorrect) > 1:
                    return failure(4, "error_text_ambiguous", "writer", activity=aid, token=str(idx)), {}
                has_corr = "correction" in item and item["correction"] is not None
                has_ans = "answer" in item and item["answer"] is not None
                if not has_corr and not has_ans:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                if has_corr and has_ans and item["correction"] != item["answer"]:
                    return failure(4, "answer_key_conflict", "writer", activity=aid, token=str(idx)), {}
                corr = item["correction"] if has_corr else item["answer"]
                if er.get("correct") != corr:
                    return failure(4, "error_ref_mismatch", "writer", activity=aid, token=str(idx)), {}
                if item.get("options"):
                    opts = item["options"]
                    if corr not in opts:
                        return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                    if opts.count(corr) > 1:
                        return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

            if typ in {"quiz", "multiple-choice"}:
                options = item.get("options") or []
                offered = [option.get("text") if isinstance(option, dict) else option for option in options]
                has_int = "correct" in item and isinstance(item["correct"], int)
                has_str = "answer" in item and isinstance(item["answer"], str)
                dict_correct = [
                    i for i, opt in enumerate(options) if isinstance(opt, dict) and opt.get("correct") is True
                ]

                if len(dict_correct) > 1:
                    return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

                if has_int and not (0 <= item["correct"] < len(options)):
                    return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(idx)), {}

                str_matched_indices = []
                if has_str:
                    str_matched_indices = [i for i, opt_txt in enumerate(offered) if opt_txt == item["answer"]]
                    if len(str_matched_indices) == 0:
                        return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                    if len(str_matched_indices) > 1:
                        return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

                if not has_int and not has_str and len(dict_correct) == 0:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}

                resolved_indices = set()
                if has_int:
                    resolved_indices.add(item["correct"])
                if str_matched_indices:
                    resolved_indices.add(str_matched_indices[0])
                if dict_correct:
                    resolved_indices.add(dict_correct[0])
                if len(resolved_indices) > 1:
                    return failure(4, "answer_key_conflict", "writer", activity=aid, token=str(idx)), {}

                item["_resolved_key_index"] = next(iter(resolved_indices))

            if (
                mod_level == "a1"
                and item.get("kind") == "form"
                and ((typ == "fill-in" and item.get("mode") == "form-choice") or typ in {"quiz", "multiple-choice"})
                and not receipts.requirement_sentence(item)
            ):
                return failure(
                    4, "form_sentence_missing", "writer", code="form_sentence_missing", activity=aid, token=str(idx)
                ), {}
            try:
                negated_case = mod_level == "a1" and a1_case_contrast_under_negated_verb(
                    item, records, typ, vesum_lookup=vesum_lookup
                )
            except NegationParticleRecordInvalid as err:
                return failure(
                    4,
                    f"a1_negation_particle_record_invalid: {err}",
                    "word_store",
                    code="a1_negation_particle_record_invalid",
                ), {}
            except (OSError, sqlite3.Error) as err:
                return failure(
                    4, f"a1_choice_source_unavailable: {err}", "pack", code="a1_choice_source_unavailable"
                ), {}
            if negated_case:
                return failure(
                    4,
                    "a1_case_contrast_under_negated_verb",
                    "writer",
                    code="a1_case_contrast_under_negated_verb",
                    activity=aid,
                    token=str(idx),
                ), {}
            if (
                mod_level == "a1"
                and item.get("kind") == "form"
                and ((typ == "fill-in" and item.get("mode") == "form-choice") or typ in {"quiz", "multiple-choice"})
            ):
                generated = item_candidates(item, words, typ)
                offered = {(candidate["record"], candidate["form"]) for candidate in generated}
                options = item.get("options") or []
                bindings = option_record_bindings(item, typ)
                if len(bindings) != len(options) or any(
                    (record_id, _choice_text(option)) not in offered
                    for record_id, option in zip(bindings, options, strict=True)
                ):
                    return failure(
                        4,
                        "form_candidate_not_generated",
                        "writer",
                        code="form_candidate_not_generated",
                        activity=aid,
                        token=str(idx),
                    ), {}

            if typ == "odd-one-out" and "words" in item:
                words_list = item.get("words") or []
                has_int = "correct" in item and isinstance(item["correct"], int)
                has_str = "answer" in item and isinstance(item["answer"], str)
                if not has_int and not has_str:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                if has_int and not (0 <= item["correct"] < len(words_list)):
                    return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(idx)), {}
                str_idx = None
                if has_str:
                    matched = [i for i, w in enumerate(words_list) if w == item["answer"]]
                    if len(matched) == 0:
                        return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                    if len(matched) > 1:
                        return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}
                    str_idx = matched[0]
                if has_int and has_str and item["correct"] != str_idx:
                    return failure(4, "answer_key_conflict", "writer", activity=aid, token=str(idx)), {}

            if typ == "image-to-letter" and item.get("options"):
                letter = item.get("letter")
                opts = item.get("options") or []
                if letter is None or not isinstance(letter, str):
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                matched = [i for i, opt in enumerate(opts) if opt == letter]
                if len(matched) == 0:
                    return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                if len(matched) > 1:
                    return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

            if typ == "translate" and item.get("options"):
                opts = item.get("options") or []
                dict_correct = [i for i, opt in enumerate(opts) if isinstance(opt, dict) and opt.get("correct") is True]
                has_str = "answer" in item and isinstance(item["answer"], str)
                if not has_str and len(dict_correct) == 0:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                if len(dict_correct) > 1:
                    return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}
                str_idx = None
                if has_str:
                    matched = [
                        i
                        for i, opt in enumerate(opts)
                        if (opt.get("text") if isinstance(opt, dict) else opt) == item["answer"]
                    ]
                    if len(matched) == 0:
                        return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
                    if len(matched) > 1:
                        return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}
                    str_idx = matched[0]
                if dict_correct and str_idx is not None and dict_correct[0] != str_idx:
                    return failure(4, "answer_key_conflict", "writer", activity=aid, token=str(idx)), {}

            if typ == "pick-syllables" and "syllables" in item:
                syls = item.get("syllables") or []
                if "correctIndices" not in item or item.get("correctIndices") is None:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                corr_indices = item.get("correctIndices") or []
                if len(corr_indices) == 0:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                for ci in corr_indices:
                    if not isinstance(ci, int) or not (0 <= ci < len(syls)):
                        return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(ci)), {}
                if len(corr_indices) != len(set(corr_indices)):
                    return failure(4, "answer_key_ambiguous", "writer", activity=aid, token=str(idx)), {}

            if "answers" in item and "options" in item and not set(item["answers"]) <= set(item["options"]):
                return failure(4, "answers_not_subset", "writer", activity=aid, token=str(idx)), {}

            if typ == "select":
                opts = item.get("options") or []
                correct_count = sum(option.get("correct") is True for option in opts)
                if correct_count == 0:
                    return failure(4, "answer_key_missing", "writer", activity=aid, token=str(idx)), {}
                min_allowed = 1 if mod_level in {"a2", "b1"} else 2
                min_req = item.get("min_correct", min_allowed)
                if correct_count < max(min_allowed, min_req):
                    return failure(4, "select_correct_set_invalid", "writer", activity=aid, token=str(idx)), {}
        if mod_level == "a1" or typ == "order":
            structural_reason = _structural_activity_error(activity, typ, records)
            if structural_reason is not None:
                return failure(4, structural_reason, "writer", code=structural_reason, activity=aid), {}
    return _pass(4), form_options


def check_6_count(expanded: dict[str, Any], target: int, words: dict[str, Any] | None = None) -> dict[str, Any]:
    uk = total = 0
    records = {w["id"]: w for w in (words or {}).get("words") or []}
    for unit in expanded["units"]:
        if unit["tab"] != "urok":
            continue
        if unit["role"] == "gloss_ref":
            match = re.fullmatch(r"\{\{gloss:(W-[0-9]+)\}\}", unit["text"])
            record = records.get(match.group(1)) if match else None
            if record is None:
                return failure(6, "gloss_record_missing", "pack", token=unit["text"])
            lemma_count = len(tokenize(record["lemma"]))
            gloss_count = len(tokenize(record.get("gloss_en") or ""))
            uk += lemma_count
            total += lemma_count + gloss_count
            continue
        for token in tokenize(unit["text"]):
            total += 1
            if token.kind == "cyrillic" and unit["role"] != "vesum_exempt":
                uk += 1
    details = {
        "urok_tokens": total,
        "ukrainian_tokens": uk,
        "ukrainian_share": round(uk / total, 6) if total else 0,
        "word_target": target,
        "not_checked": ["word_target_not_calibrated", "lesson_structural_minimums_not_calibrated"],
    }
    if total < target:
        return {**failure(6, "word_target_below_minimum", "writer"), "details": details}
    return _pass(6, details)


def check_7_deterministic(
    stream: Any,
    lesson: dict[str, Any],
    draft: dict[str, Any] | None = None,
    form_options: dict[tuple[str, int], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    for forms in (form_options or {}).values():
        for form in forms:
            if form.get("stress_source") == "pending" or not form.get("stressed"):
                return failure(7, "pending_stress", "pack", token=form.get("form"))
    if stream.failures:
        first = stream.failures[0]
        layer = (
            "pack"
            if first["code"] in {codes.LEMMA_OUTSIDE_STATE, codes.UNKNOWN_WORD_ID, codes.PENDING_STRESS}
            else "writer"
        )
        return failure(
            7,
            first.get("message") or first["code"],
            layer,
            code=first["code"],
            step=first["unit"].get("step"),
            activity=first["unit"].get("activity"),
            token=first["token"],
        )
    vocab = (lesson.get("inventory") or {}).get("vocabulary") or {}
    drilled_forms = {
        (item["record"], form["tags"])
        for act in (draft or {}).get("activities") or []
        for idx, item in enumerate(act.get("items") or [])
        for form in (form_options or {}).get((act["id"], idx), [])
    }
    for group in ("core", "recycled"):
        for item in vocab.get(group) or []:
            rid = item["evidence"] if isinstance(item, dict) else item
            if not any(
                t["unit"].get("tab") in {"urok", "vpravy"} and rid in t.get("candidates", []) for t in stream.tokens
            ):
                return failure(7, f"{group}_record_absent", "writer", token=rid)
    for item in vocab.get("core") or []:
        for tag in item.get("forms") or []:
            if (item["evidence"], tag) in drilled_forms:
                continue
            if not any(
                item["evidence"] in t.get("candidates", [])
                and any(tag in r.get("forms", []) for r in t.get("readings", []))
                and (t["unit"].get("step") is not None or t["unit"].get("activity") is not None)
                for t in stream.tokens
            ):
                return failure(7, "taught_form_not_in_teaching_position", "writer", token=f"{item['evidence']}:{tag}")
    return _pass(7, {"tokens": len(stream.tokens), "open_questions": len(stream.open_tokens())})


def dispatch_questions(batch: dict[str, Any], seat: str, *, repo_root: Path) -> dict[str, Any]:
    """Dispatch a bounded language-seat question batch, await, and parse answers."""
    agent, separator, model = seat.partition(":")
    if not separator or not agent or not model:
        raise ValueError("question seat must be agent:model")
    state = repo_root / "batch_state" / "tasks"
    state.mkdir(parents=True, exist_ok=True)
    task_id = (
        f"questions-{batch['lesson']['level']}-{batch['lesson']['slug']}-{batch['lesson']['n']}-{uuid.uuid4().hex[:8]}"
    )
    prompt = state / f"{task_id}.prompt.md"
    instruction = (
        "Choose exactly one offered candidate for every question using its sentence. "
        "Return only YAML with an answers list; each entry has id and record, "
        "and stressed when a record has multiple offered readings. "
        "Use only offered record identifiers and stressed spellings.\n\n"
    )
    lock.atomic_write(prompt, instruction.encode("utf-8") + lock.yaml_bytes(batch))
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "delegate.py"),
        "dispatch",
        "--agent",
        agent,
        "--model",
        model,
        "--mode",
        "read-only",
        "--worktree",
        "--task-id",
        task_id,
        "--prompt-file",
        str(prompt),
        "--research-role",
        "writer",
        "--research-task-family",
        "constrained-resolution",
        "--research-track",
        batch["lesson"]["level"],
        "--research-owned-path",
        f"curriculum/l2-uk-en/evidence/{batch['lesson']['level']}/_state/"
        f"{batch['lesson']['slug']}/lesson-{batch['lesson']['n']}.questions.yaml",
    ]
    sent = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if sent.returncode:
        raise RuntimeError(f"question dispatch failed: {sent.stderr.strip()}")
    done = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "delegate.py"), "wait", task_id, "--timeout", "1800"],
        capture_output=True,
        text=True,
        timeout=1830,
        check=False,
    )
    if done.returncode:
        raise RuntimeError(f"question wait failed: {done.stderr.strip()}")
    result = json.loads(done.stdout)
    if result.get("status") != "done" or not result.get("result_file"):
        raise RuntimeError("question dispatch did not finish with an answer file")
    return yaml.safe_load(strip_markdown_fence(Path(result["result_file"]).read_text(encoding="utf-8")))


def _printable_form_draft(
    draft: dict[str, Any], choices: dict[tuple[str, int], list[dict[str, Any]]]
) -> dict[str, Any]:
    rendered = copy.deepcopy(draft)
    for act in rendered.get("activities") or []:
        for idx, item in enumerate(act.get("items") or []):
            forms = choices.get((act["id"], idx))
            if forms is None:
                continue
            item["options"] = [f["stressed"] for f in forms]
            answer = next(f for f in forms if f["tags"] == item["answer_tags"])
            item["answer"] = answer["stressed"]
    return rendered


def _printable_form_expanded(
    expanded: dict[str, Any], choices: dict[tuple[str, int], list[dict[str, Any]]]
) -> dict[str, Any]:
    rendered = copy.deepcopy(expanded)
    for unit in rendered["units"]:
        if unit["tab"] != "vpravy" or not isinstance(unit["item"], int):
            continue
        forms = choices.get((unit["activity"], unit["item"]))
        block = unit["block"]
        if forms is not None and isinstance(block, str) and block.startswith("opt_"):
            index = int(block[4:])
            unit["text"] = forms[index]["stressed"]
    return rendered


def run_lesson(
    level: str,
    slug: str,
    n: int,
    *,
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words: dict[str, Any],
    state_dir: Path,
    repo_root: Path,
    plans_dir: Path,
    evidence_dir: Path,
    question_seat: str | None = None,
    question_dispatch: QuestionDispatch | None = None,
    sources: Any = None,
    allowlist: Allowlist | None = None,
    site_dir: Path | None = None,
    expected_inputs: dict[str, str] | None = None,
    inventory_gate: Callable[..., Any] = check_lesson,
    observed_writer: Callable[..., Any] = write_observed,
    render_check: Callable[..., Any] = check_11_render,
) -> dict[str, Any]:
    """Stop at the first failed check; write a schema-valid gate report each run."""
    from scripts.curriculum.evidence.sources import Sources
    from scripts.curriculum.resolver.stream import load_allowlist

    state_dir.mkdir(parents=True, exist_ok=True)
    unlink_current(state_dir, n)
    rows: list[dict[str, Any]] = []
    inputs = expected_inputs or {}
    ledger_inputs = {
        "plan_sha256": inputs.get("plan_sha256") or hashlib.sha256(lock.yaml_bytes(plan)).hexdigest(),
        "pack_lock": inputs.get("pack_lock") or hashlib.sha256(lock.yaml_bytes(pack)).hexdigest(),
        "words_lock": inputs.get("words_lock") or hashlib.sha256(lock.yaml_bytes(words)).hexdigest(),
        "card_sha256": inputs.get("style_card_sha256") or "0" * 64,
        "prompt_sha256": inputs.get("prompt_sha256") or "0" * 64,
    }
    gate_path = state_dir / f"lesson-{n}.gates.yaml"
    ledger_path = state_dir / f"lesson-{n}.regeneration.yaml"

    def finish(row: dict[str, Any] | None = None) -> dict[str, Any]:
        if row is not None:
            rows[:] = [prior for prior in rows if prior["check"] != row["check"]]
            rows.append(row)
        existing = {prior["check"] for prior in rows}
        for number in range(1, 10):
            if number not in existing:
                rows.append({"check": number, "status": "not_checked", "reason": "prior_check_failed"})
        rows.sort(key=lambda prior: prior["check"])
        for number in (10, 11):
            if number not in {r["check"] for r in rows}:
                rows.append({"check": number, "status": "not_checked", "reason": "prior_check_failed"})
        rows.sort(key=lambda prior: prior["check"])
        doc = {
            "level": level,
            "slug": slug,
            "n": n,
            "passed": all(r["status"] != "failed" for r in rows),
            "checks": rows,
        }
        Draft202012Validator(
            json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
        ).validate(doc)
        lock.write(gate_path, lock.yaml_bytes(doc))
        bad = next((r for r in rows if r["status"] == "failed"), None)
        if bad is not None:
            record_failure(ledger_path, slug, n, bad, ledger_inputs)
        return {**doc, "passed_through": bad["check"] if bad else 11, "manifest_sha256": None}

    previous = load_ledger(ledger_path, slug, n, ledger_inputs)
    if previous["terminal_layer"] is not None:
        return finish(failure(1, "regeneration_terminal", previous["terminal_layer"]))
    # A fresh input series still invalidates receipts left by earlier failures.
    if load_ledger(ledger_path, slug, n)["attempts"]:
        invalidate_lesson_resolution(state_dir, n)

    lesson = _lesson(plan, n)
    activity_types = {a["id"]: a["type"] for a in lesson.get("activities") or []}
    errors = validate_draft(draft, level, activity_types=activity_types)
    if errors:
        err = errors[0]
        return finish(failure(1, f"{err.check}: {err.reason}", "writer", token=err.path))
    if draft["lesson"] != {"module": f"{level}/{slug}", "n": n}:
        return finish(failure(1, "lesson_identity_mismatch", "writer"))
    if draft["status"] == "evidence_gap" and any(
        gap["step"] not in {step["id"] for step in lesson["steps"]} for gap in draft["gaps"]
    ):
        return finish(failure(1, "gap_step_not_in_plan", "writer"))
    for key, value in inputs.items():
        if key in draft["inputs"] and draft["inputs"][key] != value:
            return finish(failure(1, f"input_hash_mismatch: {key}", "writer"))
    rows.append(_pass(1))
    if draft["status"] == "evidence_gap":
        gap = draft["gaps"][0]
        return finish(
            failure(
                2,
                "evidence_gap: " + json.dumps(draft["gaps"], ensure_ascii=False),
                _gap_layer(draft["gaps"], lesson),
                step=gap.get("step"),
            )
        )
    rows.append(_pass(2))
    row = check_3_structure(draft, lesson)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    row, form_options = check_4_activities(draft, lesson, words, pack, level=level)
    if row["status"] == "failed":
        return finish(row)
    if level == "a1":
        row["details"] = {"draft_report": draft_report(plan, [draft])}
    rows.append(row)
    assembled = check_5_assembly(draft, plan, pack, words, level, slug, n, output_dir=state_dir)
    if not assembled.passed:
        return finish(
            failure(
                5,
                assembled.reason or "assembly_failed",
                assembled.layer or "engine",
                step=assembled.step,
                activity=assembled.activity,
                token=assembled.token,
            )
        )
    expanded = assembled.artifacts["expanded_doc"]
    rows.append(_pass(5))
    row = check_6_count(expanded, lesson["word_target"], words)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    owns_sources = sources is None
    with ExitStack() as source_session:
        try:
            expanded_obj = ExpandedDocument.from_data(expanded)
            selected_allowlist = allowlist or load_allowlist(
                level, slug, n, plans_dir=plans_dir, evidence_dir=evidence_dir
            )
            if sources is None:
                sources = source_session.enter_context(Sources())
            stream = resolve(expanded_obj, selected_allowlist, sources)
        except ResolverError as err:
            layer = "pack" if err.code in {codes.UNKNOWN_WORD_ID, codes.LOCK_MISMATCH} else "engine"
            return finish(failure(7, err.message, layer, code=err.code))
        except (OSError, ValueError) as err:
            return finish(failure(7, f"resolver_input_unavailable: {err}", "pack"))
        except Exception as err:
            return finish(failure(7, f"resolver_error: {err}", "engine"))
        row = check_7_deterministic(stream, lesson, draft, form_options)
        if row["status"] == "failed":
            return finish(row)
        rows.append(row)
        # Questions omit step, while receipts retain it for digest provenance.
        token_steps = [token["unit"].pop("step", None) for token in stream.tokens]
        batch = questions.build_questions(stream, expanded_obj, selected_allowlist)
        try:
            questions.write_questions(state_dir / f"lesson-{n}.questions.yaml", batch)
        except (ResolverError, OSError) as err:
            return finish(failure(8, f"question_batch_invalid: {err}", "engine", code=getattr(err, "code", None)))
        if batch["questions"] and not question_seat:
            return finish(failure(8, "question_seat_required", "driver"))
        if batch["questions"] and (question_seat.count(":") != 1 or not all(question_seat.split(":"))):
            return finish(failure(8, "question_seat_invalid", "driver"))
        try:
            if batch["questions"]:
                # Resolution rows already have their identities in the stream.
                # Release our pinned snapshot during the slow provider call;
                # the receipt gate opens a fresh snapshot lazily through _db().
                # Injected sessions belong to their caller and stay untouched.
                if owns_sources:
                    sources.close()
                answer_doc = (question_dispatch or (lambda b, s: dispatch_questions(b, s, repo_root=repo_root)))(
                    batch, question_seat
                )
                selections = receipts.apply_answers(batch, answer_doc, question_seat.replace(":", "@"))
                if len(selections) != len(batch["questions"]):
                    raise ResolverError(
                        codes.TOKEN_UNRESOLVED, "every question must be answered before inventory and rendering"
                    )
            else:
                selections = {}
            receipt_doc = receipts.build_receipts(
                stream, batch, selections, question_seat.replace(":", "@") if question_seat else None
            )
            for receipt, step in zip(receipt_doc["tokens"], token_steps, strict=True):
                if step is not None:
                    receipt["unit"]["step"] = step
            receipt_path = state_dir / f"lesson-{n}.resolutions.yaml"
            receipt_sha = receipts.write_receipts(receipt_path, receipt_doc)
            for token, receipt in zip(stream.tokens, receipt_doc["tokens"], strict=True):
                token["selected"] = receipt["selected"]
                token["provenance"] = receipt["provenance"]
            for token, step in zip(stream.tokens, token_steps, strict=True):
                if step is not None:
                    token["unit"] = {**token["unit"], "step": step}
            stream.inputs["receipts_sha256"] = receipt_sha
        except (ResolverError, ValueError, RuntimeError, OSError) as err:
            return finish(
                failure(
                    8,
                    str(err),
                    "writer" if isinstance(err, ResolverError) else "driver",
                    code=getattr(err, "code", None),
                )
            )
        rows.append(_pass(8, {"questions": len(batch["questions"]), "answered": len(selections)}))
        if level == "a1":
            try:
                choice_row = check_7_a1_choices(
                    draft,
                    lesson,
                    words,
                    stream,
                    state_dir=state_dir,
                    lesson_n=n,
                    sources=sources,
                    pack=pack,
                    allowlist=selected_allowlist,
                    requirement_inputs=receipts.requirement_inputs(
                        receipt_doc["inputs"],
                        yaml.safe_load((state_dir / f"lesson-{n}.draft.yaml").read_text(encoding="utf-8")),
                    ),
                )
            except OSError as err:
                return finish(
                    failure(7, f"a1_choice_source_unavailable: {err}", "pack", code="a1_choice_source_unavailable")
                )
            except (ResolverError, ValueError) as err:
                return finish(
                    failure(
                        7,
                        f"a1_choice_check_invalid: {err}",
                        "engine",
                        code=getattr(err, "code", None) or "a1_choice_check_invalid",
                    )
                )
            if choice_row["status"] == "failed":
                return finish(choice_row)
            row["details"].update(choice_row.get("details", {}))
    try:
        gate = inventory_gate(
            level,
            slug,
            n,
            stream,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            expanded=expanded_obj,
            resolutions_path=receipt_path,
        )
    except Exception as err:
        return finish(failure(7, f"inventory_gate_error: {err}", "engine"))
    if not gate.ok:
        first = gate.failures[0]
        return finish(failure(7, first.message, _inventory_layer(first.code), code=first.code, token=first.token))
    try:
        observed_writer(
            level,
            slug,
            n,
            resolutions_doc=receipt_doc,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            expanded=expanded_obj,
            state_dir=state_dir,
        )
    except ObservedError as err:
        return finish(failure(7, err.message, _inventory_layer(err.code), code=err.code))
    except Exception as err:
        return finish(failure(7, f"observed_index_error: {err}", "engine"))
    print_draft = _printable_form_draft(draft, form_options)
    print_expanded = _printable_form_expanded(expanded, form_options)
    try:
        rendered = check_9_stress_and_render(
            print_expanded,
            print_draft,
            plan,
            pack,
            words,
            stream,
            level,
            slug,
            n,
            provenance_doc=assembled.artifacts.get("provenance"),
            repo_root=repo_root,
            output_dir=state_dir,
            site_dir=site_dir,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
        )
    except Exception as err:
        return finish(failure(9, f"stress_or_render_error: {err}", "engine"))
    if not rendered.passed:
        layer = rendered.layer or "engine"
        return finish(
            failure(
                9,
                rendered.reason or "stress_or_render_failed",
                layer,
                step=rendered.step,
                activity=rendered.activity,
                token=rendered.token,
            )
        )
    if rendered.artifacts.get("provenance"):
        assembled.artifacts["provenance"] = rendered.artifacts["provenance"]
    rows.append(_pass(9))
    rows.append({"check": 10, "status": "not_checked", "reason": "grammar_checker_undecided"})
    (repo_root / "batch_state" / "verify_shippable").mkdir(parents=True, exist_ok=True)
    try:
        rendered_check = render_check(
            level, slug, astro_build=True, module_dir=site_dir, plan_path=plans_dir / f"{slug}.yaml", through_lesson=n
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return finish(failure(11, f"verify_shippable_environment_error: {err}", "harness"))
    except Exception as err:
        return finish(failure(11, f"verify_shippable_error: {err}", "engine"))
    if not rendered_check.passed:
        row = failure(
            11,
            rendered_check.reason or "verify_shippable_failed",
            "harness" if rendered_check.layer == "harness" else "engine",
        )
        row["details"] = {"verify_shippable": rendered_check.artifacts.get("verify_shippable", {})}
        return finish(row)
    rows.append(_pass(11, {"verify_shippable": rendered_check.artifacts.get("verify_shippable", {})}))
    gate = finish()
    try:
        manifest, digest = write_manifest(
            level,
            slug,
            n,
            lesson_kind="recap" if lesson.get("kind") == "recap" else "lesson",
            state_dir=state_dir,
            repo_root=repo_root,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            position=plan.get("arc_ref", {}).get("position", 1),
            site_dir=site_dir,
        )
    except Exception as err:
        reason = f"digest_error:{err.code}: {err.message}" if isinstance(err, DigestError) else str(err)
        path = getattr(err, "path", None) or (err.filename if isinstance(err, OSError) and err.filename else reason)
        write_manifest_error(state_dir, n, reason, str(path), datetime.now(UTC).isoformat().replace("+00:00", "Z"))
        bad = failure(12, reason, "engine")
        record_failure(ledger_path, slug, n, bad, ledger_inputs)
        return {
            **gate,
            "passed": False,
            "passed_through": 12,
            "stopping_check": 12,
            "reason": reason,
            "manifest_sha256": None,
        }
    draft_path = state_dir / f"lesson-{n}.draft.yaml"
    success_inputs = {**ledger_inputs, "draft_sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest()}
    record_success(ledger_path, slug, n, success_inputs)
    return {**gate, "passed_through": 12, "manifest_sha256": digest, "manifest": manifest}
