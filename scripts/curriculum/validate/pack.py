"""Minimal readers for the evidence pack and the level word store (Brief A).

Isolated on purpose: #8413 replaces this module with the real pack tooling.
A module pack (evidence/<level>/<slug>.yaml) holds top-level lists `texts`,
`exercises`, `examples`, `errors`, `videos`, `standard` of records carrying
`id`, and no `words:` list — its presence fails. A video record's explicit
listening models (`models: {letters, words}`) are kept; descriptions never
establish models (evidence-pack-v1 schema). A text record's `quote` bytes and a
video record's `url`, `models.segment` and `use` are kept for the review gates (#9487), as are
the printable text of text, exercise and example records and an example's `sentence_ref.words`.
The word store
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
class VideoModels:
    """A video record's explicit listening models: Ukrainian letters, word-store ids and the timed segment."""

    letters: tuple[str, ...] = ()
    words: tuple[str, ...] = ()
    #: models.segment: the part of the recording that models them; None is the whole recording.
    segment: str | None = None


@dataclass(frozen=True)
class Pack:
    """The module evidence pack: every record id it defines, its error records and its video models."""

    path: Path
    ids: frozenset[str] = field(default_factory=frozenset)
    error_ids: frozenset[str] = field(default_factory=frozenset)
    #: V- id -> its explicit models; a video record without a models mapping is absent here.
    video_models: dict[str, VideoModels] = field(default_factory=dict)
    #: T- id -> the record's quote bytes, as the engine would print them; a text record without a quote is absent.
    quotes: dict[str, str] = field(default_factory=dict)
    #: V- id -> (url, models.segment or None); a video record without a string url is absent.
    video_sources: dict[str, tuple[str, str | None]] = field(default_factory=dict)
    #: V- id -> the record's `use` line, which the assembler prints when the plan gives none.
    video_uses: dict[str, str] = field(default_factory=dict)
    #: text, exercise or example id -> its printable Ukrainian (quote, text, items_sample), one line each.
    record_texts: dict[str, str] = field(default_factory=dict)
    #: EX- id -> (sentence text, the word ids of its sentence_ref).
    examples: dict[str, tuple[str, tuple[str, ...]]] = field(default_factory=dict)


@dataclass(frozen=True)
class WordRecord:
    id: str
    lemma: str
    form_tags: frozenset[str]
    #: The surface text of every form the record lists (the lemma is not added).
    form_texts: tuple[str, ...] = ()
    #: The record's CEFR level as the store spells it ("A1"…"C2"); None when it carries none.
    cefr_level: str | None = None
    #: (tags, surface text) of every form that carries a text, in store order.
    tagged_forms: tuple[tuple[str, str], ...] = ()


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
    video_models: dict[str, VideoModels] = {}
    quotes: dict[str, str] = {}
    video_sources: dict[str, tuple[str, str | None]] = {}
    video_uses: dict[str, str] = {}
    record_texts: dict[str, str] = {}
    examples: dict[str, tuple[str, tuple[str, ...]]] = {}
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
            if list_name == "texts" and isinstance(record.get("quote"), str):
                quotes[record["id"]] = record["quote"]
            if list_name == "videos" and isinstance(record.get("models"), dict):
                models = record["models"]
                video_models[record["id"]] = VideoModels(
                    letters=tuple(item for item in models.get("letters") or [] if isinstance(item, str)),
                    words=tuple(item for item in models.get("words") or [] if isinstance(item, str)),
                    segment=models["segment"] if isinstance(models.get("segment"), str) else None,
                )
            if list_name == "videos" and isinstance(record.get("url"), str):
                segment = (
                    (record.get("models") or {}).get("segment") if isinstance(record.get("models"), dict) else None
                )
                video_sources[record["id"]] = (record["url"], segment if isinstance(segment, str) else None)
            if list_name == "videos" and isinstance(record.get("use"), str):
                video_uses[record["id"]] = record["use"]
            if list_name in ("texts", "exercises", "examples"):
                printable = [record.get(key) for key in ("quote", "text")]
                printable += record.get("items_sample") if isinstance(record.get("items_sample"), list) else []
                if any(isinstance(item, str) for item in printable):
                    record_texts[record["id"]] = "\n".join(item for item in printable if isinstance(item, str))
            if list_name == "examples" and isinstance(record.get("text"), str):
                sentence_ref = record.get("sentence_ref") if isinstance(record.get("sentence_ref"), dict) else {}
                words = sentence_ref.get("words") if isinstance(sentence_ref.get("words"), list) else []
                examples[record["id"]] = (record["text"], tuple(item for item in words if isinstance(item, str)))
    return Pack(
        path=pack_path,
        ids=frozenset(ids),
        error_ids=frozenset(error_ids),
        video_models=video_models,
        quotes=quotes,
        video_sources=video_sources,
        video_uses=video_uses,
        record_texts=record_texts,
        examples=examples,
    )


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
        form_texts: list[str] = []
        tagged_forms: list[tuple[str, str]] = []
        for form in entry["forms"]:
            if not isinstance(form, dict) or not isinstance(form.get("tags"), str):
                raise PlanError(
                    codes.WORDS_MALFORMED, f"{words_path}: a form of {entry['id']} has no string tags: {form!r}"
                )
            tags.add(form["tags"])
            if isinstance(form.get("form"), str):
                form_texts.append(form["form"])
                tagged_forms.append((form["tags"], form["form"]))
        if entry["id"] in records:
            raise PlanError(codes.DUPLICATE_WORD_ID, f"{words_path}: id {entry['id']} appears twice")
        cefr = entry.get("cefr")
        cefr_level = cefr.get("level") if isinstance(cefr, dict) and isinstance(cefr.get("level"), str) else None
        records[entry["id"]] = WordRecord(
            id=entry["id"],
            lemma=entry["lemma"],
            form_tags=frozenset(tags),
            form_texts=tuple(form_texts),
            cefr_level=cefr_level,
            tagged_forms=tuple(tagged_forms),
        )
    return WordStore(path=words_path, records=records)
