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

import copy
import hashlib
import json
import re
import unicodedata
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


# A requirement is a language judgement, not a form inferred by the resolver. Keep it
# beside the resolution receipts with the same YAML + lock publication rule. Missing
# receipts are an explicit completeness status; a present but broken receipt is invalid.
_A1_REQUIREMENT_GROUPS = frozenset({"Gender", "Number", "Case", "Person", "VerbForm"})
_REQUIREMENT_FIELDS = frozenset(
    {
        "activity",
        "item",
        "requires",
        "writer",
        "reviewer",
        "payload_sha256",
        "decision",
        "reason",
        "options",
        "requires_forced",
    }
)
_EVIDENCE_RE = re.compile(r"^(?:vesum|pravopys|textbook|grinchenko|sum20|vts|ulif):[^\s:]+$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def requirement_sentence(item: dict[str, Any]) -> str:
    """The sentence rendered for an activity item, in assembler precedence."""
    for field in ("prompt", "sentence", "question", "cue", "statement"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def requirement_payload_sha256(sentence: str, options: list[str], key_index: int, requires: dict[str, str]) -> str:
    payload = {
        "sentence": canonical_text(sentence),
        "options": [canonical_text(o) for o in options],
        "key_index": key_index,
        "requires": requires,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def requirement_inputs(resolution_inputs: dict[str, str], authored_draft: dict[str, Any]) -> dict[str, str]:
    """Bind the whole draft, ignoring only formatting in form sentences and options."""
    stable = copy.deepcopy(authored_draft)
    for activity in stable.get("activities") or []:
        for item in activity.get("items") or []:
            if item.get("kind") != "form":
                continue
            item.pop("_resolved_key_index", None)
            for field in ("prompt", "sentence", "question", "cue", "statement"):
                if isinstance(item.get(field), str):
                    item[field] = canonical_text(item[field])
            for option in item.get("options") or []:
                if isinstance(option, dict) and isinstance(option.get("text"), str):
                    option["text"] = canonical_text(option["text"])
            if isinstance(item.get("options"), list):
                item["options"] = [canonical_text(o) if isinstance(o, str) else o for o in item["options"]]
    encoded = json.dumps(stable, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    inputs = {key: value for key, value in resolution_inputs.items() if key != "expanded_sha256"}
    inputs["draft_semantic_sha256"] = hashlib.sha256(encoded).hexdigest()
    return inputs


def requirement_receipt_path(state_dir: Path, lesson_n: int) -> Path:
    """Return the sidecar path for one lesson's requirement judgements."""
    return Path(state_dir) / f"lesson-{lesson_n}.requirements.yaml"


def _requirement_error(message: str) -> ResolverError:
    return ResolverError(codes.RECEIPT_INVALID, f"requirement receipt: {message}")


# Lanes that may judge Ukrainian (the LANGUAGE-LANES rule in model-assignment.md): only
# claude, codex and agy; Grok and every other family are excluded. Every confirmation path
# (requirement receipts and group-sort question answers) reads this.
LANGUAGE_LANES = frozenset({"agy", "claude", "codex"})


def language_seat_family(seat: str, *, what: str) -> str:
    """Return the family of a language-lane seat whose lane and model both resolve to it."""
    from scripts.review.second_seat import IdentityError, concrete_family

    _check_seat(seat)
    lane, separator, model = seat.partition("@")
    if not separator or not model:
        raise _requirement_error(f"{what} seat must name a lane and model")
    if lane.casefold() not in LANGUAGE_LANES:
        raise _requirement_error(f"{what} seat is not a language lane")
    try:
        lane_family = concrete_family(lane, what=f"{what} lane")
        model_family = concrete_family(model, what=f"{what} model")
    except IdentityError as exc:
        raise _requirement_error(f"{what} seat has unresolved family: {exc}") from exc
    if lane_family != model_family:
        raise _requirement_error(f"{what} seat and model family disagree")
    return lane_family


def _seat_family(seat: str, *, what: str) -> str:
    """Resolve both parts of a writer seat and refuse contradictory identities."""
    from scripts.review.reviewer_resolver import UNRESOLVED_AUTHOR_FAMILIES, resolve_author_family
    from scripts.review.second_seat import IdentityError, concrete_family

    _check_seat(seat)
    lane, separator, model = seat.partition("@")
    if not separator or not model:
        raise _requirement_error(f"{what} seat must name a lane and model")
    try:
        lane_family = concrete_family(lane, what=f"{what} lane")
        model_family = resolve_author_family(model)
    except IdentityError as exc:
        raise _requirement_error(f"{what} seat has unresolved family: {exc}") from exc
    if model_family not in UNRESOLVED_AUTHOR_FAMILIES and lane_family != model_family:
        raise _requirement_error(f"{what} seat and model family disagree")
    return lane_family


def validate_requirement_receipts(doc: Any) -> None:
    """Validate item identity, complete-demand snapshot and independent provenance."""
    if not isinstance(doc, dict) or set(doc) != {"requirements_schema", "lesson", "inputs", "items"}:
        raise _requirement_error("expected requirements_schema, lesson, inputs and items")
    if type(doc["requirements_schema"]) is not int or doc["requirements_schema"] != 2:
        raise _requirement_error("requirements_schema must be 2")
    lesson = doc["lesson"]
    if (
        not isinstance(lesson, dict)
        or set(lesson) != {"level", "slug", "n"}
        or not all(isinstance(lesson[k], str) and lesson[k] for k in ("level", "slug"))
        or type(lesson["n"]) is not int
        or lesson["n"] < 1
    ):
        raise _requirement_error("lesson identity is malformed")
    inputs = doc["inputs"]
    if (
        not isinstance(inputs, dict)
        or not inputs
        or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in inputs.items())
    ):
        raise _requirement_error("inputs must contain the draft input hashes")
    if not isinstance(doc["items"], list):
        raise _requirement_error("items must be a list")
    seen: set[tuple[str, int]] = set()
    for index, row in enumerate(doc["items"]):
        if not isinstance(row, dict) or set(row) != _REQUIREMENT_FIELDS:
            raise _requirement_error(f"item {index} has malformed fields")
        activity, item = row["activity"], row["item"]
        if not isinstance(activity, str) or not activity or type(item) is not int or item < 0:
            raise _requirement_error(f"item {index} has malformed activity or item locator")
        locator = (activity, item)
        if locator in seen:
            raise _requirement_error(f"duplicate item locator {locator!r}")
        seen.add(locator)
        demand = row["requires"]
        if (
            not isinstance(demand, dict)
            or not demand
            or set(demand) - _A1_REQUIREMENT_GROUPS
            or not all(isinstance(value, str) and value for value in demand.values())
        ):
            raise _requirement_error(f"item {index} has malformed A1 requires")
        if not isinstance(row["payload_sha256"], str) or not _SHA_RE.fullmatch(row["payload_sha256"]):
            raise _requirement_error(f"item {index} has malformed payload_sha256")
        if (
            row["decision"] not in {"confirm", "deny"}
            or not isinstance(row["reason"], str)
            or not row["reason"].strip()
        ):
            raise _requirement_error(f"item {index} needs a decision and non-empty reason")
        if type(row["requires_forced"]) is not bool or not isinstance(row["options"], list) or not row["options"]:
            raise _requirement_error(f"item {index} has malformed option judgements")
        no_evidence = False
        for option in row["options"]:
            if not isinstance(option, dict) or set(option) != {"text", "judgement", "evidence"}:
                raise _requirement_error(f"item {index} has malformed option judgement")
            if (
                not isinstance(option["text"], str)
                or not option["text"].strip()
                or option["judgement"] not in {"valid", "invalid", "depends_on_context"}
            ):
                raise _requirement_error(f"item {index} has malformed option text or judgement")
            evidence = option["evidence"]
            if not isinstance(evidence, list) or any(
                not isinstance(eid, str) or not _EVIDENCE_RE.fullmatch(eid) for eid in evidence
            ):
                raise _requirement_error(f"item {index} has invalid evidence id")
            no_evidence |= not evidence
        if no_evidence and (row["decision"] != "deny" or not row["reason"].startswith("unresolved")):
            raise _requirement_error(f"item {index} has unsupported judgement")
        confirmable = (
            row["requires_forced"]
            and not no_evidence
            and [option["judgement"] for option in row["options"]].count("valid") == 1
            and all(option["judgement"] in {"valid", "invalid"} for option in row["options"])
        )
        if row["decision"] == "confirm" and not confirmable:
            raise _requirement_error(f"item {index} cannot be confirmed")
        writer, reviewer = row["writer"], row["reviewer"]
        if not isinstance(writer, dict) or set(writer) != {"seat", "family"}:
            raise _requirement_error(f"item {index} has malformed writer provenance")
        if not isinstance(reviewer, dict) or set(reviewer) != {"seat", "family", "lane"}:
            raise _requirement_error(f"item {index} has malformed reviewer provenance")
        for provenance, seat_family in ((writer, _seat_family), (reviewer, language_seat_family)):
            _check_seat(provenance["seat"])
            _check_seat(provenance["family"])
            if provenance["family"].casefold() != seat_family(provenance["seat"], what=f"item {index}"):
                raise _requirement_error(f"item {index} seat and family disagree")
        if reviewer["lane"] != "language":
            raise _requirement_error(f"item {index} was not confirmed by a language lane")
        if writer["family"].casefold() == reviewer["family"].casefold():
            raise _requirement_error(f"item {index} writer and reviewer share a model family")


def write_requirement_receipts(path: Path, doc: dict[str, Any]) -> str:
    """Publish validated requirement judgements atomically with a lock sidecar."""
    validate_requirement_receipts(doc)
    return lock.write(Path(path), lock.yaml_bytes(doc))


def read_requirement_receipts(path: Path) -> dict[str, Any] | None:
    """Return None for absent input; fail closed on a present unlocked or invalid file."""
    path = Path(path)
    if not path.exists() and not path.with_name(path.name + ".lock").exists():
        return None
    if not lock.check(path):
        raise ResolverError(codes.LOCK_MISMATCH, f"requirements {str(path)!r} disagree with their lock")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise _requirement_error(f"cannot parse YAML: {exc}") from exc
    validate_requirement_receipts(doc)
    return doc


def requirement_status(
    doc: dict[str, Any] | None,
    *,
    lesson: dict[str, Any],
    state_dir: Path,
    inputs: dict[str, Any],
    activity: str,
    item: int,
    payload_sha256: str,
    options: list[str],
    key_index: int,
    requires: dict[str, str],
) -> str:
    """Return the named gate code or confirmed, with missing before writer-unresolved before stale before denied."""
    if doc is None:
        return "requires_receipt_missing"
    validate_requirement_receipts(doc)
    from scripts.review.second_seat import IdentityError, writer_family

    try:
        actual_writer_family = writer_family(state_dir, lesson["n"])
    except IdentityError:
        return "requires_writer_unresolved"
    for row in doc["items"]:
        if row["activity"] == activity and row["item"] == item:
            if (
                doc["lesson"] != lesson
                or doc["inputs"] != inputs
                or row["writer"]["family"] != actual_writer_family
                or row["reviewer"]["family"] == actual_writer_family
                or row["payload_sha256"] != payload_sha256
                or row["requires"] != requires
            ):
                return "requires_receipt_stale"
            if len(row["options"]) != len(options) or [canonical_text(option["text"]) for option in row["options"]] != [
                canonical_text(option) for option in options
            ]:
                return "requires_receipt_stale"
            if row["options"][key_index]["judgement"] != "valid":
                return "requires_receipt_denied"
            return "confirmed" if row["decision"] == "confirm" else "requires_receipt_denied"
    return "requires_receipt_missing"
