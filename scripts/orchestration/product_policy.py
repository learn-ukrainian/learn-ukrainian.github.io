"""Versioned product policy for dispatch admission (#12680, machinery move step 2).

Machinery decides *how* to admit a dispatch; the product decides which seats and
which changed paths are curriculum business. Those product decisions live in one
data file, ``scripts/curriculum/admission_policy.v1.json``, and this module is the
only reader. It imports nothing from the product: the file is data, never code.

The file is trusted because of where it is read from, not because of what it says:
the default path is in the product checkout ``scripts.common.repo_root.product_root``
selects (C-4746): ``LU_PRODUCT_ROOT`` when the operator sets it, else the checkout
this package is in, so a dispatcher that runs the primary checkout's code
(``scripts/dispatcher/primary.py``) also reads the primary checkout's policy. No
command-line flag redirects it; the ``path`` argument exists for tests.

Fail closed. :func:`load_policy` raises :class:`ProductPolicyError` (a
``ValueError``, so admission callers that already refuse on an invalid threshold
refuse here too) when the file is:

- missing, a symlink, not a regular file, larger than :data:`MAX_POLICY_BYTES` or
  unreadable (``policy_missing``, ``policy_not_regular_file``, ``policy_too_large``,
  ``policy_unreadable``);
- not strict UTF-8 JSON, has a duplicate key or a non-finite number (``policy_not_json``);
- of another schema or schema version (``policy_schema_mismatch``,
  ``policy_version_incompatible``);
- copied or renamed from another origin: ``origin`` must name this file's
  repository path, and the file's own name must be that path's name
  (``policy_origin_mismatch``);
- missing a field, carrying an unknown one, or holding a malformed value
  (``policy_field_missing``, ``policy_field_unknown``, ``policy_field_invalid``);
- naming a seat or family outside the ASCII name grammar, or two entries that
  are lookalikes of each other (``policy_name_invalid``, ``policy_lookalike_entries``);
- altered or truncated after its digest was computed: ``content_sha256`` is the
  SHA-256 of the canonical JSON of every other field (``policy_digest_mismatch``).
  The digest proves completeness, not authorship; authorship is the reviewed
  commit that changed the file. ``python -m scripts.orchestration.product_policy
  --digest PATH`` prints the value to record after an edit;
- outside the v1 safety envelope (``policy_outside_v1_envelope``), even with a
  recomputed digest.

The v1 safety envelope is part of this interface's contract, not product data. A
v1 policy may tighten within it, but never loosen it:

- floors: every learner-payload pattern and every content agent type in the envelope
  stays listed (more may be added);
- ceilings: no Ukrainian content family and no Ukrainian review seat outside the
  envelope (fewer is allowed);
- receipts: for each author family, and for the default, the required reviewer
  families include at least those the envelope requires.

Loosening is an incompatible change: it needs schema v2 and a loader update here,
reviewed as a change to dispatch admission (#12680 F1, CTO decision option B).

The decisions on a loaded :class:`ProductPolicy` match names and paths exactly.
An input that is not exact but folds to a policy entry (case, Unicode lookalike
letters, dash or slash variants, padding) raises ``lookalike_seat_name`` or
``lookalike_learner_path`` instead of answering "not covered", and a changed path
that is not a canonical repository-relative path raises ``change_path_not_canonical``
(so does a bare string where a collection of paths belongs), and a bare string
where a collection of author families belongs raises ``decision_input_invalid``.
A rename is passed as an ``(origin, destination)`` pair and counts when either
side is a learner payload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from types import MappingProxyType
from typing import Any

from scripts.common.repo_root import ProductRootError, product_root

SCHEMA = "learn-ukrainian.product-admission-policy"
SCHEMA_VERSION = 1
POLICY_REL = "scripts/curriculum/admission_policy.v1.json"
MAX_POLICY_BYTES = 64 * 1024
DIGEST_FIELD = "content_sha256"

_TOP_FIELDS = frozenset({"schema", "schema_version", "origin", "seats", "receipts", DIGEST_FIELD})
_SEAT_FIELDS = frozenset({"content_agent_types", "ukrainian_content_families", "ukrainian_review_seats"})
_RECEIPT_FIELDS = frozenset({"learner_payload_paths", "review_receipts_by_author_family", "review_receipts_default"})
_REVIEW_SEAT_FIELDS = frozenset({"route", "family"})

_NAME_RE = re.compile(r"[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*\Z")
# A learner payload pattern: canonical repository-relative segments of ASCII
# letters, digits, ``.``, ``_``, ``-`` and ``*``; a directory prefix ends in ``/``.
_PATTERN_SEGMENT = r"[A-Za-z0-9_.*-]+"
_PATTERN_RE = re.compile(rf"{_PATTERN_SEGMENT}(?:/{_PATTERN_SEGMENT})*/?\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

# The v1 safety envelope (see the module docstring). Equal to the decisions in
# force when v1 was cut; changing any value here is a schema change.
_V1_LEARNER_PAYLOAD_FLOOR = frozenset({
    "curriculum/",
    "scripts/curriculum/",
    "scripts/data/stress_overrides.yaml",
    "scripts/verification/stress*",
    "scripts/pipeline/stress_annotator.py",
    "scripts/lexicon/",
    "site/src/lib/lexicon/",
    "scripts/review/prompts/",
    "scripts/build/phases/",
    "scripts/build/fresh/prompt*",
    "docs/epics/fresh-build-*",
    "schemas/activities-*",
})
_V1_CONTENT_AGENT_TYPE_FLOOR = frozenset({"curriculum-orchestrator"})
_V1_UKRAINIAN_CONTENT_FAMILY_CEILING = frozenset({"anthropic", "google", "openai"})
_V1_REVIEW_SEAT_CEILING = frozenset({("agy", "google"), ("codex", "openai")})
_V1_RECEIPTS_BY_AUTHOR_FLOOR: Mapping[str, frozenset[str]] = MappingProxyType({
    "google": frozenset({"openai"}),
    "openai": frozenset({"google"}),
})
_V1_RECEIPTS_DEFAULT_FLOOR = frozenset({"google", "openai"})

# Letters from other scripts that render like Latin ones, and dash and slash
# variants. Used only to *detect* a lookalike, never to accept one.
_CONFUSABLES = str.maketrans({
    "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t",
    "у": "y", "х": "x", "і": "i", "ї": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ɡ": "g", "ԛ": "q", "ԝ": "w",
    "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t",
    "υ": "u", "χ": "x", "ı": "i", "ℓ": "l", "0": "o", "1": "l",
    "_": "-", "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-", "﹣": "-",
    "∕": "/", "⁄": "/", "⧸": "/", "\\": "/",
})


class ProductPolicyError(ValueError):
    """The product policy or a decision input refused; ``code`` names the rule."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"product admission policy refused ({code}): {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ReviewSeat:
    route: str
    family: str


@dataclass(frozen=True)
class ProductPolicy:
    """A validated policy. Build one only through :func:`load_policy` or :func:`parse_policy`."""

    origin: str
    content_agent_types: frozenset[str]
    ukrainian_content_families: frozenset[str]
    ukrainian_review_seats: frozenset[ReviewSeat]
    learner_payload_paths: tuple[str, ...]
    review_receipts_by_author_family: Mapping[str, frozenset[str]]
    review_receipts_default: frozenset[str]

    # --- seat decisions -------------------------------------------------

    def is_content_seat(self, agent_type: str) -> bool:
        """True when this agent type is a curriculum (content) seat."""
        return _name_decision(agent_type, self.content_agent_types)

    def ukrainian_content_family_allowed(self, family: str) -> bool:
        """True when a model of this family may work on Ukrainian content."""
        return _name_decision(family, self.ukrainian_content_families)

    def is_ukrainian_review_seat(self, route: str, family: str) -> bool:
        """True when this (harness route, family) pair is a Ukrainian review seat."""
        routes = {seat.route for seat in self.ukrainian_review_seats}
        families = {seat.family for seat in self.ukrainian_review_seats}
        route_known = _name_decision(route, routes)
        family_known = _name_decision(family, families)
        return route_known and family_known and ReviewSeat(route, family) in self.ukrainian_review_seats

    # --- receipt decisions ----------------------------------------------

    def requires_ukrainian_review(self, changes: Iterable[str | tuple[str, str]]) -> bool:
        """True when any changed path, or either side of a rename, is a learner payload."""
        if isinstance(changes, (str, bytes)):
            raise ProductPolicyError("change_path_not_canonical", "pass a collection of paths, not one string")
        for change in changes:
            sides = change if isinstance(change, tuple) else (change,)
            if isinstance(change, tuple) and len(change) != 2:
                raise ProductPolicyError("change_path_not_canonical", f"a rename is (origin, destination), got {change!r}")
            for path in sides:
                if self._is_learner_payload(path):
                    return True
        return False

    def required_review_receipts(self, author_families: Iterable[str]) -> frozenset[str]:
        """The reviewer families whose receipts a Ukrainian head needs for these authors."""
        if isinstance(author_families, (str, bytes)):
            raise ProductPolicyError("decision_input_invalid", "pass a collection of author families, not one string")
        authors = frozenset(author_families)
        if len(authors) == 1:
            (author,) = authors
            known = set(self.review_receipts_by_author_family)
            if _name_decision(author, known):
                return self.review_receipts_by_author_family[author]
        return self.review_receipts_default

    def _is_learner_payload(self, path: Any) -> bool:
        _require_canonical_path(path)
        if any(_pattern_matches(pattern, path) for pattern in self.learner_payload_paths):
            return True
        folded = _skeleton(path)
        if any(_pattern_matches(_skeleton(pattern), folded) for pattern in self.learner_payload_paths):
            raise ProductPolicyError("lookalike_learner_path", f"{path!r} folds to a learner payload path")
        return False


def _skeleton(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text).casefold()
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return "".join(folded.translate(_CONFUSABLES).split())


def _name_decision(name: Any, known: Iterable[str]) -> bool:
    if not isinstance(name, str):
        raise ProductPolicyError("lookalike_seat_name", f"a seat name must be a string, got {type(name).__name__}")
    known = frozenset(known)
    if name in known:
        return True
    folded = _skeleton(name)
    if any(_skeleton(entry) == folded for entry in known):
        raise ProductPolicyError("lookalike_seat_name", f"{name!r} is a lookalike of a policy seat name")
    return False


def _pattern_matches(pattern: str, path: str) -> bool:
    return path == pattern or (pattern.endswith("/") and path.startswith(pattern)) or fnmatchcase(path, pattern)


def _require_canonical_path(path: Any) -> None:
    if not isinstance(path, str) or not path:
        raise ProductPolicyError("change_path_not_canonical", f"a changed path must be a non-empty string, got {path!r}")
    if (
        path.startswith("/")
        or path != path.strip()
        or "\\" in path
        or any(unicodedata.category(ch).startswith(("C", "Z")) and ch != " " for ch in path)
        or any(part in ("", ".", "..") for part in path.split("/"))
        or unicodedata.normalize("NFC", path) != path
    ):
        raise ProductPolicyError("change_path_not_canonical", f"{path!r} is not a canonical repository-relative path")


# --- loading -------------------------------------------------------------


def canonical_digest(document: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON of every field except ``content_sha256``."""
    body = {key: value for key, value in document.items() if key != DIGEST_FIELD}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _read_bytes(path: Path) -> bytes:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        raise ProductPolicyError("policy_missing", f"no product policy at {path}") from None
    except OSError as exc:
        raise ProductPolicyError("policy_unreadable", f"{path}: {exc.strerror}") from None
    if not stat.S_ISREG(info.st_mode):
        raise ProductPolicyError("policy_not_regular_file", f"{path} is not a regular file (symlinks are refused)")
    if info.st_size > MAX_POLICY_BYTES:
        raise ProductPolicyError("policy_too_large", f"{path} is {info.st_size} bytes (limit {MAX_POLICY_BYTES})")
    # O_NONBLOCK: a FIFO or device swapped in after the lstat opens at once instead of
    # blocking (and holding the admission lock); the fstat below then refuses it.
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProductPolicyError("policy_unreadable", f"{path}: {exc.strerror}") from None
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise ProductPolicyError("policy_not_regular_file", f"{path} changed while it was opened")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            data = handle.read(MAX_POLICY_BYTES + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(data) > MAX_POLICY_BYTES:
        raise ProductPolicyError("policy_too_large", f"{path} grew past {MAX_POLICY_BYTES} bytes")
    return data


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProductPolicyError("policy_not_json", f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise ProductPolicyError("policy_not_json", f"non-finite number {token}")


def _decode(data: bytes, path: Path) -> Any:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ProductPolicyError("policy_not_json", f"{path} is not UTF-8") from None
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ProductPolicyError("policy_not_json", f"{path}: {exc.msg} at line {exc.lineno}") from None


def _fields(value: Any, expected: frozenset[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ProductPolicyError("policy_field_invalid", f"{where} must be an object")
    missing = sorted(expected - value.keys())
    if missing:
        raise ProductPolicyError("policy_field_missing", f"{where} lacks {', '.join(missing)}")
    unknown = sorted(value.keys() - expected)
    if unknown:
        raise ProductPolicyError("policy_field_unknown", f"{where} has unknown {', '.join(unknown)}")
    return value


def _names(value: Any, where: str, *, allow_empty: bool = False) -> frozenset[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ProductPolicyError("policy_field_invalid", f"{where} must be a non-empty list of names")
    for name in value:
        if not isinstance(name, str) or not _NAME_RE.match(name):
            raise ProductPolicyError("policy_name_invalid", f"{where} entry {name!r} is not an ASCII lowercase name")
    _unique_skeletons(value, where)
    return frozenset(value)


def _unique_skeletons(entries: list[str], where: str) -> None:
    seen: dict[str, str] = {}
    for entry in entries:
        folded = _skeleton(entry)
        if folded in seen:
            raise ProductPolicyError(
                "policy_lookalike_entries", f"{where} entries {seen[folded]!r} and {entry!r} are lookalikes or duplicates"
            )
        seen[folded] = entry


def _require_v1_envelope(
    *,
    patterns: frozenset[str],
    content_agent_types: frozenset[str],
    content_families: frozenset[str],
    review_seats: frozenset[tuple[str, str]],
    by_author: Mapping[str, frozenset[str]],
    default: frozenset[str],
) -> None:
    """Refuse a v1 policy that loosens the v1 safety envelope (it may only tighten)."""
    loosened: list[str] = []
    if missing := sorted(_V1_LEARNER_PAYLOAD_FLOOR - patterns):
        loosened.append(f"learner_payload_paths drops {', '.join(missing)}")
    if missing := sorted(_V1_CONTENT_AGENT_TYPE_FLOOR - content_agent_types):
        loosened.append(f"content_agent_types drops {', '.join(missing)}")
    if extra := sorted(content_families - _V1_UKRAINIAN_CONTENT_FAMILY_CEILING):
        loosened.append(f"ukrainian_content_families adds {', '.join(extra)}")
    if extra_seats := sorted(review_seats - _V1_REVIEW_SEAT_CEILING):
        loosened.append(f"ukrainian_review_seats adds {', '.join(f'{r}/{f}' for r, f in extra_seats)}")
    for author in sorted(set(by_author) | set(_V1_RECEIPTS_BY_AUTHOR_FLOOR)):
        required = by_author.get(author, default)
        floor = _V1_RECEIPTS_BY_AUTHOR_FLOOR.get(author, _V1_RECEIPTS_DEFAULT_FLOOR)
        if missing := sorted(floor - required):
            loosened.append(f"receipts for author {author} drop {', '.join(missing)}")
    if missing := sorted(_V1_RECEIPTS_DEFAULT_FLOOR - default):
        loosened.append(f"review_receipts_default drops {', '.join(missing)}")
    if loosened:
        raise ProductPolicyError(
            "policy_outside_v1_envelope",
            "; ".join(loosened) + " (loosening needs schema v2 and a loader update)",
        )


def parse_policy(document: Any, *, file_name: str | None = None) -> ProductPolicy:
    """Validate a decoded policy document. ``file_name`` is the name the file was read under."""
    top = _fields(document, _TOP_FIELDS, "policy")
    if top["schema"] != SCHEMA:
        raise ProductPolicyError("policy_schema_mismatch", f"schema {top['schema']!r} is not {SCHEMA!r}")
    version = top["schema_version"]
    if type(version) is not int or version != SCHEMA_VERSION:
        raise ProductPolicyError(
            "policy_version_incompatible", f"schema_version {version!r} is not {SCHEMA_VERSION} (this loader reads v1 only)"
        )
    if top["origin"] != POLICY_REL:
        raise ProductPolicyError("policy_origin_mismatch", f"origin {top['origin']!r} is not {POLICY_REL!r}")
    if file_name is not None and file_name != POLICY_REL.rsplit("/", 1)[-1]:
        raise ProductPolicyError("policy_origin_mismatch", f"file name {file_name!r} does not match origin {POLICY_REL!r}")
    digest = top[DIGEST_FIELD]
    if not isinstance(digest, str) or not _SHA256_RE.match(digest):
        raise ProductPolicyError("policy_field_invalid", f"{DIGEST_FIELD} must be 64 lowercase hex digits")
    try:
        actual = canonical_digest(top)
    except (TypeError, ValueError) as exc:
        raise ProductPolicyError("policy_field_invalid", f"policy is not canonical JSON data: {exc}") from None
    if actual != digest:
        raise ProductPolicyError("policy_digest_mismatch", "content does not match content_sha256 (altered or truncated)")

    seats = _fields(top["seats"], _SEAT_FIELDS, "seats")
    content_agent_types = _names(seats["content_agent_types"], "seats.content_agent_types")
    content_families = _names(seats["ukrainian_content_families"], "seats.ukrainian_content_families")
    raw_seats = seats["ukrainian_review_seats"]
    if not isinstance(raw_seats, list) or not raw_seats:
        raise ProductPolicyError("policy_field_invalid", "seats.ukrainian_review_seats must be a non-empty list")
    review_seats: list[ReviewSeat] = []
    for index, raw in enumerate(raw_seats):
        entry = _fields(raw, _REVIEW_SEAT_FIELDS, f"seats.ukrainian_review_seats[{index}]")
        route = next(iter(_names([entry["route"]], f"seats.ukrainian_review_seats[{index}].route")))
        family = next(iter(_names([entry["family"]], f"seats.ukrainian_review_seats[{index}].family")))
        review_seats.append(ReviewSeat(route, family))
    _unique_skeletons([seat.route for seat in review_seats], "seats.ukrainian_review_seats routes")
    seat_families = {seat.family for seat in review_seats}
    if not seat_families <= content_families:
        raise ProductPolicyError(
            "policy_field_invalid", "every Ukrainian review seat family must be a Ukrainian content family"
        )

    receipts = _fields(top["receipts"], _RECEIPT_FIELDS, "receipts")
    patterns = receipts["learner_payload_paths"]
    if not isinstance(patterns, list) or not patterns:
        raise ProductPolicyError("policy_field_invalid", "receipts.learner_payload_paths must be a non-empty list")
    for pattern in patterns:
        if not isinstance(pattern, str) or not _PATTERN_RE.match(pattern) or any(
            part in (".", "..") for part in pattern.rstrip("/").split("/")
        ):
            raise ProductPolicyError("policy_field_invalid", f"learner payload path {pattern!r} is not canonical")
    _unique_skeletons(patterns, "receipts.learner_payload_paths")
    by_author_raw = receipts["review_receipts_by_author_family"]
    if not isinstance(by_author_raw, dict):
        raise ProductPolicyError("policy_field_invalid", "receipts.review_receipts_by_author_family must be an object")
    _names(list(by_author_raw), "receipts.review_receipts_by_author_family keys", allow_empty=True)
    by_author: dict[str, frozenset[str]] = {}
    for author, required in by_author_raw.items():
        names = _names(required, f"receipts.review_receipts_by_author_family.{author}")
        if not names <= seat_families:
            raise ProductPolicyError("policy_field_invalid", f"receipts for author {author!r} name a non-seat family")
        by_author[author] = names
    default = _names(receipts["review_receipts_default"], "receipts.review_receipts_default")
    if not default <= seat_families:
        raise ProductPolicyError("policy_field_invalid", "receipts.review_receipts_default names a non-seat family")
    _require_v1_envelope(
        patterns=frozenset(patterns),
        content_agent_types=content_agent_types,
        content_families=content_families,
        review_seats=frozenset((seat.route, seat.family) for seat in review_seats),
        by_author=by_author,
        default=default,
    )

    return ProductPolicy(
        origin=top["origin"],
        content_agent_types=content_agent_types,
        ukrainian_content_families=content_families,
        ukrainian_review_seats=frozenset(review_seats),
        learner_payload_paths=tuple(patterns),
        review_receipts_by_author_family=MappingProxyType(by_author),
        review_receipts_default=default,
    )


def default_policy_path() -> Path:
    """:data:`POLICY_REL` in the selected product checkout; refuse (``policy_missing``) without one."""
    try:
        return product_root() / POLICY_REL
    except ProductRootError as exc:
        raise ProductPolicyError("policy_missing", str(exc)) from None


def load_policy(path: Path | None = None) -> ProductPolicy:
    """Read and validate the product policy, or raise :class:`ProductPolicyError`."""
    target = default_policy_path() if path is None else Path(path)
    return parse_policy(_decode(_read_bytes(target), target), file_name=target.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the product admission policy, or print the content_sha256 to record after an edit.",
        epilog="Exit codes: 0 valid (or digest printed), 2 usage error, 3 policy refused.",
    )
    parser.add_argument("path", nargs="?", type=Path, default=None, help=f"policy file (default: {POLICY_REL} in the product checkout)")
    parser.add_argument("--digest", action="store_true", help="print the canonical content_sha256 without validating it")
    args = parser.parse_args(argv)
    try:
        if args.path is None:
            args.path = default_policy_path()
        if args.digest:
            document = _decode(_read_bytes(args.path), args.path)
            if not isinstance(document, dict):
                raise ProductPolicyError("policy_field_invalid", "policy must be an object")
            print(canonical_digest(document))
            return 0
        policy = load_policy(args.path)
    except ProductPolicyError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except (TypeError, ValueError) as exc:
        print(f"product admission policy refused (policy_field_invalid): {exc}", file=sys.stderr)
        return 3
    print(f"valid: {policy.origin} schema v{SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "POLICY_REL",
    "SCHEMA",
    "SCHEMA_VERSION",
    "ProductPolicy",
    "ProductPolicyError",
    "ReviewSeat",
    "canonical_digest",
    "default_policy_path",
    "load_policy",
    "parse_policy",
]
