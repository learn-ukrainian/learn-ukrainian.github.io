"""Stable per-lesson regeneration ledger for fresh builds."""

from __future__ import annotations

import fcntl
import hashlib
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError

from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lock

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "fresh-regeneration-ledger-v1.schema.json"
HARNESS_SCHEMA = SCHEMA.with_name("fresh-writer-harness-v1.schema.json")
# Same bound as the fresh ledger: one initial attempt plus two retries.
MAX_HARNESS_FAILURES = 3
HARNESS_EXHAUSTED = "writer_harness_exhausted"
INPUT_KEYS = ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")


@contextmanager
def lesson_mutex(path: Path) -> Iterator[None]:
    """Serialize a whole transaction; the .lock file remains a digest, never a mutex."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with Path(f"{path}.mutex").open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _serialized(function):
    @wraps(function)
    def transaction(path, *args, **kwargs):
        with lesson_mutex(path):
            return function(path, *args, **kwargs)

    return transaction


def inputs_digest(inputs: Mapping[str, str]) -> str:
    """Short digest of an attempt's ``INPUT_KEYS`` values; missing keys count as zeros, as in the ledger."""
    values = [inputs.get(key, "0" * 64) for key in INPUT_KEYS]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode("ascii")).hexdigest()[:10]


def writer_inputs(hashes: Mapping[str, str], card_sha256: str, prompt_sha256: str) -> dict[str, str]:
    """The complete ``INPUT_KEYS`` snapshot every writer entry point keys its task ID and ledger on (#8425)."""
    return {
        "plan_sha256": hashes["plan_sha256"],
        "pack_lock": hashes["pack_lock"],
        "words_lock": hashes["words_lock"],
        "card_sha256": card_sha256,
        "prompt_sha256": prompt_sha256,
    }


def writer_task_id(level: str, slug: str, n: int, attempt: int, effort: str | None, inputs: Mapping[str, str]) -> str:
    """Key dispatch attempts by inputs and effort; keep the lesson's regeneration budget separate.

    Changed inputs restart the ledger at attempt 1, so their digest keeps a new run from reusing an earlier
    run's ID; identical inputs keep the same base ID whichever entry point dispatches them. The writer
    reuses a done record and only adds a retry suffix after a terminal non-done record, retaining all
    prior evidence. Omitting effort keeps the seat's own default.
    """
    task_id = f"write-{level}-{slug}-{n}-{attempt}-{inputs_digest(inputs)}"
    return f"{task_id}-{effort}" if effort is not None else task_id


def _validate(doc: dict[str, Any]) -> None:
    schema = json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)


def _load_ledger(path: Path, slug: str, n: int, inputs: dict[str, str] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {"slug": slug, "n": n, "attempts": [], "regenerations": 0, "terminal_layer": None}
    lock.require(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(doc)
    if (doc["slug"], doc["n"]) != (slug, n):
        raise ValueError("regeneration ledger belongs to another lesson")
    if (
        inputs is not None
        and doc["attempts"]
        and any(doc["attempts"][-1]["inputs"][key] != inputs.get(key, "0" * 64) for key in INPUT_KEYS)
    ):
        doc.update(attempts=[], regenerations=0, terminal_layer=None)
    return doc


@_serialized
def load_ledger(path: Path, slug: str, n: int, inputs: dict[str, str] | None = None) -> dict[str, Any]:
    """Read a consistent data/digest pair under the lesson transaction mutex."""
    return _load_ledger(path, slug, n, inputs)


@_serialized
def record_writer_call(path: Path, slug: str, n: int, inputs: dict[str, str] | None = None) -> dict[str, Any]:
    """Count delivered retries by completed failures, so re-harvesting a done reply is idempotent.

    Dispatch/harness failures never call this. An interrupted check can harvest the same
    successful task again without consuming another regeneration.
    """
    doc = _load_ledger(path, slug, n, inputs)
    if doc["terminal_layer"] is not None:
        return doc
    if doc.get("last_success") or not doc["attempts"]:
        doc.update(attempts=[], regenerations=0)
    else:
        if len(doc["attempts"]) > 2:
            doc["terminal_layer"] = "driver"
        else:
            doc["regenerations"] = max(doc["regenerations"], len(doc["attempts"]))
    _validate(doc)
    lock.write(path, lock.yaml_bytes(doc))
    return doc


@_serialized
def record_harness_failure(
    path: Path, slug: str, n: int, reason: str, inputs: dict[str, str], *, at: str | None = None
) -> dict[str, Any]:
    """Bound harness failures separately, without spending the content budget."""
    evidence_path = path.with_name(f"lesson-{n}.writer-harness.yaml")
    evidence = _load_harness(path, slug, n)
    if evidence["terminal_state"] is None:
        evidence["failures"].append(
            {"reason": reason, "inputs": dict(inputs), "at": at or datetime.now(UTC).isoformat().replace("+00:00", "Z")}
        )
        if len(evidence["failures"]) >= MAX_HARNESS_FAILURES:
            evidence["terminal_state"] = HARNESS_EXHAUSTED
        _validate_harness(evidence)
        lock.write(evidence_path, lock.yaml_bytes(evidence))
    doc = _load_ledger(path, slug, n, inputs)
    if evidence["terminal_state"] is not None:
        doc["terminal_layer"] = "driver"
    return doc


def _validate_harness(doc: dict[str, Any]) -> None:
    schema = json.loads(
        checked_existing_path(HARNESS_SCHEMA.parents[1], HARNESS_SCHEMA, "schemas").read_text(encoding="utf-8")
    )
    try:
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(doc)
    except ValidationError as err:
        raise ValueError(f"writer harness schema invalid: {err.message}") from err
    # jsonschema's date-time checker is optional and absent in some installs.
    # Validate timestamps with the standard library instead of silently skipping it.
    for row in doc["failures"]:
        moment = datetime.fromisoformat(row["at"])
        if moment.tzinfo is None or "t" not in row["at"].lower():
            raise ValueError("writer harness timestamp must include time and timezone")
    state = doc.get("terminal_state")
    if state is not None and len(doc["failures"]) < MAX_HARNESS_FAILURES:
        raise ValueError("writer harness terminal state precedes its failure cap")


def _load_harness(path: Path, slug: str, n: int) -> dict[str, Any]:
    evidence_path = path.with_name(f"lesson-{n}.writer-harness.yaml")
    if not evidence_path.exists():
        return {"slug": slug, "n": n, "layer": "harness", "failures": [], "terminal_state": None}
    lock.require(evidence_path)
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    _validate_harness(evidence)
    if (evidence["slug"], evidence["n"]) != (slug, n):
        raise ValueError("writer harness evidence belongs to another lesson")
    # Valid pre-schema sidecars are retained; derive the stop state from their history.
    evidence["terminal_state"] = HARNESS_EXHAUSTED if len(evidence["failures"]) >= MAX_HARNESS_FAILURES else None
    return evidence


@_serialized
def load_harness(path: Path, slug: str, n: int) -> dict[str, Any]:
    """Validate and read harness history, including compatible pre-schema records."""
    return _load_harness(path, slug, n)


@_serialized
def record_failure(
    path: Path, slug: str, n: int, failure: dict[str, Any], inputs: dict[str, str], *, at: str | None = None
) -> dict[str, Any]:
    """Record a failed attempt; repeated checks and the third failure are terminal."""
    doc = _load_ledger(path, slug, n, inputs)
    if doc["terminal_layer"] is not None:
        return doc
    if doc.get("last_success") or not doc["attempts"]:
        doc.update(attempts=[], regenerations=0)
    previous = doc["attempts"]
    doc.pop("last_success", None)
    layer = failure["layer"]
    if layer not in {"writer", "plan", "pack", "word_store", "engine", "driver"}:
        raise ValueError(f"unknown failure layer {layer!r}")
    previous_same = any(row["failed_check"] == failure["check"] for row in previous)
    # Both delivered writer replies and direct runner failures use the completed-attempt count.
    doc["regenerations"] = max(doc["regenerations"], min(2, len(previous)))
    previous.append(
        {
            "attempt": len(previous) + 1,
            "failed_check": failure["check"],
            "code": failure.get("code", str(failure["check"])),
            "reason": failure["reason"],
            "at": at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "inputs": {key: inputs.get(key, "0" * 64) for key in INPUT_KEYS},
        }
    )
    if previous_same:
        doc["terminal_layer"] = {
            "writer": "plan",
            "plan": "plan",
            "pack": "pack",
            "word_store": "pack",
            "engine": "driver",
            "driver": "driver",
        }[layer]
    elif doc["regenerations"] >= 2:
        doc["terminal_layer"] = "driver"
    _validate(doc)
    lock.write(path, lock.yaml_bytes(doc))
    return doc


@_serialized
def record_success(
    path: Path, slug: str, n: int, inputs: dict[str, str] | None = None, *, at: str | None = None
) -> dict[str, Any]:
    """Count a regeneration that succeeded without another failure row."""
    doc = _load_ledger(path, slug, n, inputs)
    if doc["terminal_layer"] is None:
        if not doc.get("last_success"):
            doc["regenerations"] = min(2, max(doc["regenerations"], len(doc["attempts"])))
        if inputs is not None:
            previous = doc.get("last_success") or {}
            if previous.get("inputs") != inputs:
                doc["last_success"] = {
                    "at": at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "through_check": 12,
                    "inputs": dict(inputs),
                }
        else:
            # A caller without an input snapshot still ends the failed-attempt series.
            doc["attempts"] = []
        _validate(doc)
        lock.write(path, lock.yaml_bytes(doc))
    return doc


def invalidate_lesson_resolution(state_dir: Path, n: int) -> None:
    """Invalidate only this lesson's questions and receipts before regeneration."""
    for suffix in ("questions.yaml", "resolutions.yaml"):
        path = state_dir / f"lesson-{n}.{suffix}"
        for candidate in (path, Path(f"{path}.lock")):
            candidate.unlink(missing_ok=True)
