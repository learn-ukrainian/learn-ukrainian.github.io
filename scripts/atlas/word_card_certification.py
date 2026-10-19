"""Exact-artifact certification at word-card acceptance and export boundaries.

Only the repository review ledger grants approval. A run reads that authority
once, hashes each dependency once, and discards its cache on exit. Reimports and
cached packages therefore consult current withdrawals and snapshot bindings.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REVIEW_EVIDENCE_PATH = PROJECT_ROOT / "docs/atlas/word-cards/review-evidence-ledger.json"
PERMISSIONS_REGISTER_PATH = PROJECT_ROOT / "docs/sources/permissions-register.yaml"
SCHEMA_PATH = PROJECT_ROOT / "schemas/word-card-v1.schema.json"
IMPLEMENTATION_PATHS = (
    *sorted(PROJECT_ROOT.glob("scripts/atlas/*.py")),
    PROJECT_ROOT / "scripts/lexicon/runner/ulif_dictua_parse.py",
    PROJECT_ROOT / "scripts/lexicon/source_attribution.py",
    PROJECT_ROOT / "scripts/lexicon/ulif_raw_cache.py",
    PROJECT_ROOT / "scripts/lexicon/lemma_normalization.py",
    PROJECT_ROOT / "scripts/wiki/sources_db.py",
    PROJECT_ROOT / "scripts/lexicon/manifest_io.py",
    PROJECT_ROOT / "scripts/lexicon/publish_manifest.py",
    PROJECT_ROOT / "scripts/lexicon/export_open_dataset.py",
    PROJECT_ROOT / "scripts/open_dataset/publish.py",
    PROJECT_ROOT / "scripts/open_dataset/hydrate.py",
    PROJECT_ROOT / "scripts/config/vesum_source.lock.json",
)
RULE_PATHS = (
    *sorted(PROJECT_ROOT.glob("schemas/word-card-*.schema.json")),
    PROJECT_ROOT / "docs/atlas/word-cards/schema.md",
    PROJECT_ROOT / "docs/atlas/word-cards/identity.md",
    PROJECT_ROOT / "docs/atlas/word-cards/export-invariants.md",
    PROJECT_ROOT / "docs/atlas/word-cards/acceptance-export-path-census.json",
)


class UncertifiedCardRefusal(ValueError):
    """No acceptance or export output may be written after this refusal."""


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class CertificationAuthority:
    """Authority snapshot and dependency hashes for one acceptance/export run."""

    def __init__(self) -> None:
        self.hashes: dict[Path, str] = {}
        self.snapshots: dict[tuple[str, str], str] = {}
        self.json_values: dict[Path, Any] = {}
        self.ledger = json.loads(REVIEW_EVIDENCE_PATH.read_bytes())
        if self.ledger.get("schema_version") != "word-card-review-evidence.v1":
            raise UncertifiedCardRefusal("unsupported review evidence ledger")
        reviews = self.ledger["approved_reviews"]
        if not isinstance(reviews, list):
            raise UncertifiedCardRefusal("approved_reviews must be a list")
        self.reviews = {r["card_id"]: r for r in reviews}
        if len(self.reviews) != len(reviews):
            raise UncertifiedCardRefusal("duplicate card review evidence")
        self.validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_bytes()))
        self.implementation = self.fingerprint(IMPLEMENTATION_PATHS)
        self.rules = self.fingerprint(RULE_PATHS)
        self.register = self.file_hash(PERMISSIONS_REGISTER_PATH)

    def file_hash(self, path: Path) -> str:
        if path not in self.hashes:
            with path.open("rb") as source:
                self.hashes[path] = hashlib.file_digest(source, "sha256").hexdigest()
        return self.hashes[path]

    def fingerprint(self, paths: tuple[Path, ...]) -> str:
        return digest({p.relative_to(PROJECT_ROOT).as_posix(): self.file_hash(p) for p in paths})

    def snapshot(self, category: str, name: str) -> str:
        if (category, name) in self.snapshots:
            return self.snapshots[category, name]
        binding = self.ledger["snapshot_bindings"][category][name]
        relative = Path(binding["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise UncertifiedCardRefusal("snapshot authority must be repository relative")
        path = (PROJECT_ROOT / relative).resolve()
        if not path.is_relative_to(PROJECT_ROOT.resolve()):
            raise UncertifiedCardRefusal("snapshot authority must be repository relative")
        # A lock may name a canonical data digest instead of being the data.
        # Its bytes are still bound by the review's implementation fingerprint.
        if "json_keys" in binding:
            if path not in self.json_values:
                self.json_values[path] = json.loads(path.read_bytes())
            value = self.json_values[path]
            for key in binding["json_keys"]:
                value = value[key]
            self.snapshots[category, name] = value
        else:
            self.snapshots[category, name] = self.file_hash(path)
        return self.snapshots[category, name]


_AUTHORITY: ContextVar[dict[str, CertificationAuthority] | None] = ContextVar("word_card_authority", default=None)


@contextmanager
def certification_run() -> Iterator[None]:
    """Reuse authority within this run, never across separately invoked runs."""
    current = _AUTHORITY.get()
    token = _AUTHORITY.set(current if current is not None else {})
    try:
        yield
    finally:
        _AUTHORITY.reset(token)


def looks_like_card(value: Any) -> bool:
    return isinstance(value, dict) and bool(
        {"card_id", "card_kind", "build", "quality", "assertions"}.intersection(value)
    )


@certification_run()
def load_certified_card_for_export(card: Any, *, required_approval: str = "dataset") -> dict[str, Any]:
    """Return only the exact certified card, with approval for this projection.

    There are no caller-supplied approvals, snapshot overrides or draft bypasses.
    Tests redirect the authority files to temporary fixtures.
    """
    try:
        if isinstance(card, str):
            card = json.loads(card)
        if not isinstance(card, dict) or "card_id" not in card:
            raise UncertifiedCardRefusal("entry is not a certified word card")
        state = _AUTHORITY.get()
        authority = state.get("authority")
        if authority is None:
            authority = CertificationAuthority()
            state["authority"] = authority
        if not authority.validator.is_valid(card):
            raise UncertifiedCardRefusal("invalid word-card schema")
        review = card["quality"]["linguistic_review"]
        build = card["build"]
        evidence = authority.reviews.get(card["card_id"], {})
        if (card["state"] != "active" or card["quality"]["identity_confidence"] not in {"high", "medium"}
                or not isinstance(review.get("record"), str) or not review["record"].strip()
                or not isinstance(review.get("lane"), str) or not review["lane"].strip()
                or review["status"] != "reviewed" or required_approval not in review.get("approved_for", [])
                or evidence.get("status") != "active"
                or not isinstance(evidence.get("approved_for"), list)
                or required_approval not in evidence.get("approved_for", [])
                or evidence.get("record") != review.get("record")
                or evidence.get("lane") != review.get("lane")):
            raise UncertifiedCardRefusal("missing, withdrawn or inapplicable certification")
        if (build["rules_version"] != "rules-v1"
                or build["card_version"] != "cv_" + digest({k: v for k, v in card.items() if k != "build"})[:24]
                or evidence.get("card_version") != build["card_version"]
                or evidence.get("build_sha256") != digest(build)
                or evidence.get("implementation_sha256") != authority.implementation
                or evidence.get("rules_sha256") != authority.rules):
            raise UncertifiedCardRefusal("certification does not match artifact, implementation or rules")
        inputs = build["inputs"]
        for category in ("S", "V", "I", "O"):
            if not isinstance(inputs.get(category), dict) or not inputs[category]:
                raise UncertifiedCardRefusal("missing source or removal snapshot")
            for name, snapshot in inputs[category].items():
                if snapshot["content_sha256"] != authority.snapshot(category, name):
                    raise UncertifiedCardRefusal("source or removal snapshot changed")
        if ("vesum" not in inputs["V"] or "overlay" not in inputs["O"]
                or "suppressions" not in inputs["O"]
                or inputs["R"]["rules"]["version"] != build["rules_version"]
                or inputs["R"]["normaliser"]["version"] != "norm-v1"
                or inputs["R"]["register"]["content_sha256"] != authority.register):
            raise UncertifiedCardRefusal("missing or stale rules, permissions or suppression binding")
        return card
    except UncertifiedCardRefusal:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise UncertifiedCardRefusal("missing or invalid certification authority") from exc


@certification_run()
def certified_inventory(manifest: Any, *, required_approval: str = "dataset") -> list[dict[str, Any]]:
    """Check both inventories, including mixed legacy/card manifests, before writes."""
    if not isinstance(manifest, dict):
        raise UncertifiedCardRefusal("invalid card inventory")
    if set(manifest) - {"cards", "entries", "version", "generated_at", "manifest_fingerprint"}:
        raise UncertifiedCardRefusal("unreviewed fields outside card inventory")
    for key in ("version", "generated_at"):
        if key in manifest and not isinstance(manifest[key], str):
            raise UncertifiedCardRefusal("invalid card inventory metadata")
    if "manifest_fingerprint" in manifest:
        fingerprint = manifest["manifest_fingerprint"]
        if (not isinstance(fingerprint, dict) or set(fingerprint) != {"schema_version", "fingerprint"}
                or type(fingerprint["schema_version"]) is not int or not isinstance(fingerprint["fingerprint"], str)):
            raise UncertifiedCardRefusal("invalid card inventory fingerprint")
    cards = []
    for key in ("cards", "entries"):
        if key in manifest:
            if not isinstance(manifest[key], list):
                raise UncertifiedCardRefusal("invalid card inventory")
            cards.extend(manifest[key])
    if not cards:
        raise UncertifiedCardRefusal("empty certified inventory")
    for card in cards:
        load_certified_card_for_export(card, required_approval=required_approval)
    if len({card["card_id"] for card in cards}) != len(cards):
        raise UncertifiedCardRefusal("duplicate certified card")
    return cards


def card_entry_type(card: dict[str, Any]) -> str:
    """Map schema card kinds to the existing Atlas article classification."""
    return {"lexeme": "lemma", "mwe": "multiword_term", "proper_name": "proper_name"}[card["card_kind"]]


def card_head(card: dict[str, Any]) -> str:
    return card["key_at_creation"]["spelling"]


def card_field(card: dict[str, Any], name: str) -> str | None:
    selected = card.get("fields", {}).get(name, {}).get("selected")
    for assertion in card.get("assertions", []):
        if assertion.get("assertion_id") == selected and assertion.get("status") == "active":
            value = assertion.get("value")
            return value.strip() or None if isinstance(value, str) else None
    return None


def guard_card_inventory(manifest: dict[str, Any], *, required_approval: str = "site") -> None:
    """Legacy evidence stays evidence; a card inventory must pass certification."""
    entries = manifest.get("entries", [])
    if ("cards" in manifest or manifest.get("certified") is True
            or (isinstance(entries, list) and any(looks_like_card(entry) for entry in entries))):
        certified_inventory(manifest, required_approval=required_approval)
