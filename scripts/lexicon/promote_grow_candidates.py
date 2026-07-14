#!/usr/bin/env python3
"""Promote deterministic Atlas grow candidates into the live manifest.

Phase 2 writes ``data/lexicon/grow_candidates.json`` with a confidence split:
``auto_merge`` entries are dictionary-grounded and safe to promote, while
``needs_review`` entries are held for a human. This script promotes only the
clean bucket, validates the prospective manifest before writing it, and leaves
the held set as a local PR-body artifact.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.check_atlas_manifest_enrichment import check_enrichment
from scripts.lexicon import verify_manifest
from scripts.lexicon.build_data_manifest import _lemma_key, _slug_for_url
from scripts.lexicon.enrich_manifest import (
    _entry_has_learner_english_anchor,
    _fill_learner_english_anchor_from_slovnyk_cache,
    _load_slovnyk_cache_file,
    _slovnyk_cache_path,
)
from scripts.lexicon.fill_from_content import ModuleInfo, _load_manifest, _manifest_entry
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.manifest_fingerprint import (
    DEFAULT_FINGERPRINT,
    build_fingerprint,
    write_fingerprint,
)
from scripts.sync.promote_module import _write_atomically

DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_NEEDS_REVIEW = PROJECT_ROOT / "data" / "lexicon" / "grow_needs_review.json"
PRIMARY_SOURCE = "content_lexicon_grow"
APPROVAL_LEDGER_KIND = "atlas_grow_promotion_ledger"
_OPTIONAL_CANDIDATE_FIELDS = (
    "heritage_status",
    "enrichment",
    "pronunciation",
    "sections",
    "wiki_reference",
    # Granular source-inventory provenance (source_id/title/locator/context) is
    # emitted by grow_lexicon_from_sources.py and must survive promotion so the
    # manifest entry keeps a traceable origin. The Atlas conformance/enrichment
    # gates impose no closed key set, so it is retained verbatim at top level.
    "source_provenance",
)
_ENRICHED_STAT_KEYS = ("enriched", "enriched_total", "enriched_count")
_DUMMY_MODULE = ModuleInfo(track="", slug="", module_num=0, vocab_path=Path())

SelfCheck = Callable[[Path], int]
FingerprintWriter = Callable[[Path], Any]


@dataclass(frozen=True)
class HeldLemma:
    lemma: str
    reason: str


@dataclass(frozen=True)
class PromotionResult:
    candidates_found: bool
    promoted: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    held: tuple[HeldLemma, ...]
    cached_anchor_fills: tuple[str, ...]
    anchorless_promoted: tuple[str, ...]
    lemmas_total: int | None
    manifest_written: bool
    fingerprint_written: bool
    needs_review_written: bool
    dry_run: bool


class SelfCheckError(RuntimeError):
    """Raised when a prospective manifest fails a required promote gate."""

    def __init__(self, exit_code: int) -> None:
        self.exit_code = exit_code or 2
        super().__init__(f"manifest self-check failed with exit code {self.exit_code}")


def promote_grow_candidates(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    manifest_path: Path = DEFAULT_MANIFEST,
    needs_review_path: Path = DEFAULT_NEEDS_REVIEW,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    approval_ledger_path: Path | None = None,
    write: bool = False,
    self_check: SelfCheck | None = None,
    fingerprint_writer: FingerprintWriter | None = None,
) -> PromotionResult:
    """Promote clean grow candidates and return a structured summary."""
    candidates_path = _resolve_path(candidates_path)
    manifest_path = _resolve_path(manifest_path)
    needs_review_path = _resolve_path(needs_review_path)
    fingerprint_path = _resolve_path(fingerprint_path)
    if approval_ledger_path is not None:
        approval_ledger_path = _resolve_path(approval_ledger_path)
    self_check = self_check or verify_prospective_manifest
    fingerprint_writer = fingerprint_writer or _write_fingerprint_sidecar

    if not candidates_path.exists():
        return PromotionResult(
            candidates_found=False,
            promoted=(),
            skipped_existing=(),
            held=(),
            cached_anchor_fills=(),
            anchorless_promoted=(),
            lemmas_total=None,
            manifest_written=False,
            fingerprint_written=False,
            needs_review_written=False,
            dry_run=not write,
        )

    candidates = _load_candidates(candidates_path)
    held = tuple(_held_lemmas(candidates.get("needs_review", [])))
    auto_merge = _candidate_entries(candidates.get("auto_merge", []))
    if approval_ledger_path is not None:
        auto_merge = _approved_candidate_entries(
            auto_merge,
            candidates_path=candidates_path,
            approval_ledger_path=approval_ledger_path,
        )
    manifest = _load_manifest(manifest_path)
    entries = manifest["entries"]
    existing_keys = _manifest_lemma_keys(entries)
    sorted_keys = [_lemma_key(str(entry.get("lemma") or "")) for entry in entries if isinstance(entry, dict)]

    promoted: list[str] = []
    skipped_existing: list[str] = []
    newly_promoted_entries: list[dict[str, Any]] = []
    for candidate in auto_merge:
        lemma = strip_acute_stress(_candidate_lemma(candidate))
        key = _lemma_key(lemma)
        if key in existing_keys:
            skipped_existing.append(lemma)
            continue
        entry = manifest_entry_from_candidate(candidate)
        _insert_manifest_entry(entries, sorted_keys, entry)
        existing_keys.add(key)
        promoted.append(lemma)
        newly_promoted_entries.append(entry)

    cached_anchor_fills, anchorless_promoted = _fill_cached_anchors_for_new_entries(
        newly_promoted_entries
    )

    if promoted:
        _refresh_manifest_metadata(manifest)

    manifest_written = False
    fingerprint_written = False
    needs_review_written = False

    if write:
        if promoted:
            _validate_before_write(manifest, manifest_path, self_check)
            _write_json_atomically(manifest_path, manifest)
            manifest_written = True
            fingerprint_writer(fingerprint_path)
            fingerprint_written = True
        _write_needs_review(needs_review_path, held)
        needs_review_written = True

    return PromotionResult(
        candidates_found=True,
        promoted=tuple(promoted),
        skipped_existing=tuple(skipped_existing),
        held=held,
        cached_anchor_fills=cached_anchor_fills,
        anchorless_promoted=anchorless_promoted,
        lemmas_total=len(entries),
        manifest_written=manifest_written,
        fingerprint_written=fingerprint_written,
        needs_review_written=needs_review_written,
        dry_run=not write,
    )


def manifest_entry_from_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Build one live manifest entry from a P2 enriched candidate."""
    lemma = strip_acute_stress(_candidate_lemma(candidate))
    gloss = _candidate_gloss(candidate)
    pos = _clean_optional_str(candidate.get("pos"))
    base_entry = _manifest_entry(
        lemma,
        {"translation": gloss, "gloss": gloss, "pos": pos, "ipa": candidate.get("ipa")},
        _DUMMY_MODULE,
        {"pos": pos},
    )
    base_entry["url_slug"] = _slug_for_url(lemma)
    base_entry["primary_source"] = _clean_optional_str(candidate.get("primary_source")) or PRIMARY_SOURCE
    base_entry["course_usage"] = _course_usage(candidate)

    for field in _OPTIONAL_CANDIDATE_FIELDS:
        if field in candidate:
            base_entry[field] = candidate[field]
    if "pos" in candidate:
        base_entry["pos"] = candidate.get("pos")
    return base_entry


def verify_prospective_manifest(manifest_path: Path) -> int:
    """Run the required Atlas promote gates against a manifest file."""
    verify_status = verify_manifest.run(
        manifest_path,
        sample=0,
        baseline_path=None,
        run_conformance=True,
    )
    enrichment_status = check_enrichment(manifest_path=manifest_path)
    return verify_status or enrichment_status


def format_summary(result: PromotionResult, *, report: bool = False, candidates_path: Path = DEFAULT_CANDIDATES) -> str:
    lines = ["Atlas grow promotion"]
    if not result.candidates_found:
        lines.append(f"Candidates: no candidates file at {_display_path(candidates_path)}")
        lines.extend(
            [
                "Promoted: 0",
                "Held for review: 0",
                "New lemmas_total: unchanged",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"Mode: {'dry-run' if result.dry_run else 'write'}",
            f"Promoted: {len(result.promoted)}",
            f"Skipped existing: {len(result.skipped_existing)}",
            f"Held for review: {len(result.held)}",
            f"Cached learner-English anchors filled: {len(result.cached_anchor_fills)}",
            f"Promoted entries still without learner-English anchor: {len(result.anchorless_promoted)}",
            f"New lemmas_total: {result.lemmas_total}",
            f"Manifest written: {str(result.manifest_written).lower()}",
            f"Fingerprint written: {str(result.fingerprint_written).lower()}",
            f"Needs-review written: {str(result.needs_review_written).lower()}",
        ]
    )
    if report:
        if result.promoted:
            lines.append("Promoted lemmas:")
            lines.extend(f"- {lemma}" for lemma in result.promoted)
        if result.skipped_existing:
            lines.append("Skipped existing lemmas:")
            lines.extend(f"- {lemma}" for lemma in result.skipped_existing)
        if result.held:
            lines.append("Held lemmas:")
            lines.extend(f"- {item.lemma}: {item.reason}" for item in result.held)
        if result.anchorless_promoted:
            lines.append("Promoted entries without learner-English anchor:")
            lines.extend(f"- {lemma}" for lemma in result.anchorless_promoted)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--needs-review", type=Path, default=DEFAULT_NEEDS_REVIEW)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument(
        "--approval-ledger",
        type=Path,
        help=(
            "Require an exact, checksum-bound atlas_grow_promotion_ledger; "
            "only its approve decisions are promoted"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Write the manifest and held-review report")
    mode.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    parser.add_argument("--report", action="store_true", help="Print promoted and held lemma details")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = promote_grow_candidates(
            candidates_path=args.candidates,
            manifest_path=args.manifest,
            needs_review_path=args.needs_review,
            fingerprint_path=args.fingerprint,
            approval_ledger_path=args.approval_ledger,
            write=args.write,
        )
    except (SelfCheckError, ValueError) as exc:
        print(f"error: {exc}; no files written", file=sys.stderr)
        return exc.exit_code if isinstance(exc, SelfCheckError) else 2
    print(format_summary(result, report=args.report, candidates_path=args.candidates))
    return 0


def _resolve_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_candidates(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Candidates payload must be a JSON object: {path}")
    return payload


def _candidate_entries(raw_entries: object) -> list[Mapping[str, Any]]:
    if not isinstance(raw_entries, list):
        return []
    return [entry for entry in raw_entries if isinstance(entry, Mapping)]


def _approved_candidate_entries(
    candidates: Sequence[Mapping[str, Any]],
    *,
    candidates_path: Path,
    approval_ledger_path: Path,
) -> list[Mapping[str, Any]]:
    """Return only explicitly approved candidates from a bound triage ledger.

    A grow run can be deterministic while still surfacing an unsafe systematic
    class.  The ledger is therefore an additional fail-closed decision gate:
    it must cover the exact current auto-merge set and identify the candidate
    file by SHA-256.  A stale, partial, or mismatched ledger cannot silently
    broaden promotion.
    """
    try:
        payload = yaml.safe_load(approval_ledger_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read approval ledger: {approval_ledger_path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"approval ledger is not valid YAML: {approval_ledger_path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"approval ledger must be a mapping: {approval_ledger_path}")
    if payload.get("kind") != APPROVAL_LEDGER_KIND:
        raise ValueError(
            f"approval ledger kind must be {APPROVAL_LEDGER_KIND!r}: {approval_ledger_path}"
        )

    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("approval ledger lacks provenance")
    expected_sha256 = str(provenance.get("candidates_sha256") or "").strip()
    actual_sha256 = hashlib.sha256(candidates_path.read_bytes()).hexdigest()
    if expected_sha256 != actual_sha256:
        raise ValueError(
            "approval ledger candidate SHA-256 does not match the supplied candidates file"
        )

    raw_decisions = payload.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ValueError("approval ledger decisions must be a list")

    candidate_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for candidate in candidates:
        key = _candidate_decision_key(candidate)
        if key in candidate_by_key:
            raise ValueError(f"duplicate auto-merge candidate decision key: {key!r}")
        candidate_by_key[key] = candidate

    decision_by_key: dict[tuple[str, str], str] = {}
    for row in raw_decisions:
        if not isinstance(row, Mapping):
            raise ValueError("approval ledger decision must be a mapping")
        key = _candidate_decision_key(row)
        if key in decision_by_key:
            raise ValueError(f"duplicate approval ledger decision key: {key!r}")
        decision = str(row.get("decision") or "").strip()
        if decision not in {"approve", "deferred", "reject"}:
            raise ValueError(f"invalid approval ledger decision for {key!r}: {decision!r}")
        decision_by_key[key] = decision

    candidate_keys = set(candidate_by_key)
    decision_keys = set(decision_by_key)
    if candidate_keys != decision_keys:
        missing = sorted(candidate_keys - decision_keys)
        unexpected = sorted(decision_keys - candidate_keys)
        details: list[str] = []
        if missing:
            details.append(f"missing decisions={len(missing)}")
        if unexpected:
            details.append(f"unexpected decisions={len(unexpected)}")
        raise ValueError(
            "approval ledger does not exactly cover auto-merge candidates "
            f"({', '.join(details)})"
        )

    return [
        candidate
        for candidate in candidates
        if decision_by_key[_candidate_decision_key(candidate)] == "approve"
    ]


def _candidate_decision_key(candidate: Mapping[str, Any]) -> tuple[str, str]:
    lemma = _lemma_key(strip_acute_stress(_candidate_lemma(candidate)))
    pos = str(candidate.get("pos") or "").strip().casefold()
    if not pos:
        raise ValueError(f"candidate decision key lacks pos: {candidate.get('lemma')!r}")
    return lemma, pos


def _fill_cached_anchors_for_new_entries(
    entries: Sequence[dict[str, Any]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Fill cached English anchors only for this promotion's new entries.

    The helper deliberately reads the pre-existing slovnyk cache and never
    fetches or invents glosses.  Any remaining lemma is returned so callers
    must preserve it in the next curation ledger instead of hiding search debt.
    """
    filled: list[str] = []
    anchorless: list[str] = []
    for entry in entries:
        lemma = _candidate_lemma(entry)
        cache = _load_slovnyk_cache_file(_slovnyk_cache_path(lemma))
        if _fill_learner_english_anchor_from_slovnyk_cache(entry, lemma, cache):
            filled.append(lemma)
        if not _entry_has_learner_english_anchor(entry):
            anchorless.append(lemma)
    return tuple(filled), tuple(anchorless)


def _candidate_lemma(candidate: Mapping[str, Any]) -> str:
    lemma = str(candidate.get("lemma") or "").strip()
    if not lemma:
        raise ValueError("candidate entry is missing lemma")
    return lemma


def _manifest_lemma_keys(entries: Sequence[Any]) -> set[str]:
    keys: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        lemma = entry.get("lemma")
        if isinstance(lemma, str) and lemma.strip():
            keys.add(_lemma_key(lemma))
    return keys


def _candidate_gloss(candidate: Mapping[str, Any]) -> str | None:
    explicit = _clean_optional_str(candidate.get("gloss"))
    if explicit:
        return explicit
    enrichment = candidate.get("enrichment")
    if isinstance(enrichment, Mapping):
        meaning = enrichment.get("meaning")
        gloss = _meaning_text(meaning)
        if gloss:
            return gloss
    return None


def _meaning_text(meaning: object) -> str | None:
    if isinstance(meaning, str):
        return _clean_optional_str(meaning)
    if not isinstance(meaning, Mapping):
        return None
    definitions = meaning.get("definitions")
    if isinstance(definitions, list):
        for definition in definitions:
            text = _definition_text(definition)
            if text:
                return text
    for key in ("text", "definition", "gloss"):
        text = _clean_optional_str(meaning.get(key))
        if text:
            return text
    return None


def _definition_text(definition: object) -> str | None:
    if isinstance(definition, Mapping):
        for key in ("text", "definition", "value"):
            text = _clean_optional_str(definition.get(key))
            if text:
                return text
        return None
    return _clean_optional_str(definition)


def _clean_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _course_usage(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    direct_usage = candidate.get("course_usage")
    if isinstance(direct_usage, list):
        return [dict(item) for item in direct_usage if isinstance(item, Mapping)]

    contexts = candidate.get("source_contexts")
    if isinstance(contexts, list):
        usage_rows: list[dict[str, Any]] = []
        for item in contexts:
            if not isinstance(item, Mapping):
                continue
            usage = _usage_from_context(item)
            if usage:
                usage_rows.append(usage)
        return usage_rows

    context = candidate.get("source_context")
    if isinstance(context, Mapping):
        usage = _usage_from_context(context)
        return [usage] if usage else []
    return []


def _usage_from_context(context: Mapping[str, Any]) -> dict[str, Any] | None:
    track = _clean_optional_str(context.get("track"))
    slug = _clean_optional_str(context.get("slug"))
    if not track or not slug:
        return None
    usage: dict[str, Any] = {
        "track": track,
        "slug": slug,
        "context": _clean_optional_str(context.get("context")) or PRIMARY_SOURCE,
    }
    module_num = context.get("module_num")
    if module_num is not None:
        usage["module_num"] = module_num
    return usage


def _insert_manifest_entry(entries: list[dict[str, Any]], sorted_keys: list[str], entry: dict[str, Any]) -> None:
    key = _lemma_key(str(entry["lemma"]))
    index = bisect.bisect_left(sorted_keys, key)
    entries.insert(index, entry)
    sorted_keys.insert(index, key)


def _refresh_manifest_metadata(manifest: dict[str, Any]) -> None:
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("Manifest entries must be a list")
    stats = manifest.setdefault("stats", {})
    if not isinstance(stats, dict):
        stats = {}
        manifest["stats"] = stats
    stats["lemmas_total"] = len(entries)
    enriched_count = sum(1 for entry in entries if isinstance(entry, Mapping) and entry.get("enrichment"))
    for key in _ENRICHED_STAT_KEYS:
        if key in stats:
            stats[key] = enriched_count
    manifest["enrichment_generated"] = True
    manifest["generated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    _embed_manifest_fingerprint(manifest)


def _embed_manifest_fingerprint(manifest: dict[str, Any]) -> None:
    """Re-stamp the manifest's embedded fingerprint to match the sidecar.

    ``publish_manifest.py`` rejects a manifest whose embedded
    ``manifest_fingerprint`` does not match the committed
    ``lexicon-manifest.fingerprint.json`` sidecar. Promotion mutates lexicon
    code state, so keep the embedded value aligned with the freshly built
    sidecar (mirrors ``repair_plural_noun_aliases.py``).
    """
    fingerprint_payload = build_fingerprint(PROJECT_ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }


def _validate_before_write(manifest: dict[str, Any], manifest_path: Path, self_check: SelfCheck) -> None:
    with tempfile.TemporaryDirectory(prefix="atlas-grow-promote-") as tmp_dir:
        temp_manifest = Path(tmp_dir) / manifest_path.name
        temp_manifest.write_bytes(_json_bytes(manifest))
        exit_code = self_check(temp_manifest)
    if exit_code != 0:
        raise SelfCheckError(exit_code)


def _write_json_atomically(path: Path, payload: object) -> None:
    _write_atomically(path, _json_bytes(payload))


def _write_needs_review(path: Path, held: Sequence[HeldLemma]) -> None:
    payload = [{"lemma": item.lemma, "reason": item.reason} for item in held]
    _write_json_atomically(path, payload)


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _held_lemmas(raw_items: object) -> list[HeldLemma]:
    if not isinstance(raw_items, list):
        return []
    held: list[HeldLemma] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        entry = item.get("entry")
        lemma = ""
        if isinstance(entry, Mapping):
            lemma = str(entry.get("lemma") or "").strip()
        reason = str(item.get("reason") or "").strip()
        held.append(HeldLemma(lemma=lemma, reason=reason))
    return held


def _write_fingerprint_sidecar(path: Path) -> dict[str, Any]:
    return write_fingerprint(path, root=PROJECT_ROOT)


def _display_path(path: Path) -> str:
    path = _resolve_path(path)
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
