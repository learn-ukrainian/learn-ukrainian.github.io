"""Resolution receipts: `lesson-<n>.resolutions.yaml`, deterministic YAML with a lock sidecar.

Every token of the stream gets a receipt: its occurrence (the review
contract's `tab`, `activity`, `item` plus `block`, and the offset), its
candidate records, the selected record and forms, and how it was selected.
A selection comes only from deterministic narrowing to one record, or from a
recorded answer to a constrained question. `apply_answers` rejects any answer
that names a record outside its question's candidates, so the answering seat
cannot introduce a record. The observed-state index (#8414) and the digest
(#8430) read record ids from here, never from a re-analysis.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock

from . import codes
from .inputs import ResolverError
from .stream import ResolutionStream

REPO_ROOT = Path(__file__).resolve().parents[3]
RECEIPTS_SCHEMA = REPO_ROOT / "schemas/resolution-receipts-v1.schema.json"
# A seat identity is one provenance field: no colon, no whitespace.
SEAT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@+-]*$")
PROVENANCE_RE = re.compile(r"^(?:proposal:[A-Za-z0-9._/@+-]+\+)?question:([A-Za-z0-9._/@+-]+):(Q-[0-9]{3,})$")


def _check_seat(seat: str) -> str:
    if not isinstance(seat, str) or not SEAT_RE.fullmatch(seat):
        raise ResolverError(codes.INVALID_INPUT, f"seat identity {seat!r} must match {SEAT_RE.pattern}")
    return seat


def apply_answers(questions: dict[str, Any], answers: Any, seat: str) -> dict[str, dict[str, Any]]:
    """Validate a seat's answers against the batch; return question id -> selection."""
    _check_seat(seat)
    if not isinstance(answers, dict) or not isinstance(answers.get("answers"), list):
        raise ResolverError(codes.INVALID_INPUT, "the answers file must be a mapping with an 'answers' list")
    by_id = {question["id"]: question for question in questions["questions"]}
    selections: dict[str, dict[str, Any]] = {}
    for answer in answers["answers"]:
        if not isinstance(answer, dict) or set(answer) - {"id", "record", "stressed"} or "id" not in answer:
            raise ResolverError(codes.INVALID_INPUT, f"malformed answer {answer!r}")
        question = by_id.get(answer["id"])
        if question is None:
            raise ResolverError(codes.INVALID_ANSWER, f"answer to unknown question {answer['id']!r}")
        if answer["id"] in selections:
            raise ResolverError(codes.INVALID_ANSWER, f"question {answer['id']} is answered twice")
        matching = [c for c in question["candidates"] if c["record"] == answer.get("record")]
        if "stressed" in answer:
            matching = [c for c in matching if c["stressed"] == answer["stressed"]]
        if len(matching) != 1:
            offered = [(c["record"], c["stressed"]) for c in question["candidates"]]
            raise ResolverError(
                codes.INVALID_ANSWER,
                f"{answer['id']} ({question['token']!r} in {question['sentence']!r}): answer "
                f"{answer.get('record')!r} is not exactly one of the candidates {offered}"
                + ("; name 'stressed' too, the record has several readings" if len(matching) > 1 else ""),
            )
        chosen = matching[0]
        if chosen["stressed"] is None:
            raise ResolverError(
                codes.PENDING_STRESS,
                f"{answer['id']} ({question['token']!r}): the selected reading of {chosen['record']} has pending stress",
            )
        selections[answer["id"]] = {
            "record": chosen["record"],
            "forms": list(chosen["forms"]),
            "stressed": chosen["stressed"],
        }
    unanswered = [q["id"] for q in questions["questions"] if q["blocking"] and q["id"] not in selections]
    if unanswered:
        raise ResolverError(codes.TOKEN_UNRESOLVED, f"blocking questions without an answer: {unanswered}")
    return selections


def build_receipts(
    stream: ResolutionStream,
    questions: dict[str, Any],
    selections: dict[str, dict[str, Any]],
    seat: str | None,
) -> dict[str, Any]:
    if stream.failures:
        first = stream.failures[0]
        raise ResolverError(
            first["code"],
            f"{len(stream.failures)} token failure(s) must be fixed before receipts; first: {first['token']!r} "
            f"in {first['text']!r}: {first['message']}",
        )
    if questions["inputs"] != stream.inputs or questions["lesson"] != stream.lesson:
        raise ResolverError(codes.STALE_QUESTIONS, "the questions batch was built from other inputs")
    by_place = {(json.dumps(q["unit"], sort_keys=True), q["offset"]): q for q in questions["questions"]}
    tokens = []
    for token in stream.tokens:
        receipt = {
            "unit": token["unit"],
            "offset": token["offset"],
            "token": token["token"],
            "surface": token["surface"],
            "class": token["class"],
            "candidates": token["candidates"],
            "selected": token["selected"],
            "provenance": token["provenance"],
        }
        if token["class"] in codes.OPEN_CLASSES:
            question = by_place.get((json.dumps(token["unit"], sort_keys=True), token["offset"]))
            if question is None:
                raise ResolverError(codes.STALE_QUESTIONS, f"no question for open token {token['token']!r}")
            selection = selections.get(question["id"])
            if selection is not None:
                receipt["selected"] = selection
                # No tagger fills `proposal` yet, so the `proposal:<tagger>+` prefix is never written.
                receipt["provenance"] = f"question:{_check_seat(seat or '')}:{question['id']}"
        tokens.append(receipt)
    doc = {"resolutions_schema": 1, "lesson": dict(stream.lesson), "inputs": dict(stream.inputs), "tokens": tokens}
    validate_receipts(doc)
    return doc


def validate_receipts(doc: Any) -> None:
    schema = json.loads(RECEIPTS_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        raise ResolverError(codes.RECEIPT_INVALID, f"at {list(first.absolute_path)}: {first.message}")
    for index, token in enumerate(doc["tokens"]):
        where = f"token {index} ({token['token']!r})"
        klass, selected, provenance = token["class"], token["selected"], token["provenance"]
        if klass in codes.FAILURE_CLASSES:
            raise ResolverError(codes.RECEIPT_INVALID, f"{where} carries failure class {klass}")
        if selected is not None and selected["record"] not in token["candidates"]:
            raise ResolverError(codes.RECEIPT_INVALID, f"{where} selects a record outside its candidates")
        if klass in codes.OPEN_CLASSES:
            if selected is None:
                if provenance is not None:
                    raise ResolverError(codes.RECEIPT_INVALID, f"{where} has provenance but no selection")
                if klass == codes.STRESS_OPEN:
                    raise ResolverError(codes.TOKEN_UNRESOLVED, f"{where} is stress_open without an answer")
            elif provenance is None or not PROVENANCE_RE.fullmatch(provenance):
                raise ResolverError(codes.RECEIPT_INVALID, f"{where} is selected without a question provenance")
        elif provenance != "deterministic":
            raise ResolverError(codes.RECEIPT_INVALID, f"{where} is {klass} but not deterministic")
        elif (selected is not None) != (klass == codes.RESOLVED):
            raise ResolverError(codes.RECEIPT_INVALID, f"{where}: only a resolved token carries a selection")


def write_receipts(path: Path, doc: dict[str, Any]) -> str:
    validate_receipts(doc)
    return lock.write(Path(path), lock.yaml_bytes(doc))


def check_receipts(path: Path) -> dict[str, Any]:
    """Fail closed on an absent or mismatching lock, then on schema and rules."""
    path = Path(path)
    if not lock.check(path):
        raise ResolverError(codes.LOCK_MISMATCH, f"resolutions {str(path)!r} are absent or disagree with their lock")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_receipts(doc)
    return doc
