"""Minimal readers for the evidence pack and the level word store (Brief A).

Isolated on purpose: #8413 replaces this module with the real pack tooling.
A module pack (evidence/<level>/<slug>.yaml) holds top-level lists `texts`,
`exercises`, `examples`, `errors`, `videos`, `standard` of records carrying
`id`, and no `words:` list — its presence fails. The word store
(evidence/<level>/_words.yaml) holds `words[] {id, lemma, forms[] {tags}}`.
A `<file>.lock` sidecar sits beside each file; its first whitespace-delimited
token is the lowercase hex sha256 of the file's bytes. Duplicate ids fail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import codes
from .loader import PlanError

PACK_LISTS = ("texts", "exercises", "examples", "errors", "videos", "standard")

_LOCK_TOKEN = re.compile(r"^([0-9a-f]{64})\b")


def _read_yaml(path: Path, not_found: str, invalid: str) -> object:
    if not path.is_file():
        raise PlanError(not_found, f"{path} does not exist")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise PlanError(invalid, f"{path} is not valid YAML: {error}") from error


def lock_digest(path: Path, failure_code: str) -> str:
    """The sha256 recorded in <path>.lock; any deviation fails closed with failure_code."""
    lock = Path(f"{path}.lock")
    try:
        token = _LOCK_TOKEN.match(lock.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError) as error:
        raise PlanError(failure_code, f"{lock} is missing or unreadable: {error}") from error
    if not token:
        raise PlanError(failure_code, f"{lock} does not start with a lowercase hex sha256 token")
    return token.group(1)


@dataclass(frozen=True)
class Pack:
    """The module evidence pack: every record id it defines, and its error records."""

    path: Path
    ids: frozenset[str] = field(default_factory=frozenset)
    error_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class WordRecord:
    id: str
    lemma: str
    form_tags: frozenset[str]


@dataclass(frozen=True)
class WordStore:
    path: Path
    records: dict[str, WordRecord] = field(default_factory=dict)


def load_pack(pack_path: Path) -> Pack:
    """Load the module pack, rejecting a words: list and duplicate ids."""
    data = _read_yaml(pack_path, codes.PACK_NOT_FOUND, codes.PACK_YAML_INVALID)
    if not isinstance(data, dict):
        raise PlanError(codes.PACK_MALFORMED, f"{pack_path} does not hold a mapping at the top level")
    if "words" in data:
        raise PlanError(
            codes.PACK_WORDS_LIST_PRESENT,
            f"{pack_path} carries a words: list; a module pack holds no words — "
            "word records live in the level word store evidence/<level>/_words.yaml (§3)",
        )
    ids: set[str] = set()
    error_ids: set[str] = set()
    for list_name in PACK_LISTS:
        records = data.get(list_name, [])
        if records is None:
            continue
        if not isinstance(records, list):
            raise PlanError(codes.PACK_MALFORMED, f"{pack_path}: {list_name} is not a list")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                raise PlanError(
                    codes.PACK_MALFORMED, f"{pack_path}: a record in {list_name} has no string id: {record!r}"
                )
            if record["id"] in ids:
                raise PlanError(codes.DUPLICATE_PACK_ID, f"{pack_path}: id {record['id']} appears twice")
            ids.add(record["id"])
            if list_name == "errors":
                error_ids.add(record["id"])
    return Pack(path=pack_path, ids=frozenset(ids), error_ids=frozenset(error_ids))


def load_words(words_path: Path) -> WordStore:
    """Load the level word store, rejecting duplicate ids."""
    data = _read_yaml(words_path, codes.WORDS_NOT_FOUND, codes.WORDS_YAML_INVALID)
    if not isinstance(data, dict) or not isinstance(data.get("words"), list):
        raise PlanError(codes.WORDS_MALFORMED, f"{words_path} does not hold a words: list")
    records: dict[str, WordRecord] = {}
    for entry in data["words"]:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("id"), str)
            or not isinstance(entry.get("lemma"), str)
            or not isinstance(entry.get("forms"), list)
        ):
            raise PlanError(codes.WORDS_MALFORMED, f"{words_path}: a word record lacks id, lemma or forms: {entry!r}")
        tags: set[str] = set()
        for form in entry["forms"]:
            if not isinstance(form, dict) or not isinstance(form.get("tags"), str):
                raise PlanError(
                    codes.WORDS_MALFORMED, f"{words_path}: a form of {entry['id']} has no string tags: {form!r}"
                )
            tags.add(form["tags"])
        if entry["id"] in records:
            raise PlanError(codes.DUPLICATE_WORD_ID, f"{words_path}: id {entry['id']} appears twice")
        records[entry["id"]] = WordRecord(id=entry["id"], lemma=entry["lemma"], form_tags=frozenset(tags))
    return WordStore(path=words_path, records=records)
