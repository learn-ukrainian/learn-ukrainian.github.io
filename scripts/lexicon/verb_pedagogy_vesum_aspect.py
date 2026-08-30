#!/usr/bin/env python3
"""VESUM verb aspect + existing opposite-aspect xref pedagogy fill for Atlas (#7471).

Applies ``enrichment.verb_pedagogy.aspect`` (``"imperfective"`` / ``"perfective"``)
to every Atlas ``pos: "verb"`` entry whose VESUM analyses agree on one aspect --
this reuses ``scripts.lexicon.enrich_manifest._verb_aspect`` and never
reimplements the VESUM tag lookup. Verbs VESUM has no opinion on (two-aspect
verbs, ambiguous forms, VESUM misses) are left alone: no aspect claim without
a source.

Also fills ``enrichment.verb_pedagogy.aspect_partner`` when a partner is
already sourced, but from exactly two places -- never a new lookup:
1. Anna Ohoiko's headword pair, set earlier by
   ``scripts.lexicon.ohoiko_quality_enrichment.apply_ohoiko_quality_enrichment``.
   That value is never overwritten here.
2. The entry's own СУМ-20/ВТС definition-card cross-reference. When a card's
   body is a resolved «докон./недок. до X» (or bare «див. X») pointer --
   ``enrich_manifest._resolve_definition_xref`` already records this as
   ``card["cross_reference"]["target"]`` at build time -- and X's VESUM aspect
   disagrees with this entry's, the cross-reference IS an aspect-pair pointer.

Deliberately out of scope (operator #7471): no new stems, no government
parsing beyond what the Anna pass already sourced, no invented partners for
verbs with neither an Anna pair nor a dictionary cross-reference.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.enrich_manifest import _verb_aspect

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

ASPECT_LABELS = {"imperf": "imperfective", "perf": "perfective"}
SOURCE_LABEL_VESUM = "VESUM"


def _aspect_label(lemma: str) -> str | None:
    """VESUM aspect for one lemma as the learner-facing label, else ``None``."""
    tag = _verb_aspect(lemma)
    return ASPECT_LABELS.get(tag) if tag else None


def _xref_sourced_partner(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Recover an aspect partner from an existing dictionary cross-reference.

    Never a new lookup: only reads ``cross_reference`` values that
    ``enrich_manifest._resolve_definition_xref`` already attached to this
    entry's own ``definition_cards`` at build time.
    """
    lemma = str(entry.get("lemma") or "")
    lemma_aspect = _verb_aspect(lemma)
    if not lemma_aspect:
        return None
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    for card in enrichment.get("definition_cards") or []:
        if not isinstance(card, dict):
            continue
        xref = card.get("cross_reference")
        target = str(xref.get("target") or "") if isinstance(xref, dict) else ""
        if not target:
            continue
        target_aspect = _verb_aspect(target)
        if target_aspect and target_aspect != lemma_aspect:
            return {"lemma": target, "source": str(card.get("source") or "dictionary cross-reference")}
    return None


def apply_vesum_verb_aspect(manifest: dict[str, Any]) -> dict[str, int]:
    """Apply VESUM aspect (+ sourced partner fallback) to every Atlas verb entry."""
    entries = manifest.get("entries", [])
    entries_by_lemma = {e["lemma"]: e for e in entries if isinstance(e, dict) and "lemma" in e}

    verbs_total = 0
    aspect_known = 0
    aspect_applied = 0
    aspect_partner_from_xref = 0

    for entry in entries:
        if not isinstance(entry, dict) or entry.get("pos") != "verb":
            continue
        verbs_total += 1
        lemma = str(entry.get("lemma") or "")
        if not lemma:
            continue
        aspect_label = _aspect_label(lemma)
        if aspect_label is None:
            continue
        aspect_known += 1

        enrichment = entry.setdefault("enrichment", {})
        if enrichment is None:
            enrichment = {}
            entry["enrichment"] = enrichment
        verb_pedagogy = enrichment.setdefault("verb_pedagogy", {})
        if verb_pedagogy is None:
            verb_pedagogy = {}
            enrichment["verb_pedagogy"] = verb_pedagogy

        if verb_pedagogy.get("aspect") != aspect_label:
            verb_pedagogy["aspect"] = aspect_label
            aspect_applied += 1

        if "aspect_partner" not in verb_pedagogy:
            partner = _xref_sourced_partner(entry)
            if partner:
                target_entry = entries_by_lemma.get(partner["lemma"])
                if target_entry is not None and target_entry.get("url_slug"):
                    partner["url_slug"] = target_entry["url_slug"]
                verb_pedagogy["aspect_partner"] = partner
                aspect_partner_from_xref += 1

        sources = set(enrichment.get("sources") or [])
        sources.add(SOURCE_LABEL_VESUM)
        enrichment["sources"] = sorted(sources)

    return {
        "verbs_total": verbs_total,
        "verbs_aspect_known": aspect_known,
        "aspect_applied": aspect_applied,
        "aspect_partner_from_xref": aspect_partner_from_xref,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the VESUM verb-aspect pedagogy fill."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH, help="Path to manifest JSON")
    parser.add_argument("--write", action="store_true", help="Write changes to manifest file")
    args = parser.parse_args(argv)

    from scripts.lexicon.manifest_io import load_manifest, write_manifest

    manifest = load_manifest(args.manifest)
    stats = apply_vesum_verb_aspect(manifest)
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.write:
        write_manifest(args.manifest, manifest)
        print(f"Wrote updated manifest to {args.manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
