"""Append-only level id ledger. Allocation identity never changes or disappears.

The ledger is a YAML list; allocated_at_build is the caller's deterministic
build fingerprint, never an implicit wall-clock timestamp. ULIF enrichment is
stored on the word record without rewriting the original allocation identity.
"""

import re
from copy import deepcopy
from pathlib import Path

import yaml

from . import codes, lock

ID_RE = re.compile(r"W-([0-9]+)\Z")
FIELDS = {"id", "lemma", "pos", "entry", "allocated_at_build", "retired"}


def _fail(value: object) -> None:
    raise ValueError(f"{codes.REGISTRY_MISMATCH}: {value!r}")


def number(word_id: str) -> int:
    match = ID_RE.fullmatch(word_id) if isinstance(word_id, str) else None
    if match is None or int(match[1]) < 1:
        _fail(word_id)
    return int(match[1])


def validate(records: list[dict]) -> None:
    if not isinstance(records, list):
        _fail(records)
    previous = 0
    identities = []
    for record in records:
        if not isinstance(record, dict) or set(record) - FIELDS or FIELDS - {"retired"} - set(record):
            _fail(record)
        current = number(record["id"])
        if current <= previous:
            _fail(record)
        previous = current
        if any(not isinstance(record[key], str) or not record[key] for key in ("lemma", "pos", "allocated_at_build")):
            _fail(record)
        if "retired" in record and record["retired"] is not True:
            _fail(record)
        entry = record["entry"]
        if entry != "unresolved":
            if not isinstance(entry, dict):
                _fail(record)
            if entry.get("source") == "vesum":
                if set(entry) != {"source", "entry_id"} or type(entry["entry_id"]) is not int or entry["entry_id"] < 1:
                    _fail(record)
            elif entry.get("source") == "ulif":
                key = entry.get("key")
                if set(entry) != {"source", "key"} or not isinstance(key, list) or len(key) != 2:
                    _fail(record)
                if not isinstance(key[0], str) or not key[0] or type(key[1]) is not int or key[1] < 1:
                    _fail(record)
            else:
                _fail(record)
        if not record.get("retired"):
            identity = (record["lemma"], record["pos"], entry)
            if identity in identities:
                _fail(record)
            identities.append(identity)


def load(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        if Path(f"{path}.lock").exists():
            _fail(str(path))
        return []
    lock.require(path)
    records = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate(records)
    return records


def allocate(records: list[dict], *, lemma: str, pos: str, entry: dict | str, allocated_at_build: str) -> str:
    """Append a new allocation; duplicate active identities require an explicit update."""
    validate(records)
    word_id = f"W-{max((number(row['id']) for row in records), default=0) + 1:03d}"
    row = {
        "id": word_id,
        "lemma": lemma,
        "pos": pos,
        "entry": deepcopy(entry),
        "allocated_at_build": allocated_at_build,
    }
    validate([*records, row])
    records.append(row)
    return word_id


def retire(records: list[dict], word_id: str) -> None:
    validate(records)
    for record in records:
        if record["id"] == word_id:
            record["retired"] = True
            return
    _fail(word_id)


def write(path: Path, records: list[dict]) -> str:
    """Require the locked previous ledger as a prefix; only retirement may change."""
    validate(records)
    old = load(path)
    if len(records) < len(old):
        _fail(records)
    for before, after in zip(old, records, strict=False):
        expected = dict(before)
        if after.get("retired"):
            expected["retired"] = True
        if after != expected:
            _fail(after)
    return lock.write(path, lock.yaml_bytes(records))


def check_store(records: list[dict], words: list[dict]) -> None:
    """Check active ids and original identities; unresolved allocations may resolve."""
    validate(records)
    active = {row["id"]: row for row in records if not row.get("retired")}
    if len({word["id"] for word in words}) != len(words) or set(active) != {word["id"] for word in words}:
        _fail([word["id"] for word in words])
    for word in words:
        original = active[word["id"]]
        if any(word.get(key) != original[key] for key in ("lemma", "pos")):
            _fail(word)
        if original["entry"] != "unresolved" and original["entry"] != word.get("entry"):
            _fail(word)
