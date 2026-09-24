"""Stable per-lesson regeneration ledger for fresh builds."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lock

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "fresh-regeneration-ledger-v1.schema.json"
INPUT_KEYS = ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")


def _validate(doc: dict[str, Any]) -> None:
    schema = json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)


def load_ledger(path: Path, slug: str, n: int) -> dict[str, Any]:
    if not path.exists():
        return {"slug": slug, "n": n, "attempts": [], "regenerations": 0, "terminal_layer": None}
    lock.require(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(doc)
    if (doc["slug"], doc["n"]) != (slug, n):
        raise ValueError("regeneration ledger belongs to another lesson")
    return doc


def record_failure(path: Path, slug: str, n: int, failure: dict[str, Any], inputs: dict[str, str], *,
                   at: str | None = None) -> dict[str, Any]:
    """Record a failed attempt; repeated checks and the third failure are terminal."""
    doc = load_ledger(path, slug, n)
    if doc["terminal_layer"] is not None:
        return doc
    previous = doc["attempts"]
    doc.pop("last_success", None)
    layer = failure["layer"]
    if layer not in {"writer", "plan", "pack", "word_store", "engine", "driver"}:
        raise ValueError(f"unknown failure layer {layer!r}")
    previous_same = any(row["failed_check"] == failure["check"] for row in previous)
    prior_count = doc["regenerations"]
    if previous:
        doc["regenerations"] = min(2, prior_count + 1)
    previous.append({
        "attempt": len(previous) + 1,
        "failed_check": failure["check"],
        "code": failure.get("code", str(failure["check"])),
        "reason": failure["reason"],
        "at": at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "inputs": {key: inputs.get(key, "0" * 64) for key in INPUT_KEYS},
    })
    if previous_same:
        doc["terminal_layer"] = {"writer": "plan", "plan": "plan", "pack": "pack", "word_store": "pack",
                                 "engine": "driver", "driver": "driver"}[layer]
    elif doc["regenerations"] >= 2:
        doc["terminal_layer"] = "driver"
    _validate(doc)
    lock.write(path, lock.yaml_bytes(doc))
    return doc


def record_success(path: Path, slug: str, n: int, inputs: dict[str, str] | None = None, *,
                   at: str | None = None) -> dict[str, Any]:
    """Count a regeneration that succeeded without another failure row."""
    doc = load_ledger(path, slug, n)
    if doc["terminal_layer"] is None:
        doc["regenerations"] = min(2, max(doc["regenerations"], len(doc["attempts"])))
        if inputs is not None:
            previous = doc.get("last_success") or {}
            if previous.get("inputs") != inputs:
                doc["last_success"] = {"at": at or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                                       "through_check": 12, "inputs": dict(inputs)}
        _validate(doc)
        lock.write(path, lock.yaml_bytes(doc))
    return doc


def invalidate_lesson_resolution(state_dir: Path, n: int) -> None:
    """Invalidate only this lesson's questions and receipts before regeneration."""
    for suffix in ("questions.yaml", "resolutions.yaml"):
        path = state_dir / f"lesson-{n}.{suffix}"
        for candidate in (path, Path(f"{path}.lock")):
            candidate.unlink(missing_ok=True)
