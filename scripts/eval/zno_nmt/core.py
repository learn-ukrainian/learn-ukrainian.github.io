"""Strict, provider-independent data and scoring primitives for ZNO/NMT.

The evaluator deliberately has no I/O beyond the small JSON helpers in this
module. In particular, the question packet and its grading key are separate
objects: packet validation can therefore be performed in a process that never
has access to the answers.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from contextlib import suppress
from pathlib import Path
from typing import Any

EXAM_SCHEMA = "zno-nmt.exam.v1"
PACKET_SCHEMA = "zno-nmt.questions.v1"
KEY_SCHEMA = "zno-nmt.key.v1"
RUN_SCHEMA = "zno-nmt.run.v1"
COMPARISON_SCHEMA = "zno-nmt.comparison.v1"

_EXAM_FIELDS = {"schema", "title", "subject", "year", "provenance", "scoring", "items"}
_PROVENANCE_FIELDS = {"source_url", "source_revision", "license", "exposure"}
_SCORING_FIELDS = {"kind", "policy_url", "pass_threshold", "expected_items", "expected_points"}
_ITEM_FIELDS = {"id", "kind", "question", "options", "rows", "correct"}
_CHOICE_FIELDS = {"id", "text"}
_PACKET_FIELDS = {"schema", "items", "packet_sha256"}
_PACKET_ITEM_FIELDS = {"id", "kind", "question", "options", "rows"}
_KEY_FIELDS = {
    "schema",
    "packet_sha256",
    "title",
    "subject",
    "year",
    "provenance",
    "scoring",
    "answers",
    "key_sha256",
}
_RUN_FIELDS = {
    "schema",
    "packet_sha256",
    "condition",
    "status",
    "responses",
    "identity",
    "comparison",
    "metrics",
}
_RUN_OPTIONAL_FIELDS = {"failure_reason", "repeat"}
_CONDITIONS = {"closed-book", "sources"}
_STATUSES = {"ok", "failed"}


class ExamError(ValueError):
    """Raised when an exam artifact violates its versioned data contract."""


def _json_safe(value: Any, *, where: str = "value") -> None:
    """Reject values that cannot be represented as strict JSON.

    json.dumps silently accepts NaN by default and coerces non-string object
    keys. Neither behaviour is suitable for an artifact identity. This
    recursive check keeps canonical deterministic across Python versions and
    catches the same mistakes before hashing.
    """

    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ExamError(f"{where} contains a non-finite number")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _json_safe(item, where=f"{where}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ExamError(f"{where} has a non-string object key")
            _json_safe(item, where=f"{where}.{key}")
        return
    raise ExamError(f"{where} contains a non-JSON value")


def canonical(value: Any) -> str:
    """Return compact, Unicode-preserving, recursively sorted JSON text."""

    _json_safe(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise ExamError(f"value is not canonicalizable: {exc}") from exc


def digest(value: Any) -> str:
    """Return the SHA-256 digest of canonical UTF-8 bytes."""

    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _duplicate_rejecting_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExamError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ExamError(f"non-finite JSON number: {value}")


def read_json(path: str | os.PathLike[str]) -> Any:
    """Read UTF-8 JSON while rejecting duplicate keys and NaN/Infinity."""

    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
        return json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_pairs,
            parse_constant=_reject_json_constant,
        )
    except ExamError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExamError(f"cannot read strict JSON from {file_path}: {exc}") from exc


def write_private_json(path: str | os.PathLike[str], value: Any) -> None:
    """Create a private JSON file exactly once, with mode 0600.

    O_EXCL makes publication non-overwriting and prevents an existing symlink
    from being followed. A failed write removes only the newly created target,
    leaving an existing artifact untouched. This is an intentionally small,
    portable atomic-ish primitive for local receipts; callers must not use it
    as a replacement/update operation.
    """

    file_path = Path(path)
    payload = canonical(value).encode("utf-8")
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            os.fspath(file_path),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except FileExistsError:
        raise
    except OSError as exc:
        raise ExamError(f"cannot create private JSON at {file_path}: {exc}") from exc

    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        with suppress(OSError):
            file_path.unlink()
        raise


def _require_exact_dict(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExamError(f"{where} must be an object")
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected, key=repr)
        detail: list[str] = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"unknown {extra}")
        raise ExamError(f"{where} has invalid fields ({'; '.join(detail)})")
    return value


def _require_string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        qualifier = "non-empty " if nonempty else ""
        raise ExamError(f"{where} must be a {qualifier}string")
    return value


def _require_question(value: Any, where: str) -> str:
    question = _require_string(value, where)
    if not question.strip():
        raise ExamError(f"{where} must contain non-whitespace text")
    return question


def _require_integer(value: Any, where: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExamError(f"{where} must be an integer")
    if positive and value <= 0:
        raise ExamError(f"{where} must be greater than zero")
    return value


def _require_number(value: Any, where: str, *, nonnegative: bool = False) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExamError(f"{where} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError as exc:
        raise ExamError(f"{where} must be a finite number") from exc
    if not finite:
        raise ExamError(f"{where} must be a finite number")
    if nonnegative and value < 0:
        raise ExamError(f"{where} must be non-negative")
    return value


def _require_digest(value: Any, where: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ExamError(f"{where} must be a lowercase SHA-256 hex digest")
    return value


def _validate_provenance(value: Any, where: str = "provenance") -> dict[str, str]:
    provenance = _require_exact_dict(value, _PROVENANCE_FIELDS, where)
    return {
        key: _require_string(provenance[key], f"{where}.{key}")
        for key in ("source_url", "source_revision", "license", "exposure")
    }


def _validate_scoring(
    value: Any,
    where: str = "scoring",
    *,
    expected_items: int | None = None,
    expected_points: int | None = None,
) -> dict[str, Any]:
    scoring = _require_exact_dict(value, _SCORING_FIELDS, where)
    kind = _require_string(scoring["kind"], f"{where}.kind")
    if kind not in {"benchmark", "official"}:
        raise ExamError(f"unsupported scoring kind: {kind!r}")

    policy_url = scoring["policy_url"]
    if policy_url is not None:
        _require_string(policy_url, f"{where}.policy_url")
    threshold = scoring["pass_threshold"]
    if threshold is not None:
        _require_number(threshold, f"{where}.pass_threshold", nonnegative=True)
    items_count = _require_integer(scoring["expected_items"], f"{where}.expected_items", positive=True)
    points_count = _require_integer(scoring["expected_points"], f"{where}.expected_points", positive=True)
    if threshold is not None and threshold > points_count:
        raise ExamError(f"{where}.pass_threshold cannot exceed expected_points")
    if expected_items is not None and items_count != expected_items:
        raise ExamError(f"{where}.expected_items does not match the item denominator")
    if expected_points is not None and points_count != expected_points:
        raise ExamError(f"{where}.expected_points does not match the point denominator")
    return {
        "kind": kind,
        "policy_url": policy_url,
        "pass_threshold": threshold,
        "expected_items": items_count,
        "expected_points": points_count,
    }


def _validate_choices(value: Any, where: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ExamError(f"{where} must be a non-empty list")
    choices: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, choice in enumerate(value):
        choice_dict = _require_exact_dict(choice, _CHOICE_FIELDS, f"{where}[{index}]")
        choice_id = _require_string(choice_dict["id"], f"{where}[{index}].id")
        if choice_id in seen:
            raise ExamError(f"duplicate choice id {choice_id!r} in {where}")
        seen.add(choice_id)
        choices.append(
            {
                "id": choice_id,
                "text": _require_string(choice_dict["text"], f"{where}[{index}].text", nonempty=False),
            }
        )
    return choices


def _validate_rows(value: Any, where: str, *, required: bool) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ExamError(f"{where} must be a list")
    if required and not value:
        raise ExamError(f"{where} must be a non-empty list")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(value):
        row_dict = _require_exact_dict(row, _CHOICE_FIELDS, f"{where}[{index}]")
        row_id = _require_string(row_dict["id"], f"{where}[{index}].id")
        if row_id in seen:
            raise ExamError(f"duplicate row id {row_id!r} in {where}")
        seen.add(row_id)
        rows.append(
            {
                "id": row_id,
                "text": _require_string(row_dict["text"], f"{where}[{index}].text", nonempty=False),
            }
        )
    return rows


def _validate_item(value: Any, where: str = "item") -> dict[str, Any]:
    item = _require_exact_dict(value, _ITEM_FIELDS, where)
    item_id = _require_string(item["id"], f"{where}.id")
    kind = _require_string(item["kind"], f"{where}.kind")
    if kind not in {"single", "matching"}:
        raise ExamError(f"unsupported item kind: {kind!r}")
    question = _require_question(item["question"], f"{where}.question")
    options = _validate_choices(item["options"], f"{where}.options")
    rows = _validate_rows(item["rows"], f"{where}.rows", required=kind == "matching")
    option_ids = {choice["id"] for choice in options}
    row_ids = {row["id"] for row in rows}
    if option_ids & row_ids:
        raise ExamError(f"{where}.options and rows must use disjoint ids")
    correct = item["correct"]
    if kind == "single":
        if rows:
            raise ExamError(f"{where}.rows must be empty for a single item")
        correct_id = _require_string(correct, f"{where}.correct")
        if correct_id not in option_ids:
            raise ExamError(f"{where}.correct references an unknown option")
        normalized_correct: str | dict[str, str] = correct_id
    else:
        if not isinstance(correct, dict):
            raise ExamError(f"{where}.correct must be an object for matching")
        if set(correct) != row_ids:
            raise ExamError(f"{where}.correct must contain exactly one answer for every row")
        normalized_correct = {}
        selected: list[str] = []
        for row in rows:
            row_id = row["id"]
            option_id = _require_string(correct[row_id], f"{where}.correct.{row_id}")
            if option_id not in option_ids:
                raise ExamError(f"{where}.correct.{row_id} references an unknown option")
            normalized_correct[row_id] = option_id
            selected.append(option_id)
        if len(set(selected)) != len(selected):
            raise ExamError(f"{where}.correct must use unique option columns for matching")

    return {
        "id": item_id,
        "kind": kind,
        "question": question,
        "options": options,
        "rows": rows,
        "correct": normalized_correct,
    }


def _normalize_exam(exam: Any) -> dict[str, Any]:
    value = _require_exact_dict(exam, _EXAM_FIELDS, "exam")
    if value["schema"] != EXAM_SCHEMA:
        raise ExamError(f"unsupported exam schema: {value['schema']!r}")
    title = _require_string(value["title"], "exam.title")
    subject = _require_string(value["subject"], "exam.subject")
    year = _require_integer(value["year"], "exam.year", positive=True)
    provenance = _validate_provenance(value["provenance"], "exam.provenance")
    raw_items = value["items"]
    if not isinstance(raw_items, list) or not raw_items:
        raise ExamError("exam.items must be a non-empty list")
    items: list[dict[str, Any]] = []
    item_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        item = _validate_item(raw_item, f"exam.items[{index}]")
        if item["id"] in item_ids:
            raise ExamError(f"duplicate exam item id {item['id']!r}")
        item_ids.add(item["id"])
        items.append(item)
    expected_points = sum(1 if item["kind"] == "single" else len(item["rows"]) for item in items)
    scoring = _validate_scoring(
        value["scoring"],
        "exam.scoring",
        expected_items=len(items),
        expected_points=expected_points,
    )
    return {
        "schema": EXAM_SCHEMA,
        "title": title,
        "subject": subject,
        "year": year,
        "provenance": provenance,
        "scoring": scoring,
        "items": items,
    }


def _packet_item(item: dict[str, Any], opaque_id: str) -> dict[str, Any]:
    return {
        "id": opaque_id,
        "kind": item["kind"],
        "question": item["question"],
        "options": [dict(choice) for choice in item["options"]],
        "rows": [dict(row) for row in item["rows"]],
    }


def prepare_exam(exam: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate an exam and return a question-only packet plus its key."""

    normalized = _normalize_exam(exam)
    packet_items = [_packet_item(item, f"q{index:04d}") for index, item in enumerate(normalized["items"], start=1)]
    packet_body = {"schema": PACKET_SCHEMA, "items": packet_items}
    packet = packet_body | {"packet_sha256": digest(packet_body)}
    key_body = {
        "schema": KEY_SCHEMA,
        "packet_sha256": packet["packet_sha256"],
        "title": normalized["title"],
        "subject": normalized["subject"],
        "year": normalized["year"],
        "provenance": {**normalized["provenance"]},
        "scoring": {**normalized["scoring"]},
        "answers": {
            packet_item["id"]: item["correct"]
            for packet_item, item in zip(packet_items, normalized["items"], strict=True)
        },
    }
    key = key_body | {"key_sha256": digest(key_body)}
    return packet, key


def _validate_packet_item(value: Any, index: int) -> dict[str, Any]:
    item = _require_exact_dict(value, _PACKET_ITEM_FIELDS, f"packet.items[{index}]")
    item_id = _require_string(item["id"], f"packet.items[{index}].id")
    expected_id = f"q{index + 1:04d}"
    if item_id != expected_id:
        raise ExamError(f"packet item ids must be consecutive opaque ids starting at q0001 (got {item_id!r})")
    kind = _require_string(item["kind"], f"packet.items[{index}].kind")
    if kind not in {"single", "matching"}:
        raise ExamError(f"unsupported item kind: {kind!r}")
    question = _require_question(item["question"], f"packet.items[{index}].question")
    options = _validate_choices(item["options"], f"packet.items[{index}].options")
    rows = _validate_rows(item["rows"], f"packet.items[{index}].rows", required=kind == "matching")
    if kind == "single" and rows:
        raise ExamError(f"packet.items[{index}].rows must be empty for a single item")
    if {choice["id"] for choice in options} & {row["id"] for row in rows}:
        raise ExamError(f"packet.items[{index}].options and rows must use disjoint ids")
    return {"id": item_id, "kind": kind, "question": question, "options": options, "rows": rows}


def validate_packet(packet: Any) -> None:
    """Validate a question packet, including its content hash and exact shape."""

    value = _require_exact_dict(packet, _PACKET_FIELDS, "packet")
    if value["schema"] != PACKET_SCHEMA:
        raise ExamError(f"unsupported packet schema: {value['schema']!r}")
    raw_items = value["items"]
    if not isinstance(raw_items, list) or not raw_items:
        raise ExamError("packet.items must be a non-empty list")
    items = [_validate_packet_item(item, index) for index, item in enumerate(raw_items)]
    expected_hash = digest({"schema": PACKET_SCHEMA, "items": items})
    if _require_digest(value["packet_sha256"], "packet.packet_sha256") != expected_hash:
        raise ExamError("packet content hash mismatch")


def _key_body(key: dict[str, Any]) -> dict[str, Any]:
    return {field: key[field] for field in _KEY_FIELDS if field != "key_sha256"}


def validate_key(packet: Any, key: Any) -> None:
    """Validate a grading key and independently bind it to packet."""

    validate_packet(packet)
    packet_value = packet
    value = _require_exact_dict(key, _KEY_FIELDS, "key")
    if value["schema"] != KEY_SCHEMA:
        raise ExamError(f"unsupported key schema: {value['schema']!r}")
    packet_hash = _require_digest(packet_value["packet_sha256"], "packet.packet_sha256")
    if value["packet_sha256"] != packet_hash:
        raise ExamError("key is bound to a different packet")
    if _require_digest(value["key_sha256"], "key.key_sha256") != digest(_key_body(value)):
        raise ExamError("key content hash mismatch")
    _require_string(value["title"], "key.title")
    _require_string(value["subject"], "key.subject")
    _require_integer(value["year"], "key.year", positive=True)
    _validate_provenance(value["provenance"], "key.provenance")

    packet_items = packet_value["items"]
    max_points = sum(1 if item["kind"] == "single" else len(item["rows"]) for item in packet_items)
    _validate_scoring(
        value["scoring"],
        "key.scoring",
        expected_items=len(packet_items),
        expected_points=max_points,
    )
    answers = value["answers"]
    if not isinstance(answers, dict) or set(answers) != {item["id"] for item in packet_items}:
        raise ExamError("key.answers must contain exactly one answer for every packet item")
    for item in packet_items:
        answer = answers[item["id"]]
        option_ids = {choice["id"] for choice in item["options"]}
        if item["kind"] == "single":
            answer_id = _require_string(answer, f"key.answers.{item['id']}")
            if answer_id not in option_ids:
                raise ExamError(f"key.answers.{item['id']} references an unknown option")
            continue
        if not isinstance(answer, dict) or set(answer) != {row["id"] for row in item["rows"]}:
            raise ExamError(f"key.answers.{item['id']} must contain exactly one answer per row")
        selected: list[str] = []
        for row in item["rows"]:
            answer_id = _require_string(answer[row["id"]], f"key.answers.{item['id']}.{row['id']}")
            if answer_id not in option_ids:
                raise ExamError(f"key.answers.{item['id']}.{row['id']} references an unknown option")
            selected.append(answer_id)
        if len(set(selected)) != len(selected):
            raise ExamError(f"key.answers.{item['id']} repeats a matching option column")


def _validate_run(packet: dict[str, Any], run: Any) -> dict[str, Any]:
    if not isinstance(run, dict):
        raise ExamError("run must be an object")
    allowed_fields = _RUN_FIELDS | _RUN_OPTIONAL_FIELDS
    if set(run) - allowed_fields or not set(run) >= _RUN_FIELDS:
        missing = sorted(_RUN_FIELDS - set(run))
        extra = sorted(set(run) - allowed_fields)
        detail: list[str] = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"unknown {extra}")
        raise ExamError(f"run has invalid fields ({'; '.join(detail)})")
    value = run
    if value["schema"] != RUN_SCHEMA:
        raise ExamError(f"unsupported run schema: {value['schema']!r}")
    if value["packet_sha256"] != packet["packet_sha256"]:
        raise ExamError("run is bound to a different packet")
    condition = _require_string(value["condition"], "run.condition")
    if condition not in _CONDITIONS:
        raise ExamError(f"unsupported run condition: {condition!r}")
    status = _require_string(value["status"], "run.status")
    if status not in _STATUSES:
        raise ExamError(f"unsupported run status: {status!r}")
    if status == "failed":
        if "failure_reason" not in value:
            raise ExamError("failed run must include failure_reason")
        _require_string(value["failure_reason"], "run.failure_reason")
    elif "failure_reason" in value and value["failure_reason"] is not None:
        raise ExamError("failure_reason must be absent or null on an ok run")
    if "repeat" in value:
        _require_integer(value["repeat"], "run.repeat", positive=True)
    responses = value["responses"]
    if not isinstance(responses, dict):
        raise ExamError("run.responses must be an object")
    packet_ids = {item["id"] for item in packet["items"]}
    for item_id, response in responses.items():
        if not isinstance(item_id, str):
            raise ExamError("run.responses ids must be strings")
        if item_id not in packet_ids:
            raise ExamError(f"run.responses contains unknown item id {item_id!r}")
        if response is not None and not isinstance(response, (str, dict)):
            raise ExamError(f"run.responses.{item_id} must be a string, object, or null")
        if isinstance(response, dict):
            _json_safe(response, where=f"run.responses.{item_id}")
    for field in ("identity", "comparison", "metrics"):
        if not isinstance(value[field], dict):
            raise ExamError(f"run.{field} must be an object")
        _json_safe(value[field], where=f"run.{field}")
    return value


def _failed_item_detail(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "kind": item["kind"],
        "max_points": None,
        "points": None,
        "correct": None,
        "missing": None,
        "invalid": None,
        "outcome": "failed",
    }


def _score_item(
    item: dict[str, Any], gold: Any, response: Any
) -> tuple[dict[str, Any], int, bool, bool, bool]:
    """Score one item; matching duplicate selections remain informational."""
    item_id = item["id"]
    kind = item["kind"]
    max_points = 1 if kind == "single" else len(item["rows"])
    if response is None:
        detail = {
            "id": item_id,
            "kind": kind,
            "max_points": max_points,
            "points": 0,
            "correct": False,
            "missing": True,
            "invalid": False,
            "outcome": "missing",
            "response": None,
            "expected": gold,
        }
        if kind == "matching":
            detail["rows"] = [
                {
                    "id": row["id"],
                    "response": None,
                    "expected": gold[row["id"]],
                    "correct": False,
                    "missing": True,
                    "duplicate": False,
                }
                for row in item["rows"]
            ]
        return detail, 0, False, True, False

    if kind == "single":
        option_ids = {choice["id"] for choice in item["options"]}
        if not isinstance(response, str) or response not in option_ids:
            detail = {
                "id": item_id,
                "kind": kind,
                "max_points": max_points,
                "points": 0,
                "correct": False,
                "missing": False,
                "invalid": True,
                "outcome": "invalid",
                "response": response,
                "expected": gold,
            }
            return detail, 0, False, False, True
        is_correct = response == gold
        detail = {
            "id": item_id,
            "kind": kind,
            "max_points": max_points,
            "points": int(is_correct),
            "correct": is_correct,
            "missing": False,
            "invalid": False,
            "outcome": "correct" if is_correct else "incorrect",
            "response": response,
            "expected": gold,
        }
        return detail, int(is_correct), is_correct, False, False

    if not isinstance(response, dict):
        detail = {
            "id": item_id,
            "kind": kind,
            "max_points": max_points,
            "points": 0,
            "correct": False,
            "missing": False,
            "invalid": True,
            "outcome": "invalid",
            "response": response,
            "expected": gold,
        }
        return detail, 0, False, False, True

    row_ids = {row["id"] for row in item["rows"]}
    option_ids = {choice["id"] for choice in item["options"]}
    if any(not isinstance(row_id, str) or not isinstance(option_id, str) for row_id, option_id in response.items()):
        detail = {
            "id": item_id,
            "kind": kind,
            "max_points": max_points,
            "points": 0,
            "correct": False,
            "missing": False,
            "invalid": True,
            "outcome": "invalid",
            "response": response,
            "expected": gold,
        }
        return detail, 0, False, False, True
    if set(response) - row_ids or set(response.values()) - option_ids:
        detail = {
            "id": item_id,
            "kind": kind,
            "max_points": max_points,
            "points": 0,
            "correct": False,
            "missing": False,
            "invalid": True,
            "outcome": "invalid",
            "response": dict(response),
            "expected": gold,
        }
        return detail, 0, False, False, True

    selected_counts = Counter(response.values())
    row_details: list[dict[str, Any]] = []
    points = 0
    for row in item["rows"]:
        row_id = row["id"]
        selected = response.get(row_id)
        missing = selected is None
        duplicate = selected is not None and selected_counts[selected] > 1
        # Official NMT descriptions award points per correctly determined
        # logical pair. A repeated option is exposed in ``duplicate`` for
        # diagnostics, but does not erase an independently correct pair.
        is_correct = not missing and selected == gold[row_id]
        points += int(is_correct)
        row_details.append(
            {
                "id": row_id,
                "response": selected,
                "expected": gold[row_id],
                "correct": is_correct,
                "missing": missing,
                "duplicate": duplicate,
            }
        )
    is_correct_item = points == max_points
    detail = {
        "id": item_id,
        "kind": kind,
        "max_points": max_points,
        "points": points,
        "correct": is_correct_item,
        "missing": False,
        "invalid": False,
        "outcome": "correct" if is_correct_item else "incorrect",
        "response": dict(response),
        "expected": dict(gold),
        "rows": row_details,
    }
    return detail, points, is_correct_item, False, False


def score_run(packet: dict[str, Any], key: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Validate and score one run without repairing or guessing answers."""

    validate_key(packet, key)
    run_value = _validate_run(packet, run)
    scoring = key["scoring"]
    denominator = {"items": len(packet["items"]), "points": scoring["expected_points"]}
    if run_value["status"] == "failed":
        return {
            "schema": "zno-nmt.score.v1",
            "packet_sha256": packet["packet_sha256"],
            "condition": run_value["condition"],
            "status": "failed",
            "denominator": denominator,
            "raw_points": None,
            "max_points": None,
            "correct_items": None,
            "missing_items": None,
            "invalid_items": None,
            "passed": None,
            "scoring_kind": scoring["kind"],
            "items": [_failed_item_detail(item) for item in packet["items"]],
            "identity": dict(run_value["identity"]),
            "comparison": dict(run_value["comparison"]),
            "metrics": dict(run_value["metrics"]),
            "failure_reason": run_value.get("failure_reason"),
        }

    answer_map = key["answers"]
    details: list[dict[str, Any]] = []
    raw_points = 0
    correct_items = 0
    missing_items = 0
    invalid_items = 0
    for item in packet["items"]:
        response = run_value["responses"].get(item["id"])
        detail, points, is_correct, missing, invalid = _score_item(item, answer_map[item["id"]], response)
        details.append(detail)
        raw_points += points
        correct_items += int(is_correct)
        missing_items += int(missing)
        invalid_items += int(invalid)
    max_points = denominator["points"]
    if scoring["kind"] == "benchmark":
        passed: bool | None = None
    else:
        threshold = scoring["pass_threshold"]
        passed = bool(scoring["policy_url"] and threshold is not None and raw_points >= threshold)
    return {
        "schema": "zno-nmt.score.v1",
        "packet_sha256": packet["packet_sha256"],
        "condition": run_value["condition"],
        "status": "ok",
        "denominator": denominator,
        "raw_points": raw_points,
        "max_points": max_points,
        "correct_items": correct_items,
        "missing_items": missing_items,
        "invalid_items": invalid_items,
        "passed": passed,
        "scoring_kind": scoring["kind"],
        "items": details,
        "identity": dict(run_value["identity"]),
        "comparison": dict(run_value["comparison"]),
        "metrics": dict(run_value["metrics"]),
        "failure_reason": None,
    }


def _score_summary(score: dict[str, Any]) -> dict[str, Any]:
    return {
        field: score[field]
        for field in (
            "condition",
            "status",
            "raw_points",
            "max_points",
            "correct_items",
            "missing_items",
            "invalid_items",
            "passed",
        )
    }


def _metric_report(control: dict[str, Any], treatment: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for name in ("tool_calls", "elapsed_seconds", "runtime_ms", "cost_usd"):
        control_value = control.get(name)
        treatment_value = treatment.get(name)
        if (
            isinstance(control_value, (int, float))
            and not isinstance(control_value, bool)
            and math.isfinite(control_value)
            and isinstance(treatment_value, (int, float))
            and not isinstance(treatment_value, bool)
            and math.isfinite(treatment_value)
        ):
            report[name] = {
                "control": control_value,
                "treatment": treatment_value,
                "delta": treatment_value - control_value,
            }
        else:
            report[name] = {"control": None, "treatment": None, "delta": None}
    return report


def _paired_identity_value(identity: dict[str, Any], field: str) -> Any:
    aliases = {
        "model": ("model", "effective_model", "requested_model"),
        "harness": ("harness", "adapter"),
        "effective_effort": ("effective_effort",),
    }[field]
    for name in aliases:
        if name in identity:
            return identity[name]
    raise ExamError(f"paired run identity is missing {field!r}")


def _check_paired_identity(control: dict[str, Any], treatment: dict[str, Any]) -> dict[str, Any]:
    """Require every available requested/effective identity field to pair."""

    paired: dict[str, Any] = {}
    for field in ("model", "harness", "effective_effort"):
        paired[field] = _paired_identity_value(control, field)
        treatment_value = _paired_identity_value(treatment, field)
        if paired[field] != treatment_value:
            raise ExamError(f"paired runs have different identity field {field!r}")

    # Runner artifacts carry both requested and effective model/effort
    # evidence. Compare both independently; an explicit unknown remains an
    # honest equal value rather than being replaced by the requested setting.
    for field in ("requested_model", "effective_model", "requested_effort"):
        control_present = field in control
        treatment_present = field in treatment
        if control_present != treatment_present:
            raise ExamError(f"paired run identity is missing {field!r}")
        if control_present and control[field] != treatment[field]:
            raise ExamError(f"paired runs have different identity field {field!r}")
        if control_present:
            paired[field] = control[field]
    return paired


def compare_runs(
    packet: dict[str, Any],
    key: dict[str, Any],
    control: dict[str, Any],
    treatment: dict[str, Any],
) -> dict[str, Any]:
    """Compare a paired closed-book/sources run on one exact packet.

    The function reports descriptive paired differences only. A single exam
    paper is not a significance study, so no inferential statistic is emitted.
    """

    validate_key(packet, key)
    control_value = _validate_run(packet, control)
    treatment_value = _validate_run(packet, treatment)
    if control_value["condition"] != "closed-book" or treatment_value["condition"] != "sources":
        raise ExamError("control must be closed-book and treatment must use sources")
    if control_value["status"] != "ok" or treatment_value["status"] != "ok":
        raise ExamError("cannot compare a failed run")
    if control_value["comparison"] != treatment_value["comparison"]:
        raise ExamError("paired runs have different comparison configuration")
    paired_identity = _check_paired_identity(control_value["identity"], treatment_value["identity"])

    control_score = score_run(packet, key, control_value)
    treatment_score = score_run(packet, key, treatment_value)
    per_item: list[dict[str, Any]] = []
    wins = losses = ties = 0
    for control_item, treatment_item in zip(control_score["items"], treatment_score["items"], strict=True):
        control_points = control_item["points"]
        treatment_points = treatment_item["points"]
        if treatment_points > control_points:
            outcome = "win"
            wins += 1
        elif treatment_points < control_points:
            outcome = "loss"
            losses += 1
        else:
            outcome = "tie"
            ties += 1
        per_item.append(
            {
                "id": control_item["id"],
                "control_points": control_points,
                "treatment_points": treatment_points,
                "outcome": outcome,
            }
        )
    metric_report = _metric_report(control_value["metrics"], treatment_value["metrics"])
    return {
        "schema": COMPARISON_SCHEMA,
        "packet_sha256": packet["packet_sha256"],
        "control": _score_summary(control_score),
        "treatment": _score_summary(treatment_score),
        "control_points": control_score["raw_points"],
        "treatment_points": treatment_score["raw_points"],
        "score_delta": treatment_score["raw_points"] - control_score["raw_points"],
        "per_item": per_item,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "metrics": metric_report,
        "identity": paired_identity,
        "comparison": dict(control_value["comparison"]),
        "significance": None,
    }


__all__ = [
    "ExamError",
    "canonical",
    "compare_runs",
    "digest",
    "prepare_exam",
    "read_json",
    "score_run",
    "validate_key",
    "validate_packet",
    "write_private_json",
]
