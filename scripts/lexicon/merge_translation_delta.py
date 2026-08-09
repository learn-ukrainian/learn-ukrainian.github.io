#!/usr/bin/env python3
"""Additive slug-keyed merge of EN translation cards onto a live Atlas manifest.

Copies ``enrichment.translation`` from a pulled (donor) manifest onto live
entries that lack EN, keyed by ``url_slug``. Never adds or drops entries, and
never overwrites a live entry that already has a non-empty EN translation.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_PULLED = ROOT / "batch_state" / "full-en-reenrich-pulled" / "manifest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT
from scripts.lexicon.manifest_io import load_manifest, write_manifest


def sync_embedded_fingerprint_from_sidecar(
    manifest: dict[str, Any],
    *,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
) -> dict[str, Any]:
    """Embed the committed fingerprint sidecar without regenerating it.

    Sparse worktrees may omit fingerprint inputs (for example ``curriculum/``),
    so ``write_fingerprint`` / ``build_fingerprint`` can drift. Publishing only
    requires the embedded value to match the committed sidecar.
    """
    payload = json.loads(fingerprint_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{fingerprint_path} must contain a JSON object")
    schema_version = payload.get("schema_version")
    fingerprint = payload.get("fingerprint")
    if schema_version is None or not isinstance(fingerprint, str) or not fingerprint:
        raise ValueError(f"{fingerprint_path} missing schema_version/fingerprint")
    manifest["manifest_fingerprint"] = {
        "schema_version": schema_version,
        "fingerprint": fingerprint,
    }
    return payload


def entry_has_translation(entry: dict[str, Any]) -> bool:
    """Return True when ``enrichment.translation.en`` has a non-empty term."""
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False
    translation = enrichment.get("translation")
    if not isinstance(translation, dict):
        return False
    terms = translation.get("en")
    return isinstance(terms, list) and any(str(term).strip() for term in terms)


def entry_translation(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Return the translation object when it carries a non-empty EN list."""
    if not entry_has_translation(entry):
        return None
    enrichment = entry.get("enrichment")
    assert isinstance(enrichment, dict)
    translation = enrichment.get("translation")
    assert isinstance(translation, dict)
    return translation


def _slug_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest.entries must be a list")
    index: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("url_slug")
        if isinstance(slug, str) and slug:
            index[slug] = entry
    return index


def _add_source(enrichment: dict[str, Any], source: object) -> None:
    if not source:
        return
    sources = set(enrichment.get("sources") or [])
    sources.add(str(source))
    enrichment["sources"] = sorted(sources)


@dataclass
class MergeStats:
    """Deterministic summary of an additive translation merge."""

    live_entry_count_before: int
    live_entry_count_after: int
    pulled_entry_count: int
    filled: int = 0
    skipped_live_has_translation: int = 0
    skipped_pulled_missing_slug: int = 0
    skipped_pulled_lacks_translation: int = 0
    filled_slugs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def merge_translation_delta(
    live: dict[str, Any],
    pulled: dict[str, Any],
    *,
    stamp_generated_at: bool = True,
) -> MergeStats:
    """Merge pulled EN translations into ``live`` in place.

    Hard invariants:
    - ``len(live["entries"])`` is unchanged
    - entries that already have EN keep their existing translation object
    - pulled-only slugs never create new live entries
    """
    entries = live.get("entries")
    if not isinstance(entries, list):
        raise ValueError("live manifest.entries must be a list")

    before_count = len(entries)
    pulled_by_slug = _slug_index(pulled)
    stats = MergeStats(
        live_entry_count_before=before_count,
        live_entry_count_after=before_count,
        pulled_entry_count=len(pulled.get("entries") or []),
    )

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        slug = entry.get("url_slug")
        if not isinstance(slug, str) or not slug:
            continue

        if entry_has_translation(entry):
            stats.skipped_live_has_translation += 1
            continue

        donor = pulled_by_slug.get(slug)
        if donor is None:
            stats.skipped_pulled_missing_slug += 1
            continue

        donor_translation = entry_translation(donor)
        if donor_translation is None:
            stats.skipped_pulled_lacks_translation += 1
            continue

        enrichment = entry.get("enrichment")
        if not isinstance(enrichment, dict):
            enrichment = {}
            entry["enrichment"] = enrichment
        enrichment["translation"] = copy.deepcopy(donor_translation)
        _add_source(enrichment, donor_translation.get("source"))
        stats.filled += 1
        stats.filled_slugs.append(slug)

    after_count = len(live.get("entries") or [])
    stats.live_entry_count_after = after_count
    if after_count != before_count:
        raise RuntimeError(
            f"entry-count invariant broken: before={before_count} after={after_count}"
        )

    if stamp_generated_at:
        live["generated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    return stats


def prove_no_nonempty_en_overwrites(
    before_by_slug: dict[str, dict[str, Any]],
    after_by_slug: dict[str, dict[str, Any]],
) -> int:
    """Count entries whose previously non-empty EN changed after the merge."""
    modified = 0
    for slug, before_entry in before_by_slug.items():
        before_tr = entry_translation(before_entry)
        if before_tr is None:
            continue
        after_entry = after_by_slug.get(slug)
        if after_entry is None:
            modified += 1
            continue
        after_tr = entry_translation(after_entry)
        if after_tr != before_tr:
            modified += 1
    return modified


def _read_local_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Additive slug-keyed merge of EN translation cards from a pulled "
            "manifest onto the live Atlas catalog (no entry add/drop, no EN overwrite)."
        )
    )
    parser.add_argument("--live", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--pulled", type=Path, default=DEFAULT_PULLED)
    parser.add_argument(
        "--local-live",
        action="store_true",
        help="Read --live directly instead of hydrating the release-pinned default path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist the merged live manifest. Default is dry-run (in-memory only).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write the merge stats JSON.",
    )
    parser.add_argument(
        "--no-stamp-generated-at",
        action="store_true",
        help="Leave live generated_at unchanged (tests / deterministic fixtures).",
    )
    args = parser.parse_args()

    live_path = args.live if args.live.is_absolute() else ROOT / args.live
    pulled_path = args.pulled if args.pulled.is_absolute() else ROOT / args.pulled

    if args.local_live or live_path.resolve() != DEFAULT_MANIFEST.resolve():
        live = _read_local_manifest(live_path)
    else:
        live = load_manifest(live_path)
    pulled = _read_local_manifest(pulled_path)

    before_by_slug = {slug: copy.deepcopy(entry) for slug, entry in _slug_index(live).items()}
    stats = merge_translation_delta(
        live,
        pulled,
        stamp_generated_at=not args.no_stamp_generated_at,
    )
    after_by_slug = _slug_index(live)
    overwrite_proof = prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug)

    payload = stats.as_dict()
    payload["overwrite_proof_modified_nonempty_en"] = overwrite_proof
    payload["missing_translation_after"] = sum(
        1 for entry in (live.get("entries") or []) if isinstance(entry, dict) and not entry_has_translation(entry)
    )
    # Keep report compact for large fills.
    if len(payload["filled_slugs"]) > 50:
        payload["filled_slugs_sample"] = payload["filled_slugs"][:50]
        payload["filled_slugs"] = []

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.report is not None:
        report_path = args.report if args.report.is_absolute() else ROOT / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if overwrite_proof != 0:
        print(
            json.dumps(
                {
                    "error": "overwrite_proof_modified_nonempty_en",
                    "overwrite_proof_modified_nonempty_en": overwrite_proof,
                    "wrote": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    if args.write:
        if live_path.resolve() == DEFAULT_MANIFEST.resolve():
            sync_embedded_fingerprint_from_sidecar(live)
        write_manifest(live_path, live)
        print(json.dumps({"wrote": str(live_path), "entries": stats.live_entry_count_after}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
