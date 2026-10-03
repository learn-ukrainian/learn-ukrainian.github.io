"""Load and validate the private evaluation set and the preamble variants.

Set format (one JSON object, private, passed by path)::

    {
      "set_id": "uk-preamble-v1",
      "review": [
        {"id": "R01", "text": "...",
         "errors": [{"id": "R01-e1", "start": 4, "end": 9, "span": "...",
                     "error_type": "paronym", "accepted": ["...", "..."],
                     "origin": "ua-gec"}],
         "protected": [{"id": "R01-p1", "start": 20, "end": 25, "span": "...",
                        "kind": "heritage"}]}
      ],
      "writing": [{"id": "W01", "level": "B1", "instruction": "...",
                   "min_words": 120, "max_words": 180}]
    }

Offsets are 0-based Python string offsets into ``text`` (end exclusive) and
``span`` must equal ``text[start:end]``. Error spans and protected spans never
overlap. An empty error span marks an insertion point (e.g. a missing comma).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import (
    BASELINE_VARIANT,
    CEFR_LEVELS,
    ERROR_TYPES,
    PROTOCOL_MIN_ERRORS,
    PROTOCOL_MIN_PROTECTED,
    PROTOCOL_WRITING_LEVELS,
    HarnessError,
    read_json,
    sha256_file,
)

_LABEL = re.compile(r"^[a-z0-9][a-z0-9.-]{0,31}$")


@dataclass(frozen=True)
class Span:
    id: str
    start: int
    end: int
    span: str
    kind: str  # error_type for errors, protection kind for protected spans
    accepted: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewItem:
    id: str
    text: str
    errors: tuple[Span, ...]
    protected: tuple[Span, ...]


@dataclass(frozen=True)
class WritingTask:
    id: str
    level: str
    instruction: str
    min_words: int | None
    max_words: int | None


@dataclass(frozen=True)
class EvalSet:
    set_id: str
    sha256: str
    review: tuple[ReviewItem, ...]
    writing: tuple[WritingTask, ...]

    @property
    def error_count(self) -> int:
        return sum(len(item.errors) for item in self.review)

    @property
    def protected_count(self) -> int:
        return sum(len(item.protected) for item in self.review)

    def review_by_id(self) -> dict[str, ReviewItem]:
        return {item.id: item for item in self.review}

    def writing_by_id(self) -> dict[str, WritingTask]:
        return {task.id: task for task in self.writing}


@dataclass(frozen=True)
class Variant:
    label: str
    preamble: str | None
    sha256: str | None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HarnessError(message)


def _str(value: Any, where: str, *, allow_empty: bool = False) -> str:
    _require(isinstance(value, str) and (allow_empty or value.strip() != ""), f"{where}: expected a non-empty string")
    return value


def _offsets(raw: dict[str, Any], text: str, where: str) -> tuple[int, int, str]:
    start, end = raw.get("start"), raw.get("end")
    _require(
        isinstance(start, int) and isinstance(end, int) and not isinstance(start, bool) and not isinstance(end, bool),
        f"{where}: start/end must be integers",
    )
    _require(0 <= start <= end <= len(text), f"{where}: offsets {start}:{end} outside the paragraph")
    span = raw.get("span")
    _require(isinstance(span, str) and span == text[start:end], f"{where}: span does not equal text[{start}:{end}]")
    return start, end, span


def _overlap(a: Span, b: Span) -> bool:
    if a.start == a.end:
        return b.start < a.start < b.end or (b.start == b.end == a.start)
    if b.start == b.end:
        return a.start < b.start < a.end
    return a.start < b.end and b.start < a.end


def _review_item(raw: Any, index: int) -> ReviewItem:
    where = f"review[{index}]"
    _require(isinstance(raw, dict), f"{where}: expected an object")
    item_id = _str(raw.get("id"), f"{where}.id")
    text = _str(raw.get("text"), f"{where}.text")
    _require(unicodedata.normalize("NFC", text) == text, f"{where}: text must be NFC-normalised")
    errors: list[Span] = []
    for j, err in enumerate(raw.get("errors") or []):
        ew = f"{where}.errors[{j}]"
        _require(isinstance(err, dict), f"{ew}: expected an object")
        start, end, span = _offsets(err, text, ew)
        error_type = _str(err.get("error_type"), f"{ew}.error_type")
        _require(error_type in ERROR_TYPES, f"{ew}.error_type {error_type!r} is not one of {', '.join(ERROR_TYPES)}")
        accepted = err.get("accepted")
        _require(
            isinstance(accepted, list) and accepted and all(isinstance(a, str) for a in accepted),
            f"{ew}.accepted: expected a non-empty list of strings",
        )
        errors.append(Span(_str(err.get("id"), f"{ew}.id"), start, end, span, error_type, tuple(accepted)))
    protected: list[Span] = []
    for j, prot in enumerate(raw.get("protected") or []):
        pw = f"{where}.protected[{j}]"
        _require(isinstance(prot, dict), f"{pw}: expected an object")
        start, end, span = _offsets(prot, text, pw)
        _require(start < end, f"{pw}: protected spans must be non-empty")
        protected.append(Span(_str(prot.get("id"), f"{pw}.id"), start, end, span, _str(prot.get("kind"), f"{pw}.kind")))
    for err in errors:
        for prot in protected:
            _require(not _overlap(err, prot), f"{where}: error {err.id} overlaps protected span {prot.id}")
    return ReviewItem(item_id, text, tuple(errors), tuple(protected))


def _writing_task(raw: Any, index: int) -> WritingTask:
    where = f"writing[{index}]"
    _require(isinstance(raw, dict), f"{where}: expected an object")
    level = raw.get("level")
    _require(level in CEFR_LEVELS, f"{where}.level must be one of {', '.join(CEFR_LEVELS)}")
    bounds: list[int | None] = []
    for key in ("min_words", "max_words"):
        value = raw.get(key)
        _require(value is None or (isinstance(value, int) and value > 0), f"{where}.{key} must be a positive integer")
        bounds.append(value)
    return WritingTask(
        _str(raw.get("id"), f"{where}.id"), level, _str(raw.get("instruction"), f"{where}.instruction"), *bounds
    )


def load_set(path: Path) -> EvalSet:
    """Parse and validate the private set; any defect raises HarnessError."""
    try:
        raw = read_json(path)
    except (OSError, ValueError) as exc:
        raise HarnessError(f"cannot read evaluation set {path}: {exc}") from exc
    _require(isinstance(raw, dict), "evaluation set: expected a JSON object")
    review = tuple(_review_item(item, i) for i, item in enumerate(raw.get("review") or []))
    writing = tuple(_writing_task(task, i) for i, task in enumerate(raw.get("writing") or []))
    _require(bool(review or writing), "evaluation set: no review items and no writing tasks")
    ids = [item.id for item in review] + [task.id for task in writing]
    ids += [span.id for item in review for span in (*item.errors, *item.protected)]
    _require(len(ids) == len(set(ids)), "evaluation set: ids must be unique across items, errors and protected spans")
    return EvalSet(_str(raw.get("set_id"), "set_id"), sha256_file(path), review, writing)


def protocol_shortfalls(eval_set: EvalSet) -> list[str]:
    """Protocol v2 minimums that the set misses (empty when the set qualifies)."""
    problems: list[str] = []
    if eval_set.error_count < PROTOCOL_MIN_ERRORS:
        problems.append(f"{eval_set.error_count} seeded errors < {PROTOCOL_MIN_ERRORS}")
    if eval_set.protected_count < PROTOCOL_MIN_PROTECTED:
        problems.append(f"{eval_set.protected_count} protected spans < {PROTOCOL_MIN_PROTECTED}")
    levels = {task.level for task in eval_set.writing}
    missing = [level for level in PROTOCOL_WRITING_LEVELS if level not in levels]
    if missing:
        problems.append(f"writing levels missing: {', '.join(missing)}")
    return problems


def parse_variant(spec: str) -> Variant:
    """``none`` or ``LABEL=PATH``; the preamble is read once and hashed."""
    if spec == BASELINE_VARIANT:
        return Variant(BASELINE_VARIANT, None, None)
    label, sep, path_text = spec.partition("=")
    if not sep or not _LABEL.match(label) or label == BASELINE_VARIANT or not path_text:
        raise HarnessError(f"--variant {spec!r}: expected 'none' or LABEL=PATH (label: lowercase, digits, '.', '-')")
    path = Path(path_text).expanduser()
    try:
        data = path.read_bytes()
        text = data.decode("utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise HarnessError(f"--variant {label}: cannot read preamble {path}: {exc}") from exc
    if not text:
        raise HarnessError(f"--variant {label}: preamble file is empty")
    return Variant(label, text, sha256_file(path))


def parse_variants(specs: list[str]) -> list[Variant]:
    variants = [parse_variant(spec) for spec in specs]
    labels = [variant.label for variant in variants]
    if len(labels) != len(set(labels)):
        raise HarnessError("duplicate --variant labels")
    if BASELINE_VARIANT not in labels:
        raise HarnessError("the baseline variant 'none' is required for paired comparison")
    return variants
