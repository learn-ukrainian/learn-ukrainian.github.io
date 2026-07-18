#!/usr/bin/env python3
"""Promote deterministic Atlas grow candidates into the live manifest.

Phase 2 writes ``data/lexicon/grow_candidates.json`` with a confidence split:
``auto_merge`` entries are dictionary-grounded and safe to promote, while
``needs_review`` entries are held unless a checksum-bound needs-review ledger
explicitly approves them (``--needs-review-ledger``). This script promotes the
clean auto_merge bucket (optionally filtered by ``--approval-ledger``) and any
ledger-approved held entries with their approved gloss injected as the learner
anchor.  Entries still lacking a learner-English anchor remain visible promotion
debt: the curation ledger records it, while the #5138 publish gate enforces the
downstream ``old_gate_no_english_anchor`` richness-regression backstop against
the live baseline.

When to use: applying a reviewed grow promotion (auto_merge and/or needs_review
re-entry) into the live manifest after ledger validation.
When NOT to use: generating triage decisions (``triage_needs_review.py``) or
emitting the needs-review decision ledger (``generate_needs_review_ledger.py``).
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
from scripts.lexicon.source_attribution import apply_entry_attribution
from scripts.sync.promote_module import _write_atomically

DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_NEEDS_REVIEW = PROJECT_ROOT / "data" / "lexicon" / "grow_needs_review.json"
PRIMARY_SOURCE = "content_lexicon_grow"
APPROVAL_LEDGER_KIND = "atlas_grow_promotion_ledger"
NEEDS_REVIEW_LEDGER_KIND = "atlas_grow_needs_review_decisions"
ALLOWED_LEDGER_DECISIONS = frozenset({"approve", "deferred", "reject"})
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
class HeldRow:
    """One needs_review row with its candidate entry payload."""

    lemma: str
    reason: str
    entry: Mapping[str, Any]


@dataclass(frozen=True)
class PromotionResult:
    candidates_found: bool
    promoted: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    held: tuple[HeldLemma, ...]
    # Deterministic per input order (canonical for the sorted content-grower path).
    cached_anchor_fills: tuple[str, ...]
    anchorless_promoted: tuple[str, ...]
    lemmas_total: int | None
    manifest_written: bool
    fingerprint_written: bool
    needs_review_written: bool
    dry_run: bool
    needs_review_approved: int = 0
    needs_review_deferred: int = 0


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
    needs_review_ledger_path: Path | None = None,
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
    if needs_review_ledger_path is not None:
        needs_review_ledger_path = _resolve_path(needs_review_ledger_path)
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
    needs_review_raw = candidates.get("needs_review", [])
    held_rows = _held_rows(needs_review_raw)
    auto_merge = _candidate_entries(candidates.get("auto_merge", []))
    if approval_ledger_path is not None:
        auto_merge = _approved_candidate_entries(
            auto_merge,
            candidates_path=candidates_path,
            approval_ledger_path=approval_ledger_path,
        )

    needs_review_to_promote: list[Mapping[str, Any]] = []
    needs_review_approved = 0
    needs_review_deferred = 0
    if needs_review_ledger_path is not None:
        approved_entries, held_rows, needs_review_approved, needs_review_deferred = (
            _approved_needs_review_entries(
                held_rows,
                candidates_path=candidates_path,
                needs_review_ledger_path=needs_review_ledger_path,
            )
        )
        needs_review_to_promote = approved_entries
    held = tuple(HeldLemma(lemma=row.lemma, reason=row.reason) for row in held_rows)

    promote_queue: list[Mapping[str, Any]] = list(auto_merge) + list(needs_review_to_promote)

    manifest = _load_manifest(manifest_path)
    entries = manifest["entries"]
    existing_keys = _manifest_lemma_keys(entries)
    sorted_keys = [_lemma_key(str(entry.get("lemma") or "")) for entry in entries if isinstance(entry, dict)]

    promoted: list[str] = []
    skipped_existing: list[str] = []
    newly_promoted_entries: list[dict[str, Any]] = []
    for candidate in promote_queue:
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

    # Fill before validation: the prospective gate must inspect the exact post-fill
    # manifest state that would ship, including its translation/source enrichment.
    cached_anchor_fills, anchorless_promoted = _fill_cached_anchors_for_new_entries(newly_promoted_entries)

    for entry in newly_promoted_entries:
        apply_entry_attribution(entry)

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
        needs_review_approved=needs_review_approved,
        needs_review_deferred=needs_review_deferred,
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
            f"Needs-review ledger approve: {result.needs_review_approved}",
            f"Needs-review ledger deferred: {result.needs_review_deferred}",
            f"Cached learner-English anchors filled: {len(result.cached_anchor_fills)}",
            f"Promoted entries still without learner-English anchor: {len(result.anchorless_promoted)}",
            f"New lemmas_total: {result.lemmas_total}",
            f"Manifest written: {str(result.manifest_written).lower()}",
            f"Fingerprint written: {str(result.fingerprint_written).lower()}",
            f"Needs-review written: {str(result.needs_review_written).lower()}",
        ]
    )
    if result.anchorless_promoted:
        lines.append(
            "Backstop: #5138 publish gate blocks old_gate_no_english_anchor regression "
            "against the live baseline unless --allow-richness-regression has a recorded reason."
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
    parser = argparse.ArgumentParser(
        description=(
            "Promote Atlas grow candidates into the live lexicon manifest. "
            "Use this after a reviewed auto_merge and/or needs_review ledger is "
            "ready; do not use it to invent glosses or triage held lemmas."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dry-run auto_merge promotion\n"
            "  .venv/bin/python scripts/lexicon/promote_grow_candidates.py --dry-run\n"
            "\n"
            "  # Promote only ledger-approved auto_merge rows\n"
            "  .venv/bin/python scripts/lexicon/promote_grow_candidates.py --write \\\n"
            "    --approval-ledger data/lexicon/grow-triage-ledgers/…-ledger.yaml\n"
            "\n"
            "  # Re-enter needs_review via a sha-bound decisions ledger (#5230)\n"
            "  .venv/bin/python scripts/lexicon/promote_grow_candidates.py --write \\\n"
            "    --needs-review-ledger data/lexicon/source-inventory-review-decisions/"
            "…-grow-needs-review-batch-01.yaml\n"
            "\n"
            "Outputs (only with --write):\n"
            "  site/src/data/lexicon-manifest.json           updated when promotions land\n"
            "  site/src/data/lexicon-manifest.fingerprint.json  refreshed sidecar\n"
            "  data/lexicon/grow_needs_review.json           remaining held rows\n"
            "\n"
            "Exit codes:\n"
            "  0  success (dry-run or write)\n"
            "  2  validation/self-check failure; no files written\n"
            "\n"
            "Related:\n"
            "  scripts/lexicon/generate_needs_review_ledger.py  — build needs-review ledger\n"
            "  scripts/lexicon/triage_needs_review.py           — deterministic held triage\n"
            "  issue #5230                                     — needs_review re-entry arc\n"
        ),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help=f"Path to grow_candidates.json (default: {DEFAULT_CANDIDATES})",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to lexicon-manifest.json (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--needs-review",
        type=Path,
        default=DEFAULT_NEEDS_REVIEW,
        help=f"Path for remaining held-review JSON report (default: {DEFAULT_NEEDS_REVIEW})",
    )
    parser.add_argument(
        "--fingerprint",
        type=Path,
        default=DEFAULT_FINGERPRINT,
        help=f"Fingerprint sidecar path (default: {DEFAULT_FINGERPRINT})",
    )
    parser.add_argument(
        "--approval-ledger",
        type=Path,
        help=(
            "Optional exact, checksum-bound atlas_grow_promotion_ledger; "
            "only its approve decisions are promoted from auto_merge"
        ),
    )
    parser.add_argument(
        "--needs-review-ledger",
        type=Path,
        help=(
            "Optional exact, dual-sha-bound atlas_grow_needs_review_decisions ledger; "
            "only its approve rows are promoted from needs_review (with approved_gloss)"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the manifest, fingerprint sidecar, and held-review report",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing (default behaviour)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print promoted and held lemma details",
    )
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
            needs_review_ledger_path=args.needs_review_ledger,
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
    payload = load_ledger_mapping(approval_ledger_path, label="approval ledger")
    require_ledger_kind(payload, APPROVAL_LEDGER_KIND, label="approval ledger")
    provenance = require_ledger_provenance(payload, label="approval ledger")
    require_file_sha256(
        candidates_path,
        provenance.get("candidates_sha256"),
        label="approval ledger candidates_sha256",
        mismatch_message="approval ledger candidate SHA-256 does not match the supplied candidates file",
    )
    decision_rows = parse_ledger_decision_rows(
        payload.get("decisions"),
        label="approval ledger",
        allowed_decisions=ALLOWED_LEDGER_DECISIONS,
    )
    candidate_by_key = index_by_decision_key(candidates, label="auto-merge candidate")
    require_exact_decision_coverage(
        set(candidate_by_key),
        set(decision_rows),
        scope_label="auto-merge candidates",
        ledger_label="approval ledger",
    )
    return [
        candidate
        for candidate in candidates
        if decision_rows[_candidate_decision_key(candidate)]["decision"] == "approve"
    ]


def _approved_needs_review_entries(
    held_rows: Sequence[HeldRow],
    *,
    candidates_path: Path,
    needs_review_ledger_path: Path,
) -> tuple[list[Mapping[str, Any]], list[HeldRow], int, int]:
    """Return gloss-injected approve entries + remaining held rows from a bound ledger.

    Fail-closed: kind, candidates_sha256, triage_sha256 presence, exact coverage of
    the full needs_review set, and decision vocabulary must all validate before any
    promotion is considered.
    """
    payload = load_ledger_mapping(needs_review_ledger_path, label="needs-review ledger")
    require_ledger_kind(payload, NEEDS_REVIEW_LEDGER_KIND, label="needs-review ledger")
    provenance = require_ledger_provenance(payload, label="needs-review ledger")
    require_file_sha256(
        candidates_path,
        provenance.get("candidates_sha256"),
        label="needs-review ledger candidates_sha256",
        mismatch_message=(
            "needs-review ledger candidates_sha256 does not match the supplied candidates file"
        ),
    )
    triage_sha = str(provenance.get("triage_sha256") or "").strip()
    if not triage_sha:
        raise ValueError("needs-review ledger provenance lacks triage_sha256")
    if len(triage_sha) != 64 or any(ch not in "0123456789abcdef" for ch in triage_sha.casefold()):
        raise ValueError("needs-review ledger triage_sha256 must be a 64-char hex digest")

    decision_rows = parse_ledger_decision_rows(
        payload.get("decisions"),
        label="needs-review ledger",
        allowed_decisions=ALLOWED_LEDGER_DECISIONS,
    )
    held_by_key = index_held_rows_by_decision_key(held_rows)
    require_exact_decision_coverage(
        set(held_by_key),
        set(decision_rows),
        scope_label="needs_review candidates",
        ledger_label="needs-review ledger",
    )

    approved: list[Mapping[str, Any]] = []
    remaining_held: list[HeldRow] = []
    approve_count = 0
    deferred_count = 0
    for key, row in held_by_key.items():
        decision_row = decision_rows[key]
        decision = decision_row["decision"]
        if decision == "approve":
            if decision_row.get("heritage") is True:
                raise ValueError(f"needs-review ledger approve row must not set heritage=true: {key!r}")
            gloss = decision_row.get("approved_gloss")
            if not isinstance(gloss, Mapping):
                raise ValueError(f"needs-review ledger approve row lacks approved_gloss: {key!r}")
            text = str(gloss.get("text") or "").strip()
            source = str(gloss.get("source") or "").strip()
            if not text:
                raise ValueError(f"needs-review ledger approved_gloss.text is empty: {key!r}")
            if not source:
                raise ValueError(f"needs-review ledger approved_gloss.source is empty: {key!r}")
            approved.append(inject_approved_gloss(row.entry, {"text": text, "source": source}))
            approve_count += 1
        else:
            # deferred / reject stay held; heritage rows are always deferred by generator.
            deferred_count += 1
            remaining_held.append(row)

    # Preserve original needs_review order for held report stability.
    remaining_keys = {_candidate_decision_key(row.entry) for row in remaining_held}
    ordered_held = [row for row in held_rows if _candidate_decision_key(row.entry) in remaining_keys]
    return approved, ordered_held, approve_count, deferred_count


def load_ledger_mapping(path: Path, *, label: str) -> Mapping[str, Any]:
    """Load a YAML ledger as a mapping (shared auto_merge / needs_review helper)."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read {label}: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"{label} is not valid YAML: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} must be a mapping: {path}")
    return payload


def require_ledger_kind(payload: Mapping[str, Any], kind: str, *, label: str) -> None:
    if payload.get("kind") != kind:
        raise ValueError(f"{label} kind must be {kind!r}")


def require_ledger_provenance(payload: Mapping[str, Any], *, label: str) -> Mapping[str, Any]:
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError(f"{label} lacks provenance")
    return provenance


def require_file_sha256(
    path: Path,
    expected: object,
    *,
    label: str,
    mismatch_message: str,
) -> str:
    """Compare path bytes to an expected hex digest; return the actual digest."""
    expected_sha = str(expected or "").strip()
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if not expected_sha:
        raise ValueError(f"{label} is missing")
    if expected_sha != actual_sha:
        raise ValueError(mismatch_message)
    return actual_sha


def parse_ledger_decision_rows(
    raw_decisions: object,
    *,
    label: str,
    allowed_decisions: frozenset[str] = ALLOWED_LEDGER_DECISIONS,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Parse decision rows keyed by (lemma_key, pos); fail on duplicates/invalid vocab."""
    if not isinstance(raw_decisions, list):
        raise ValueError(f"{label} decisions must be a list")
    decision_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in raw_decisions:
        if not isinstance(row, Mapping):
            raise ValueError(f"{label} decision must be a mapping")
        key = _candidate_decision_key(row)
        if key in decision_by_key:
            raise ValueError(f"duplicate {label} decision key: {key!r}")
        decision = str(row.get("decision") or "").strip()
        if decision not in allowed_decisions:
            raise ValueError(f"invalid {label} decision for {key!r}: {decision!r}")
        normalized = dict(row)
        normalized["decision"] = decision
        decision_by_key[key] = normalized
    return decision_by_key


def index_by_decision_key(
    candidates: Sequence[Mapping[str, Any]],
    *,
    label: str,
) -> dict[tuple[str, str], Mapping[str, Any]]:
    by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for candidate in candidates:
        key = _candidate_decision_key(candidate)
        if key in by_key:
            raise ValueError(f"duplicate {label} decision key: {key!r}")
        by_key[key] = candidate
    return by_key


def index_held_rows_by_decision_key(held_rows: Sequence[HeldRow]) -> dict[tuple[str, str], HeldRow]:
    by_key: dict[tuple[str, str], HeldRow] = {}
    for row in held_rows:
        key = _candidate_decision_key(row.entry)
        if key in by_key:
            raise ValueError(f"duplicate needs_review candidate decision key: {key!r}")
        by_key[key] = row
    return by_key


def require_exact_decision_coverage(
    candidate_keys: set[tuple[str, str]],
    decision_keys: set[tuple[str, str]],
    *,
    scope_label: str,
    ledger_label: str,
) -> None:
    if candidate_keys == decision_keys:
        return
    missing = sorted(candidate_keys - decision_keys)
    unexpected = sorted(decision_keys - candidate_keys)
    details: list[str] = []
    if missing:
        details.append(f"missing decisions={len(missing)}")
    if unexpected:
        details.append(f"unexpected decisions={len(unexpected)}")
    raise ValueError(f"{ledger_label} does not exactly cover {scope_label} ({', '.join(details)})")


def inject_approved_gloss(
    candidate: Mapping[str, Any],
    approved_gloss: Mapping[str, str],
) -> dict[str, Any]:
    """Inject ledger-approved gloss as definition/anchor on a needs_review entry.

    Sets top-level ``gloss`` (satisfies the learner-English anchor check) and
    seeds ``enrichment.meaning`` / ``enrichment.translation`` so the existing
    anchor-fill short-circuit and attribution pass see a grounded definition.
    """
    text = str(approved_gloss.get("text") or "").strip()
    source = str(approved_gloss.get("source") or "").strip()
    if not text:
        raise ValueError("approved_gloss.text must be non-empty")
    entry = dict(candidate)
    entry["gloss"] = text
    enrichment_raw = entry.get("enrichment")
    enrichment: dict[str, Any] = dict(enrichment_raw) if isinstance(enrichment_raw, Mapping) else {}

    meaning_raw = enrichment.get("meaning")
    meaning: dict[str, Any] = dict(meaning_raw) if isinstance(meaning_raw, Mapping) else {}
    definitions = meaning.get("definitions")
    if not (isinstance(definitions, list) and any(str(item or "").strip() for item in definitions)):
        meaning["definitions"] = [text]
        if source:
            meaning["source"] = source
        enrichment["meaning"] = meaning

    translation_raw = enrichment.get("translation")
    translation: dict[str, Any] = dict(translation_raw) if isinstance(translation_raw, Mapping) else {}
    en_terms = translation.get("en")
    if not (isinstance(en_terms, list) and any(isinstance(t, str) and t.strip() for t in en_terms)):
        translation["en"] = [text]
        if source:
            translation["source"] = source
        enrichment["translation"] = translation

    sources = list(enrichment.get("sources") or []) if isinstance(enrichment.get("sources"), list) else []
    if source and source not in sources:
        sources.append(source)
    enrichment["sources"] = sources
    entry["enrichment"] = enrichment
    return entry


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
    The #5138 publish gate remains the hard backstop for an
    ``old_gate_no_english_anchor`` regression against the live baseline.
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
    return [HeldLemma(lemma=row.lemma, reason=row.reason) for row in _held_rows(raw_items)]


def _held_rows(raw_items: object) -> list[HeldRow]:
    """Parse needs_review payload rows into HeldRow values (entry + reason)."""
    if not isinstance(raw_items, list):
        return []
    held: list[HeldRow] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        entry_raw = item.get("entry")
        if isinstance(entry_raw, Mapping):
            entry: Mapping[str, Any] = entry_raw
        else:
            # Tolerate bare entry objects (tests / alternate emitters).
            entry = item
        lemma = str(entry.get("lemma") or "").strip()
        if not lemma:
            continue
        reason = str(item.get("reason") or entry.get("held_reason") or "").strip()
        held.append(HeldRow(lemma=lemma, reason=reason, entry=entry))
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
