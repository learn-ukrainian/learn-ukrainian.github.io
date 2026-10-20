"""Pair v0.1.0-pilot word cards to current atlas0 identities (#8981, #11023).

Use this to write or check the canonical pairing artifact. Do not use it to
certify Ukrainian, edit the published release, or change Atlas pages.

An active registry entry matches when its source key is ``atlas0:slug:<slug>``
and ``key_at_creation.spelling`` equals the card's spelling assertion exactly.
Capitalization is significant. One atlas entry pairs. Several atlas entries
narrow by a single part-of-speech value. A spelling claimed by more than one
release card stays unresolved. Zero atlas entries, including a card with no
spelling assertion, stay unpaired. The tool never opens ``sources.db``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.common.jsonl import jsonl_lines
from scripts.common.repo_root import main_checkout_root

ROOT = Path(__file__).resolve().parents[3]
RELEASE_VERSION = "v0.1.0-pilot"
SCHEMA_VERSION = "1"
ATLAS_SOURCE = "atlas0"
ATLAS_PREFIX = "atlas0:slug:"
# Published word-cards-v0.1 asset. Recorded for callers; inputs are hashed as read.
PUBLISHED_CARDS_SHA256 = "45bd9c9325a3b4221c86d1663d784e96a7edc096674415445d37113f793189e6"
DEFAULT_CARDS = Path("data/datasets/word-cards/releases/v0.1.0-pilot/word-cards.jsonl")
DEFAULT_REGISTRY = Path("registry/atlas/identity/registry.json")
DEFAULT_OUTPUT = Path("data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json")
CARD_ID_PATTERN = r"^wc_[0-9a-hjkmnp-tv-z]{12}$"
UNPAIRED_REASON = "new_candidate_no_current_atlas_entry"
HOMONYM_REASON = "homonym_unresolved"
CONFLICTING_SPELLING = "conflicting_spelling_assertions"

PAIRING_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version", "release_version", "cards_sha256", "registry_version",
        "total_cards", "paired_count", "unpaired_count", "ambiguous_count", "entries",
    ],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "release_version": {"const": RELEASE_VERSION},
        "cards_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "registry_version": {"type": "integer", "minimum": 1},
        "total_cards": {"type": "integer", "minimum": 0},
        "paired_count": {"type": "integer", "minimum": 0},
        "unpaired_count": {"type": "integer", "minimum": 0},
        "ambiguous_count": {"type": "integer", "minimum": 0},
        "entries": {"type": "array"},
    },
}
_ENTRY_SCHEMA: dict = {
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["card_id", "spelling", "status", "atlas0_slug", "pilot_card_id"],
            "properties": {
                "card_id": {"type": "string", "pattern": CARD_ID_PATTERN},
                "spelling": {"type": "string", "minLength": 1},
                "status": {"const": "paired"},
                "atlas0_slug": {"type": "string", "pattern": r"^atlas0:slug:\S+$"},
                "pilot_card_id": {"type": "string", "pattern": CARD_ID_PATTERN},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["card_id", "spelling", "status", "reason"],
            "properties": {
                "card_id": {"type": "string", "pattern": CARD_ID_PATTERN},
                "spelling": {"type": ["string", "null"], "minLength": 1},
                "status": {"const": "unpaired"},
                "reason": {"const": UNPAIRED_REASON},
            },
        },
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["card_id", "spelling", "status", "reason", "candidate_atlas0_slugs"],
            "properties": {
                "card_id": {"type": "string", "pattern": CARD_ID_PATTERN},
                "spelling": {"type": ["string", "null"], "minLength": 1},
                "status": {"const": "ambiguous"},
                "reason": {"enum": [HOMONYM_REASON, CONFLICTING_SPELLING]},
                "candidate_atlas0_slugs": {
                    "type": "array",
                    "items": {"type": "string", "pattern": r"^atlas0:slug:\S+$"},
                    "uniqueItems": True,
                },
            },
        },
    ]
}
_VALIDATOR = Draft202012Validator(PAIRING_SCHEMA)
_ENTRY_VALIDATOR = Draft202012Validator(_ENTRY_SCHEMA)


class PairingError(ValueError):
    """The cards, registry, or output path cannot produce a pairing artifact."""


@dataclass(frozen=True)
class AtlasIdentity:
    """One active atlas0 identity used for exact spelling match."""

    card_id: str
    spelling: str
    pos: str
    slug: str


def canonical_bytes(document: dict) -> bytes:
    """UTF-8 JSON with stable key order and a trailing newline."""
    return (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_bytes(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise PairingError(f"{label} must be a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PairingError(f"cannot read {label}: {path}") from exc


def resolve_cards_path(path: Path) -> Path:
    """Find the cards file in this checkout, then in the primary checkout.

    The published JSONL is gitignored. Dispatch worktrees read the primary
    copy and never write it.
    """
    if path.is_absolute():
        if not path.is_file():
            raise PairingError(f"cards file not found: {path}")
        return path
    local = ROOT / path
    if local.is_file():
        return local
    primary = main_checkout_root(ROOT) / path
    if primary.is_file():
        return primary
    raise PairingError(
        f"cards file not found at {local}. The v0.1.0-pilot release is gitignored; pass --cards.")


def _output_target(path: Path) -> Path:
    target = path if path.is_absolute() else ROOT / path
    primary = main_checkout_root(ROOT).resolve()
    root = ROOT.resolve()
    resolved = target.resolve()
    if primary != root and resolved.is_relative_to(primary) and not resolved.is_relative_to(root):
        raise PairingError("refusing to write the pairing artifact into the primary checkout")
    if resolved.name == "sources.db":
        raise PairingError("refusing to write sources.db")
    return target


def _json_object(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise PairingError(f"{label} must be a JSON object")
    return value


def _card_id(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"wc_[0-9a-hjkmnp-tv-z]{12}", value) is None:
        raise PairingError(f"{label} card_id is not a word-card id")
    return value


def _field_strings(card: dict, field_name: str) -> list[str]:
    found: list[str] = []
    fields = card.get("fields")
    if not isinstance(fields, list):
        raise PairingError(f"{card.get('card_id')} fields must be an array")
    for field in fields:
        item = _json_object(field, "field")
        if item.get("field") != field_name:
            continue
        value = item.get("value")
        if not isinstance(value, str) or not value:
            raise PairingError(f"{card.get('card_id')} {field_name} must be a nonempty string")
        if value not in found:
            found.append(value)
    return found


def load_cards(path: Path) -> tuple[list[dict], str]:
    """Return release cards in file order and the SHA-256 of the file bytes."""
    raw = _read_bytes(path, "cards")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise PairingError(f"cards file is not UTF-8: {path}") from exc
    cards: list[dict] = []
    seen: set[str] = set()
    for line in jsonl_lines(text):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PairingError(f"cards line is not JSON: {exc}") from exc
        card = _json_object(value, "card")
        card_id = _card_id(card.get("card_id"), "card")
        if card_id in seen:
            raise PairingError(f"duplicate card_id: {card_id}")
        seen.add(card_id)
        cards.append(card)
    if not cards:
        raise PairingError("cards file has no cards")
    return cards, _sha256(raw)


def _atlas_slug(key: object) -> str:
    if not isinstance(key, str) or not key.startswith(ATLAS_PREFIX):
        raise PairingError(f"atlas0 key must use {ATLAS_PREFIX}<slug>")
    slug = key[len(ATLAS_PREFIX):]
    if not slug or any(character.isspace() for character in slug):
        raise PairingError(f"atlas0 slug is empty or contains whitespace: {key}")
    return key


def load_atlas_identities(path: Path) -> tuple[int, tuple[AtlasIdentity, ...]]:
    """Return the registry version and active atlas0 identities."""
    try:
        document = json.loads(_read_bytes(path, "registry"))
    except json.JSONDecodeError as exc:
        raise PairingError(f"registry is not JSON: {exc}") from exc
    registry = _json_object(document, "registry")
    version = registry.get("registry_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise PairingError("registry_version must be a positive integer")
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise PairingError("registry entries must be an array")
    identities: list[AtlasIdentity] = []
    seen_slugs: set[str] = set()
    seen_ids: set[str] = set()
    for entry in entries:
        item = _json_object(entry, "registry entry")
        created = _json_object(item.get("key_at_creation"), "key_at_creation")
        keys = created.get("source_keys")
        if not isinstance(keys, list):
            raise PairingError("source_keys must be an array")
        atlas_keys = []
        for key in keys:
            record = _json_object(key, "source key")
            if record.get("source_id") != ATLAS_SOURCE:
                continue
            atlas_keys.append(_atlas_slug(record.get("key")))
        if not atlas_keys:
            continue
        if len(atlas_keys) != 1:
            raise PairingError(f"{item.get('card_id')} has more than one atlas0 key")
        if item.get("state") != "active":
            continue
        slug = atlas_keys[0]
        card_id = _card_id(item.get("card_id"), "registry entry")
        spelling = created.get("spelling")
        pos = created.get("pos")
        if not isinstance(spelling, str) or not spelling:
            raise PairingError(f"{card_id} atlas spelling must be a nonempty string")
        if not isinstance(pos, str) or not pos:
            raise PairingError(f"{card_id} atlas pos must be a nonempty string")
        if slug in seen_slugs:
            raise PairingError(f"duplicate atlas0 key: {slug}")
        if card_id in seen_ids:
            raise PairingError(f"duplicate atlas card_id: {card_id}")
        seen_slugs.add(slug)
        seen_ids.add(card_id)
        identities.append(AtlasIdentity(card_id=card_id, spelling=spelling, pos=pos, slug=slug))
    identities.sort(key=lambda item: (item.spelling, item.slug, item.card_id))
    return version, tuple(identities)


def _candidates(matches: tuple[AtlasIdentity, ...] | list[AtlasIdentity]) -> list[str]:
    return sorted({item.slug for item in matches})


def _pair_card(card: dict, by_spelling: dict[str, tuple[AtlasIdentity, ...]]) -> dict:
    card_id = _card_id(card.get("card_id"), "card")
    spellings = _field_strings(card, "spelling")
    if len(spellings) > 1:
        return {
            "card_id": card_id,
            "spelling": None,
            "status": "ambiguous",
            "reason": CONFLICTING_SPELLING,
            "candidate_atlas0_slugs": [],
        }
    if not spellings:
        return {"card_id": card_id, "spelling": None, "status": "unpaired", "reason": UNPAIRED_REASON}
    spelling = spellings[0]
    matches = by_spelling.get(spelling, ())
    if not matches:
        return {"card_id": card_id, "spelling": spelling, "status": "unpaired", "reason": UNPAIRED_REASON}
    chosen = matches
    if len(matches) > 1:
        positions = _field_strings(card, "pos")
        chosen = tuple(item for item in matches if item.pos == positions[0]) if len(positions) == 1 else ()
        if len(chosen) != 1:
            pool = chosen or matches
            return {
                "card_id": card_id,
                "spelling": spelling,
                "status": "ambiguous",
                "reason": HOMONYM_REASON,
                "candidate_atlas0_slugs": _candidates(pool),
            }
    identity = chosen[0]
    return {
        "card_id": card_id,
        "spelling": spelling,
        "status": "paired",
        "atlas0_slug": identity.slug,
        "pilot_card_id": identity.card_id,
        "_slug": identity.slug,
    }


def pair_cards(cards: list[dict], identities: tuple[AtlasIdentity, ...], registry_version: int, cards_sha256: str) -> dict:
    """Build the pairing document. Entries are sorted by card_id."""
    by_spelling: dict[str, tuple[AtlasIdentity, ...]] = {}
    grouped: dict[str, list[AtlasIdentity]] = defaultdict(list)
    for identity in identities:
        grouped[identity.spelling].append(identity)
    for spelling, group in grouped.items():
        by_spelling[spelling] = tuple(sorted(group, key=lambda item: (item.slug, item.card_id)))

    rows = [_pair_card(card, by_spelling) for card in cards]
    owners: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        slug = row.get("_slug")
        if row["status"] == "paired" and isinstance(slug, str):
            owners[slug].append(row)
    for slug, group in owners.items():
        if len(group) < 2:
            continue
        for row in group:
            card_id = row["card_id"]
            spelling = row["spelling"]
            row.clear()
            row.update({
                "card_id": card_id,
                "spelling": spelling,
                "status": "ambiguous",
                "reason": HOMONYM_REASON,
                "candidate_atlas0_slugs": [slug],
            })
    entries = []
    for row in sorted(rows, key=lambda item: item["card_id"]):
        row.pop("_slug", None)
        entries.append(row)
    counts = {"paired": 0, "unpaired": 0, "ambiguous": 0}
    for entry in entries:
        counts[entry["status"]] += 1
    document = {
        "schema_version": SCHEMA_VERSION,
        "release_version": RELEASE_VERSION,
        "cards_sha256": cards_sha256,
        "registry_version": registry_version,
        "total_cards": len(entries),
        "paired_count": counts["paired"],
        "unpaired_count": counts["unpaired"],
        "ambiguous_count": counts["ambiguous"],
        "entries": entries,
    }
    validate_document(document)
    return document


def validate_document(document: dict) -> None:
    """Reject a document that breaks the pairing schema or its count invariant."""
    errors = sorted(_VALIDATOR.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        raise PairingError(errors[0].message)
    entries = document["entries"]
    entry_errors = []
    seen: set[str] = set()
    slugs: set[str] = set()
    pilots: set[str] = set()
    for index, entry in enumerate(entries):
        entry_errors.extend(_ENTRY_VALIDATOR.iter_errors(entry))
        card_id = entry.get("card_id")
        if card_id in seen:
            raise PairingError(f"duplicate pairing card_id: {card_id}")
        if isinstance(card_id, str):
            seen.add(card_id)
        if entry.get("status") == "paired":
            if entry["atlas0_slug"] in slugs or entry["pilot_card_id"] in pilots:
                raise PairingError(f"atlas identity is not unique for {card_id}")
            slugs.add(entry["atlas0_slug"])
            pilots.add(entry["pilot_card_id"])
        previous = entries[index - 1].get("card_id") if index else None
        if isinstance(card_id, str) and isinstance(previous, str) and card_id < previous:
            raise PairingError("entries are not sorted by card_id")
    if entry_errors:
        raise PairingError(sorted(entry_errors, key=lambda item: list(item.path))[0].message)
    counts = (
        document["paired_count"], document["unpaired_count"], document["ambiguous_count"],
    )
    if sum(counts) != document["total_cards"] or document["total_cards"] != len(entries):
        raise PairingError("pairing counts do not match entries")
    if counts != (
        sum(entry["status"] == "paired" for entry in entries),
        sum(entry["status"] == "unpaired" for entry in entries),
        sum(entry["status"] == "ambiguous" for entry in entries),
    ):
        raise PairingError("pairing status counts do not match entries")


def build_pairing(cards_path: Path, registry_path: Path) -> dict:
    """Load both inputs and return the validated pairing document."""
    cards, digest = load_cards(cards_path)
    version, identities = load_atlas_identities(registry_path)
    return pair_cards(cards, identities, version, digest)


def write_atomic(path: Path, payload: bytes) -> None:
    """Replace ``path`` with ``payload``. Refuse a symlink or directory.

    The sibling stays in the destination directory so ``os.replace`` is atomic
    on one filesystem. It is not a scratch-lease tempfile.
    """
    if path.is_symlink():
        raise PairingError(f"refusing to write through a symlink: {path}")
    if path.exists() and not path.is_file():
        raise PairingError(f"output exists and is not a file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.urandom(8).hex()}.tmp"
    fd = -1
    created = False
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        created = True
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except Exception as exc:
        if fd >= 0:
            os.close(fd)
        if created:
            temporary.unlink(missing_ok=True)
        if isinstance(exc, FileExistsError):
            raise PairingError(f"could not reserve a sibling for {path}") from exc
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write the canonical atlas0 pairing for the v0.1.0-pilot word-card release.\n"
            "Use it to regenerate or check pairing-atlas0.json. "
            "Do not use it to certify language or edit the published release."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.projects.open_model_data.generate_atlas_pairing
  .venv/bin/python -m scripts.projects.open_model_data.generate_atlas_pairing --check
  .venv/bin/python -m scripts.projects.open_model_data.generate_atlas_pairing \\
      --cards data/datasets/word-cards/releases/v0.1.0-pilot/word-cards.jsonl \\
      --registry registry/atlas/identity/registry.json \\
      --output data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json

Outputs: pairing-atlas0.json (schema_version 1, entries sorted by card_id).
--check writes nothing. A missing cards file in this checkout is read from the
primary checkout when the same relative path exists there. sources.db is not opened.
Exit codes: 0 artifact written or up to date; 1 drift, refused input, or unreadable output;
2 invalid arguments.
Related: #8981, #11023; registry/atlas/identity/registry.json; docs/datasets/word-cards.md
""")
    parser.add_argument(
        "--cards", type=Path, default=DEFAULT_CARDS,
        help="Release JSONL (default: data/datasets/word-cards/releases/v0.1.0-pilot/word-cards.jsonl). "
             "Example: data/datasets/word-cards/releases/v0.1.0-pilot/word-cards.jsonl",
    )
    parser.add_argument(
        "--registry", type=Path, default=DEFAULT_REGISTRY,
        help="Atlas identity registry JSON (default: registry/atlas/identity/registry.json). "
             "Example: registry/atlas/identity/registry.json",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Pairing artifact path (default: data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json). "
             "Example: data/datasets/word-cards/releases/v0.1.0-pilot/pairing-atlas0.json",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 0 when --output matches a fresh pairing, 1 on drift. Writes nothing (default: off).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        registry_path = args.registry if args.registry.is_absolute() else ROOT / args.registry
        document = build_pairing(resolve_cards_path(args.cards), registry_path)
        payload = canonical_bytes(document)
        target = _output_target(args.output)
        if args.check:
            current = _read_bytes(target, "pairing artifact") if target.is_file() and not target.is_symlink() else b""
            if current != payload:
                print("REFUSED: pairing artifact drift", file=sys.stderr)
                return 1
        else:
            write_atomic(target, payload)
    except PairingError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    summary = {
        "ambiguous_count": document["ambiguous_count"],
        "cards_sha256": document["cards_sha256"],
        "checked": bool(args.check),
        "paired_count": document["paired_count"],
        "total_cards": document["total_cards"],
        "unpaired_count": document["unpaired_count"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
