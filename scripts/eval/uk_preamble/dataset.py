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
``span`` must equal ``text[start:end]``. An empty error span marks an insertion
point (e.g. a missing comma). Spans start and end on scoring-token boundaries
(``common.tokenize``) and hold at least one token unless empty; seeded errors
never overlap each other or a protected span; no accepted form tokenises to its
error's own tokens (see ``review_geometry``).
"""

from __future__ import annotations

import bisect
import functools
import itertools
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
    Token,
    read_json,
    sha256_file,
    sha256_text,
    token_keys,
    tokenize,
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
    sha256: str | None  # of ``preamble``, the exact text placed in the prompt


class SetError(HarnessError):
    """A set defect; ``rule`` names the violated rule and never carries set text (reports print it)."""

    def __init__(self, message: str, rule: str) -> None:
        super().__init__(message)
        self.rule = rule


@dataclass(frozen=True)
class SetProblem:
    item: str | None  # item id; None for a defect of the set as a whole
    rule: str


def _require(condition: bool, message: str, rule: str) -> None:
    if not condition:
        raise SetError(message, rule)


def _str(value: Any, where: str, rule: str, *, allow_empty: bool = False) -> str:
    _require(
        isinstance(value, str) and (allow_empty or value.strip() != ""), f"{where}: expected a non-empty string", rule
    )
    return value


def _offsets(raw: dict[str, Any], text: str, where: str) -> tuple[int, int, str]:
    start, end = raw.get("start"), raw.get("end")
    _require(
        isinstance(start, int) and isinstance(end, int) and not isinstance(start, bool) and not isinstance(end, bool),
        f"{where}: start/end must be integers",
        "offsets-not-integers",
    )
    _require(
        0 <= start <= end <= len(text), f"{where}: offsets {start}:{end} outside the paragraph", "offsets-out-of-range"
    )
    span = raw.get("span")
    _require(
        isinstance(span, str) and span == text[start:end],
        f"{where}: span does not equal text[{start}:{end}]",
        "span-text-mismatch",
    )
    return start, end, span


def _overlap(a: Span, b: Span) -> bool:
    if a.start == a.end:
        return b.start < a.start < b.end or (b.start == b.end == a.start)
    if b.start == b.end:
        return a.start < b.start < a.end
    return a.start < b.end and b.start < a.end


@dataclass(frozen=True)
class TokenSpan:
    """A span over source tokens [i1, i2); an empty one (i1 == i2) is the boundary before token i1."""

    span: Span
    i1: int
    i2: int


@dataclass(frozen=True)
class Geometry:
    """A review paragraph in scoring tokens: its spans, accepted forms and clusters of adjacent seeds."""

    tokens: tuple[Token, ...]
    seeds: tuple[TokenSpan, ...]  # sorted by (i1, i2)
    protected: tuple[TokenSpan, ...]
    accepted: dict[str, tuple[tuple[str, ...], ...]]  # seed id -> accepted forms as token keys
    clusters: tuple[tuple[TokenSpan, ...], ...]  # maximal runs of seeds with no correct token between them

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(token.key for token in self.tokens)


def _token_span(tokens: tuple[Token, ...], span: Span, where: str) -> TokenSpan:
    for pos in sorted({span.start, span.end}):
        inside = next((t for t in tokens if t.start < pos < t.end), None)
        if inside is not None:
            raise SetError(
                f"{where}: span {span.id} does not start and end on token boundaries "
                f"(offset {pos} falls inside {inside.key!r})",
                "span-not-on-token-boundary",
            )
    starts = [t.start for t in tokens]
    i1 = bisect.bisect_left(starts, span.start)
    i2 = bisect.bisect_left(starts, span.end) if span.end > span.start else i1
    _require(
        span.start == span.end or i2 > i1,
        f"{where}: span {span.id} contains no token (whitespace only)",
        "span-holds-no-token",
    )
    return TokenSpan(span, i1, i2)


def _token_overlap(a: TokenSpan, b: TokenSpan) -> bool:
    if a.i1 == a.i2 and b.i1 == b.i2:
        return a.i1 == b.i1
    if a.i1 == a.i2:
        return b.i1 < a.i1 < b.i2
    if b.i1 == b.i2:
        return a.i1 < b.i1 < a.i2
    return a.i1 < b.i2 and b.i1 < a.i2


@functools.lru_cache(maxsize=4096)
def review_geometry(item: ReviewItem, where: str | None = None) -> Geometry:
    """Validate ``item`` against the scoring contract and return its token geometry.

    Refused (HarnessError): a seed or protected span that does not start and end
    on token boundaries or holds no token; seeds overlapping each other or a
    protected span; an accepted form that tokenises to the seed's own tokens.
    """
    where = where or f"review item {item.id}"
    tokens = tuple(tokenize(item.text))
    keys = tuple(token.key for token in tokens)
    seeds = sorted((_token_span(tokens, err, where) for err in item.errors), key=lambda s: (s.i1, s.i2, s.span.start))
    protected = tuple(_token_span(tokens, prot, where) for prot in item.protected)
    for a, b in itertools.combinations(seeds, 2):
        _require(
            not _overlap(a.span, b.span) and not _token_overlap(a, b),
            f"{where}: seeds {a.span.id} and {b.span.id} overlap",
            "seeds-overlap",
        )
    for seed in seeds:
        for prot in protected:
            _require(
                not _overlap(seed.span, prot.span) and not _token_overlap(seed, prot),
                f"{where}: error {seed.span.id} overlaps protected span {prot.span.id}",
                "error-overlaps-protected",
            )
    accepted: dict[str, tuple[tuple[str, ...], ...]] = {}
    for seed in seeds:
        forms = tuple(dict.fromkeys(token_keys(form) for form in seed.span.accepted))
        own = keys[seed.i1 : seed.i2]
        _require(
            own not in forms,
            f"{where}: an accepted form of {seed.span.id} tokenises to the seed's own tokens {list(own)}",
            "accepted-form-equals-seed",
        )
        accepted[seed.span.id] = forms
    clusters: list[list[TokenSpan]] = []
    for seed in seeds:
        if clusters and seed.i1 <= max(s.i2 for s in clusters[-1]):
            clusters[-1].append(seed)
        else:
            clusters.append([seed])
    return Geometry(tokens, tuple(seeds), protected, accepted, tuple(tuple(c) for c in clusters))


def _review_item(raw: Any, index: int) -> ReviewItem:
    where = f"review[{index}]"
    _require(isinstance(raw, dict), f"{where}: expected an object", "item-not-object")
    item_id = _str(raw.get("id"), f"{where}.id", "item-id")
    text = _str(raw.get("text"), f"{where}.text", "item-text")
    _require(unicodedata.normalize("NFC", text) == text, f"{where}: text must be NFC-normalised", "text-not-nfc")
    errors: list[Span] = []
    for j, err in enumerate(raw.get("errors") or []):
        ew = f"{where}.errors[{j}]"
        _require(isinstance(err, dict), f"{ew}: expected an object", "error-not-object")
        start, end, span = _offsets(err, text, ew)
        error_type = _str(err.get("error_type"), f"{ew}.error_type", "error-type")
        _require(
            error_type in ERROR_TYPES,
            f"{ew}.error_type {error_type!r} is not one of {', '.join(ERROR_TYPES)}",
            "error-type-unknown",
        )
        accepted = err.get("accepted")
        _require(
            isinstance(accepted, list) and accepted and all(isinstance(a, str) for a in accepted),
            f"{ew}.accepted: expected a non-empty list of strings",
            "accepted-forms",
        )
        errors.append(Span(_str(err.get("id"), f"{ew}.id", "error-id"), start, end, span, error_type, tuple(accepted)))
    protected: list[Span] = []
    for j, prot in enumerate(raw.get("protected") or []):
        pw = f"{where}.protected[{j}]"
        _require(isinstance(prot, dict), f"{pw}: expected an object", "protected-not-object")
        start, end, span = _offsets(prot, text, pw)
        _require(start < end, f"{pw}: protected spans must be non-empty", "protected-empty")
        protected.append(
            Span(
                _str(prot.get("id"), f"{pw}.id", "protected-id"),
                start,
                end,
                span,
                _str(prot.get("kind"), f"{pw}.kind", "protected-kind"),
            )
        )
    item = ReviewItem(item_id, text, tuple(errors), tuple(protected))
    review_geometry(item, where)
    return item


def _writing_task(raw: Any, index: int) -> WritingTask:
    where = f"writing[{index}]"
    _require(isinstance(raw, dict), f"{where}: expected an object", "item-not-object")
    level = raw.get("level")
    _require(level in CEFR_LEVELS, f"{where}.level must be one of {', '.join(CEFR_LEVELS)}", "writing-level")
    bounds: list[int | None] = []
    for key in ("min_words", "max_words"):
        value = raw.get(key)
        _require(
            value is None or (isinstance(value, int) and value > 0),
            f"{where}.{key} must be a positive integer",
            "writing-word-bound",
        )
        bounds.append(value)
    return WritingTask(
        _str(raw.get("id"), f"{where}.id", "item-id"),
        level,
        _str(raw.get("instruction"), f"{where}.instruction", "writing-instruction"),
        *bounds,
    )


def _item_id(raw: Any) -> str | None:
    value = raw.get("id") if isinstance(raw, dict) else None
    return value if isinstance(value, str) else None


def set_problems(raw: Any) -> list[SetProblem]:
    """Every defect ``load_set`` would refuse, one per item (its first), by item id and rule; no set text.

    Runs the loader's own per-item validation (including ``review_geometry``) and its set-level
    checks, but collects instead of stopping at the first defect. The Protocol v2 minimums are
    separate (``protocol_shortfalls``).
    """
    if not isinstance(raw, dict):
        return [SetProblem(None, "set-not-object")]
    problems: list[SetProblem] = []
    ids: list[str] = []
    for key, build in (("review", _review_item), ("writing", _writing_task)):
        for index, item in enumerate(raw.get(key) or []):
            try:
                built = build(item, index)
            except SetError as exc:
                problems.append(SetProblem(_item_id(item), exc.rule))
                continue
            ids.append(built.id)
            if isinstance(built, ReviewItem):
                ids += [span.id for span in (*built.errors, *built.protected)]
    if not (raw.get("review") or raw.get("writing")):
        problems.append(SetProblem(None, "set-empty"))
    problems += [SetProblem(dup, "duplicate-id") for dup in sorted({i for i in ids if ids.count(i) > 1})]
    if not isinstance(raw.get("set_id"), str) or not raw["set_id"].strip():
        problems.append(SetProblem(None, "set-id"))
    return problems


def load_set(path: Path) -> EvalSet:
    """Parse and validate the private set; any defect raises HarnessError."""
    try:
        raw = read_json(path)
    except (OSError, ValueError) as exc:
        raise HarnessError(f"cannot read evaluation set {path}: {exc}") from exc
    _require(isinstance(raw, dict), "evaluation set: expected a JSON object", "set-not-object")
    review = tuple(_review_item(item, i) for i, item in enumerate(raw.get("review") or []))
    writing = tuple(_writing_task(task, i) for i, task in enumerate(raw.get("writing") or []))
    _require(bool(review or writing), "evaluation set: no review items and no writing tasks", "set-empty")
    ids = [item.id for item in review] + [task.id for task in writing]
    ids += [span.id for item in review for span in (*item.errors, *item.protected)]
    _require(
        len(ids) == len(set(ids)),
        "evaluation set: ids must be unique across items, errors and protected spans",
        "duplicate-id",
    )
    return EvalSet(_str(raw.get("set_id"), "set_id", "set-id"), sha256_file(path), review, writing)


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
    """``none`` or ``LABEL=PATH``; the preamble is read once and its prompt text hashed."""
    if spec == BASELINE_VARIANT:
        return Variant(BASELINE_VARIANT, None, None)
    label, sep, path_text = spec.partition("=")
    if not sep or not _LABEL.match(label) or label == BASELINE_VARIANT or not path_text:
        raise HarnessError(f"--variant {spec!r}: expected 'none' or LABEL=PATH (label: lowercase, digits, '.', '-')")
    path = Path(path_text).expanduser()
    try:
        text = path.read_bytes().decode("utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise HarnessError(f"--variant {label}: cannot read preamble {path}: {exc}") from exc
    if not text:
        raise HarnessError(f"--variant {label}: preamble file is empty")
    return Variant(label, text, sha256_text(text))


def parse_variants(specs: list[str]) -> list[Variant]:
    variants = [parse_variant(spec) for spec in specs]
    labels = [variant.label for variant in variants]
    if len(labels) != len(set(labels)):
        raise HarnessError("duplicate --variant labels")
    if BASELINE_VARIANT not in labels:
        raise HarnessError("the baseline variant 'none' is required for paired comparison")
    return variants
