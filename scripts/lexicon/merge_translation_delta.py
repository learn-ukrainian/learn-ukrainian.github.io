#!/usr/bin/env python3
"""Additive slug-keyed merge of EN translation cards and layer sections onto a live Atlas manifest.

Copies ``enrichment.translation``, ``sections.*``, ``enrichment.literary_attestation``,
and ``enrichment.morphology`` from a pulled (donor) manifest onto live entries that lack them,
keyed by ``url_slug``. Never adds or drops entries, and never overwrites live entry fields
that are already non-empty. Includes publish-side CAS re-validation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
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

from scripts.audit.audit_atlas_thin_enriched import (
    has_learner_english_anchor,
    thin_old_gate_entries,
)
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
    """Deterministic summary of an additive translation and section merge."""

    live_entry_count_before: int
    live_entry_count_after: int
    pulled_entry_count: int
    filled: int = 0
    filled_sections: int = 0
    filled_layer_sections: dict[str, int] = field(default_factory=dict)
    filled_literary_attestation: int = 0
    filled_morphology: int = 0
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
    """Merge pulled EN translations and layer sections into ``live`` in place.

    Hard invariants:
    - ``len(live["entries"])`` is unchanged
    - entries that already have EN or sections keep their existing non-empty fields
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

        donor = pulled_by_slug.get(slug)
        if donor is None:
            stats.skipped_pulled_missing_slug += 1
            continue

        if entry_has_translation(entry):
            stats.skipped_live_has_translation += 1
        else:
            donor_translation = entry_translation(donor)
            if donor_translation is None:
                stats.skipped_pulled_lacks_translation += 1
            else:
                enrichment = entry.get("enrichment")
                if not isinstance(enrichment, dict):
                    enrichment = {}
                    entry["enrichment"] = enrichment
                enrichment["translation"] = copy.deepcopy(donor_translation)
                _add_source(enrichment, donor_translation.get("source"))
                stats.filled += 1
                stats.filled_slugs.append(slug)

        donor_sections = donor.get("sections")
        if isinstance(donor_sections, dict):
            live_sections = entry.get("sections")
            if not isinstance(live_sections, dict):
                live_sections = {}
                entry["sections"] = live_sections
            for sec_name, sec_val in donor_sections.items():
                if sec_val and not live_sections.get(sec_name):
                    live_sections[sec_name] = copy.deepcopy(sec_val)
                    stats.filled_sections += 1
                    stats.filled_layer_sections[sec_name] = (
                        stats.filled_layer_sections.get(sec_name, 0) + 1
                    )
                    sec_src = sec_val.get("source") if isinstance(sec_val, dict) else None
                    enrichment = entry.get("enrichment")
                    if not isinstance(enrichment, dict):
                        enrichment = {}
                        entry["enrichment"] = enrichment
                    _add_source(enrichment, sec_src)

        donor_enr = donor.get("enrichment") if isinstance(donor.get("enrichment"), dict) else {}
        live_enr = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}

        donor_att = donor_enr.get("literary_attestation")
        if donor_att and not live_enr.get("literary_attestation"):
            if not isinstance(entry.get("enrichment"), dict):
                entry["enrichment"] = {}
                live_enr = entry["enrichment"]
            live_enr["literary_attestation"] = copy.deepcopy(donor_att)
            stats.filled_literary_attestation += 1

        donor_morph = donor_enr.get("morphology")
        if donor_morph and not live_enr.get("morphology"):
            if not isinstance(entry.get("enrichment"), dict):
                entry["enrichment"] = {}
                live_enr = entry["enrichment"]
            live_enr["morphology"] = copy.deepcopy(donor_morph)
            stats.filled_morphology += 1

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
    """Count entries whose previously non-empty target fields changed after the merge."""
    modified = 0
    for slug, before_entry in before_by_slug.items():
        after_entry = after_by_slug.get(slug)
        if after_entry is None:
            modified += 1
            continue

        before_tr = entry_translation(before_entry)
        if before_tr is not None:
            after_tr = entry_translation(after_entry)
            if after_tr != before_tr:
                modified += 1
                continue

        before_sec = before_entry.get("sections")
        if isinstance(before_sec, dict):
            after_sec = after_entry.get("sections")
            if not isinstance(after_sec, dict):
                modified += 1
                continue
            sec_modified = False
            for sec_key, sec_val in before_sec.items():
                if sec_val and after_sec.get(sec_key) != sec_val:
                    modified += 1
                    sec_modified = True
                    break
            if sec_modified:
                continue

        before_enr = before_entry.get("enrichment")
        if isinstance(before_enr, dict):
            after_enr = after_entry.get("enrichment")
            if not isinstance(after_enr, dict):
                modified += 1
                continue
            if before_enr.get("morphology") and after_enr.get("morphology") != before_enr.get("morphology"):
                modified += 1
                continue
            if (
                before_enr.get("literary_attestation")
                and after_enr.get("literary_attestation") != before_enr.get("literary_attestation")
            ):
                modified += 1
                continue
    return modified


def anchor_loss_slugs(
    before_by_slug: dict[str, dict[str, Any]],
    after_by_slug: dict[str, dict[str, Any]],
) -> list[str]:
    """Return slugs that had a learner English anchor before the merge but lost it.

    The old-gate thin count (``thin_old_gate_entries``) counts entries that are
    enrichment-gated but lack a learner English anchor. An additive layer fill
    (morphology, literary_attestation, layer sections) on a previously-empty
    entry can legitimately raise that raw count without ever touching an
    existing anchor -- that is intentional residual-policy behavior, not a
    regression. Anchor *loss* -- an entry that had a learner English anchor
    before the merge and no longer has one after -- is the actual invariant
    violation, since it can only happen if the merge stripped or replaced a
    non-empty translation/gloss/meaning field.
    """
    lost: list[str] = []
    for slug, before_entry in before_by_slug.items():
        if not has_learner_english_anchor(before_entry):
            continue
        after_entry = after_by_slug.get(slug)
        if after_entry is None or not has_learner_english_anchor(after_entry):
            lost.append(slug)
    return lost


def build_merge_report(
    live: dict[str, Any],
    pulled: dict[str, Any],
    *,
    stamp_generated_at: bool = True,
) -> dict[str, Any]:
    """Run the merge in place on ``live`` and return the full stats/invariant payload.

    No file I/O -- callers (``main`` and tests) own reading/writing the manifest.
    """
    thin_before = len(thin_old_gate_entries(live))
    before_by_slug = {slug: copy.deepcopy(entry) for slug, entry in _slug_index(live).items()}
    stats = merge_translation_delta(live, pulled, stamp_generated_at=stamp_generated_at)
    after_by_slug = _slug_index(live)
    thin_after = len(thin_old_gate_entries(live))

    overwrite_proof = prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug)
    lost_slugs = anchor_loss_slugs(before_by_slug, after_by_slug)
    old_gate_anchor_loss = len(lost_slugs)
    # The hard gate is anchor LOSS, not the raw thin count: an additive layer
    # fill on a previously-empty entry is expected to raise
    # old_gate_no_english_anchor_after (residual-policy fills onto UA-gloss-
    # only lemmas), but must never strip an anchor an entry already had.
    old_gate_not_rising = old_gate_anchor_loss == 0

    payload = stats.as_dict()
    payload["overwrite_proof_modified_nonempty_en"] = overwrite_proof
    payload["old_gate_no_english_anchor_before"] = thin_before
    payload["old_gate_no_english_anchor_after"] = thin_after
    payload["old_gate_anchor_loss"] = old_gate_anchor_loss
    payload["old_gate_not_rising"] = old_gate_not_rising
    if lost_slugs:
        payload["old_gate_anchor_loss_slugs_sample"] = lost_slugs[:50]
    payload["missing_translation_after"] = sum(
        1 for entry in (live.get("entries") or []) if isinstance(entry, dict) and not entry_has_translation(entry)
    )

    if len(payload["filled_slugs"]) > 50:
        payload["filled_slugs_sample"] = payload["filled_slugs"][:50]
        payload["filled_slugs"] = []

    return payload


def _read_local_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Additive slug-keyed merge of EN translation cards and layer sections from a pulled "
            "manifest onto the live Atlas catalog (no entry add/drop, no non-empty overwrite)."
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

    initial_live_bytes = live_path.read_bytes() if live_path.exists() else b""
    initial_live_sha = hashlib.sha256(initial_live_bytes).hexdigest()

    if args.local_live or live_path.resolve() != DEFAULT_MANIFEST.resolve():
        live = _read_local_manifest(live_path)
    else:
        live = load_manifest(live_path)
    pulled = _read_local_manifest(pulled_path)

    payload = build_merge_report(live, pulled, stamp_generated_at=not args.no_stamp_generated_at)
    overwrite_proof = payload["overwrite_proof_modified_nonempty_en"]
    old_gate_anchor_loss = payload["old_gate_anchor_loss"]
    old_gate_not_rising = payload["old_gate_not_rising"]

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.report is not None:
        report_path = args.report if args.report.is_absolute() else ROOT / args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if overwrite_proof != 0 or not old_gate_not_rising:
        print(
            json.dumps(
                {
                    "error": "merge_invariant_violation",
                    "overwrite_proof_modified_nonempty_en": overwrite_proof,
                    "old_gate_anchor_loss": old_gate_anchor_loss,
                    "old_gate_not_rising": old_gate_not_rising,
                    "wrote": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    if args.write:
        entry_count_after = payload["live_entry_count_after"]
        current_live_bytes = live_path.read_bytes() if live_path.exists() else b""
        current_live_sha = hashlib.sha256(current_live_bytes).hexdigest()
        if current_live_sha != initial_live_sha:
            print("CAS: live manifest moved during merge; re-fetching live manifest and re-evaluating merge...", file=sys.stderr)
            if args.local_live or live_path.resolve() != DEFAULT_MANIFEST.resolve():
                live = _read_local_manifest(live_path)
            else:
                live = load_manifest(live_path)
            before_by_slug = {slug: copy.deepcopy(entry) for slug, entry in _slug_index(live).items()}
            stats = merge_translation_delta(live, pulled, stamp_generated_at=not args.no_stamp_generated_at)
            after_by_slug = _slug_index(live)
            entry_count_after = stats.live_entry_count_after
            overwrite_proof = prove_no_nonempty_en_overwrites(before_by_slug, after_by_slug)
            if overwrite_proof != 0:
                print(
                    json.dumps(
                        {"error": "cas_retry_overwrite_proof_failed", "overwrite_proof": overwrite_proof},
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                return 1

        if live_path.resolve() == DEFAULT_MANIFEST.resolve():
            sync_embedded_fingerprint_from_sidecar(live)
        write_manifest(live_path, live)
        print(json.dumps({"wrote": str(live_path), "entries": entry_count_after}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

