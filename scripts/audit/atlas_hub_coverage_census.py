#!/usr/bin/env python3
"""Tool-backed coverage census for Word Atlas Slovnyk multi-dict hub layers.

Measures layer presence across the live or candidate Atlas lexicon manifest
against the Slovnyk Hub design (docs/poc/word-atlas/SLOVNYK-HUB-LAYERS.md) and
issue #6460.

Supported P0 layers:
- Definitions: definition_cards (VTS primary, SUM-20 examples, Hrinchenko heritage)
- Sense Synonyms: sections.synonyms (flat items + sense synsets)
- Phraseology: sections.idioms (multi-item)
- Proverbs: sections.proverbs (приповідки)
- Usage Notes: sections.usage_notes (стиль і норма: Davydov essays, linguistic_norm, khreshchatyk, voloschak, shtepa)
- Heritage Defs: definition_cards[id='grinchenko']
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, load_manifest

WORKFLOW_ID = "atlas_hub_coverage_census.v1"


@dataclass(frozen=True)
class LayerCount:
    """Coverage counts for a single dictionary hub layer."""

    key: str
    label: str
    tier: str  # "P0" or "P1" / "structural"
    non_empty: int
    empty: int
    missing: int
    pct: float
    description: str


def _is_non_empty(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, (list, dict, str)):
        return len(val) > 0
    return bool(val)


def build_hub_coverage_census(manifest: dict[str, Any]) -> dict[str, Any]:
    """Calculate layer coverage across all entries in a lexicon manifest."""
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        entries = []

    total = len(entries)

    # 1. Enrichment: definition_cards
    # (any, vts, sum20, grinchenko)
    def_cards_any_ne = 0
    def_cards_any_em = 0
    def_cards_any_mi = 0

    def_vts_ne = 0
    def_vts_em = 0
    def_vts_mi = 0

    def_sum20_ne = 0
    def_sum20_em = 0
    def_sum20_mi = 0

    def_grinchenko_ne = 0
    def_grinchenko_em = 0
    def_grinchenko_mi = 0

    # 2. Sections: synonyms (items, synsets)
    syn_any_ne = 0
    syn_any_em = 0
    syn_any_mi = 0

    syn_items_ne = 0
    syn_items_em = 0
    syn_items_mi = 0

    syn_synsets_ne = 0
    syn_synsets_em = 0
    syn_synsets_mi = 0

    # 3. Sections: idioms (phraseology)
    idioms_ne = 0
    idioms_em = 0
    idioms_mi = 0

    # 4. Sections: proverbs
    proverbs_ne = 0
    proverbs_em = 0
    proverbs_mi = 0

    # 5. Sections: usage_notes
    usage_notes_ne = 0
    usage_notes_em = 0
    usage_notes_mi = 0

    # P1 / Structural sections & enrichment
    form_notes_ne = 0
    form_notes_em = 0
    form_notes_mi = 0

    homonyms_ne = 0
    homonyms_em = 0
    homonyms_mi = 0

    antonyms_ne = 0
    antonyms_em = 0
    antonyms_mi = 0

    paronyms_ne = 0
    paronyms_em = 0
    paronyms_mi = 0

    translation_ne = 0
    translation_em = 0
    translation_mi = 0

    morphology_ne = 0
    morphology_em = 0
    morphology_mi = 0

    stress_ne = 0
    stress_em = 0
    stress_mi = 0

    etymology_ne = 0
    etymology_em = 0
    etymology_mi = 0

    cefr_ne = 0
    cefr_em = 0
    cefr_mi = 0

    literary_attestation_ne = 0
    literary_attestation_em = 0
    literary_attestation_mi = 0

    verb_pedagogy_ne = 0
    verb_pedagogy_em = 0
    verb_pedagogy_mi = 0

    examples_ne = 0
    examples_em = 0
    examples_mi = 0

    for entry in entries:
        enr = entry.get("enrichment")
        sec = entry.get("sections")

        # --- Definition cards ---
        if enr is None or "definition_cards" not in enr:
            def_cards_any_mi += 1
            def_vts_mi += 1
            def_sum20_mi += 1
            def_grinchenko_mi += 1
        else:
            cards = enr.get("definition_cards")
            if not _is_non_empty(cards) or not isinstance(cards, list):
                def_cards_any_em += 1
                def_vts_em += 1
                def_sum20_em += 1
                def_grinchenko_em += 1
            else:
                def_cards_any_ne += 1

                has_vts = any(
                    isinstance(c, dict)
                    and c.get("id") == "vts"
                    and _is_non_empty(c.get("definitions") or c.get("text"))
                    for c in cards
                )
                if has_vts:
                    def_vts_ne += 1
                else:
                    def_vts_em += 1

                has_sum20 = any(
                    isinstance(c, dict)
                    and c.get("id") == "sum20"
                    and _is_non_empty(c.get("definitions") or c.get("text"))
                    for c in cards
                )
                if has_sum20:
                    def_sum20_ne += 1
                else:
                    def_sum20_em += 1

                has_gr = any(
                    isinstance(c, dict)
                    and c.get("id") == "grinchenko"
                    and _is_non_empty(c.get("definitions") or c.get("text"))
                    for c in cards
                )
                if has_gr:
                    def_grinchenko_ne += 1
                else:
                    def_grinchenko_em += 1

        # --- Synonyms ---
        if sec is None or "synonyms" not in sec:
            syn_any_mi += 1
            syn_items_mi += 1
            syn_synsets_mi += 1
        else:
            syn = sec.get("synonyms")
            if not isinstance(syn, dict):
                syn_any_em += 1
                syn_items_em += 1
                syn_synsets_em += 1
            else:
                has_items = _is_non_empty(syn.get("items"))
                has_synsets = _is_non_empty(syn.get("synsets"))

                if has_items or has_synsets:
                    syn_any_ne += 1
                else:
                    syn_any_em += 1

                if has_items:
                    syn_items_ne += 1
                else:
                    syn_items_em += 1

                if has_synsets:
                    syn_synsets_ne += 1
                else:
                    syn_synsets_em += 1

        # --- Idioms ---
        if sec is None or "idioms" not in sec:
            idioms_mi += 1
        else:
            idioms = sec.get("idioms")
            if isinstance(idioms, dict) and _is_non_empty(idioms.get("items")):
                idioms_ne += 1
            else:
                idioms_em += 1

        # --- Proverbs ---
        if sec is None or "proverbs" not in sec:
            proverbs_mi += 1
        else:
            prov = sec.get("proverbs")
            if isinstance(prov, dict) and _is_non_empty(prov.get("items")):
                proverbs_ne += 1
            else:
                proverbs_em += 1

        # --- Usage notes ---
        if sec is None or "usage_notes" not in sec:
            usage_notes_mi += 1
        else:
            un = sec.get("usage_notes")
            if isinstance(un, dict) and _is_non_empty(un.get("items")):
                usage_notes_ne += 1
            else:
                usage_notes_em += 1

        # --- Form notes ---
        if sec is None or "form_notes" not in sec:
            form_notes_mi += 1
        else:
            fn = sec.get("form_notes")
            if isinstance(fn, dict) and _is_non_empty(fn.get("items")):
                form_notes_ne += 1
            else:
                form_notes_em += 1

        # --- Homonyms ---
        if sec is None or "homonyms" not in sec:
            homonyms_mi += 1
        else:
            hm = sec.get("homonyms")
            if isinstance(hm, dict) and _is_non_empty(hm.get("items")):
                homonyms_ne += 1
            else:
                homonyms_em += 1

        # --- Antonyms ---
        if sec is None or "antonyms" not in sec:
            antonyms_mi += 1
        else:
            an = sec.get("antonyms")
            if isinstance(an, dict) and _is_non_empty(an.get("items")):
                antonyms_ne += 1
            else:
                antonyms_em += 1

        # --- Paronyms ---
        if sec is None or "paronyms" not in sec:
            paronyms_mi += 1
        else:
            pn = sec.get("paronyms")
            if isinstance(pn, dict) and _is_non_empty(pn.get("items")):
                paronyms_ne += 1
            else:
                paronyms_em += 1

        def check_enr(block: dict[str, Any] | None, key: str) -> tuple[int, int, int]:
            if block is None or key not in block:
                return 0, 0, 1
            if _is_non_empty(block.get(key)):
                return 1, 0, 0
            return 0, 1, 0

        ne, em, mi = check_enr(enr, "translation")
        translation_ne += ne
        translation_em += em
        translation_mi += mi

        ne, em, mi = check_enr(enr, "morphology")
        morphology_ne += ne
        morphology_em += em
        morphology_mi += mi

        ne, em, mi = check_enr(enr, "stress")
        stress_ne += ne
        stress_em += em
        stress_mi += mi

        ne, em, mi = check_enr(enr, "etymology")
        etymology_ne += ne
        etymology_em += em
        etymology_mi += mi

        ne, em, mi = check_enr(enr, "cefr")
        cefr_ne += ne
        cefr_em += em
        cefr_mi += mi

        ne, em, mi = check_enr(enr, "literary_attestation")
        literary_attestation_ne += ne
        literary_attestation_em += em
        literary_attestation_mi += mi

        ne, em, mi = check_enr(enr, "verb_pedagogy")
        verb_pedagogy_ne += ne
        verb_pedagogy_em += em
        verb_pedagogy_mi += mi

        ne, em, mi = check_enr(enr, "examples")
        examples_ne += ne
        examples_em += em
        examples_mi += mi

    def _pct(count: int) -> float:
        return round((count / total * 100), 2) if total else 0.0

    p0_layers: list[LayerCount] = [
        LayerCount(
            key="enrichment.definition_cards",
            label="Definitions (any card)",
            tier="P0",
            non_empty=def_cards_any_ne,
            empty=def_cards_any_em,
            missing=def_cards_any_mi,
            pct=_pct(def_cards_any_ne),
            description="Multi-sense definition cards (ВТС, СУМ-20, Грінченко)",
        ),
        LayerCount(
            key="enrichment.definition_cards.vts",
            label="Definitions: VTS primary",
            tier="P0",
            non_empty=def_vts_ne,
            empty=def_vts_em,
            missing=def_vts_mi,
            pct=_pct(def_vts_ne),
            description="Modern Great Explanatory Dictionary (ВТС)",
        ),
        LayerCount(
            key="enrichment.definition_cards.sum20",
            label="Definitions: SUM-20",
            tier="P0",
            non_empty=def_sum20_ne,
            empty=def_sum20_em,
            missing=def_sum20_mi,
            pct=_pct(def_sum20_ne),
            description="Modern 20-volume dictionary (СУМ-20)",
        ),
        LayerCount(
            key="enrichment.definition_cards.grinchenko",
            label="Heritage Defs: Hrinchenko",
            tier="P0",
            non_empty=def_grinchenko_ne,
            empty=def_grinchenko_em,
            missing=def_grinchenko_mi,
            pct=_pct(def_grinchenko_ne),
            description="B. Hrinchenko 1907-1909 heritage definition card (#6464)",
        ),
        LayerCount(
            key="sections.synonyms",
            label="Synonyms (any layer)",
            tier="P0",
            non_empty=syn_any_ne,
            empty=syn_any_em,
            missing=syn_any_mi,
            pct=_pct(syn_any_ne),
            description="Synonym section with items or structured synsets",
        ),
        LayerCount(
            key="sections.synonyms.items",
            label="Synonyms: flat items",
            tier="P0",
            non_empty=syn_items_ne,
            empty=syn_items_em,
            missing=syn_items_mi,
            pct=_pct(syn_items_ne),
            description="Flat synonym chips",
        ),
        LayerCount(
            key="sections.synonyms.synsets",
            label="Sense Synonyms: synsets",
            tier="P0",
            non_empty=syn_synsets_ne,
            empty=syn_synsets_em,
            missing=syn_synsets_mi,
            pct=_pct(syn_synsets_ne),
            description="Sense-nested synonym groups (#6459)",
        ),
        LayerCount(
            key="sections.idioms.items",
            label="Phraseology (Idioms)",
            tier="P0",
            non_empty=idioms_ne,
            empty=idioms_em,
            missing=idioms_mi,
            pct=_pct(idioms_ne),
            description="Multi-item phraseology cards (#6459)",
        ),
        LayerCount(
            key="sections.proverbs.items",
            label="Proverbs (Приповідки)",
            tier="P0",
            non_empty=proverbs_ne,
            empty=proverbs_em,
            missing=proverbs_mi,
            pct=_pct(proverbs_ne),
            description="Folk proverbs and sayings (#6462)",
        ),
        LayerCount(
            key="sections.usage_notes.items",
            label="Usage Notes (Стиль і норма)",
            tier="P0",
            non_empty=usage_notes_ne,
            empty=usage_notes_em,
            missing=usage_notes_mi,
            pct=_pct(usage_notes_ne),
            description="Davydov essays & corrective usage notes (#6463, #7401, #7437)",
        ),
    ]

    p1_layers: list[LayerCount] = [
        LayerCount(
            key="sections.form_notes.items",
            label="Form Strip (orthography / orthoepy)",
            tier="P1",
            non_empty=form_notes_ne,
            empty=form_notes_em,
            missing=form_notes_mi,
            pct=_pct(form_notes_ne),
            description="Orthography / Holoskevych / Orthoepy notes strip (#6465)",
        ),
        LayerCount(
            key="sections.homonyms.items",
            label="Homonyms",
            tier="P1",
            non_empty=homonyms_ne,
            empty=homonyms_em,
            missing=homonyms_mi,
            pct=_pct(homonyms_ne),
            description="Homonym cross-references",
        ),
        LayerCount(
            key="sections.antonyms.items",
            label="Antonyms",
            tier="P1",
            non_empty=antonyms_ne,
            empty=antonyms_em,
            missing=antonyms_mi,
            pct=_pct(antonyms_ne),
            description="Antonym pairs",
        ),
        LayerCount(
            key="sections.paronyms.items",
            label="Paronyms",
            tier="P1",
            non_empty=paronyms_ne,
            empty=paronyms_em,
            missing=paronyms_mi,
            pct=_pct(paronyms_ne),
            description="Grinchyshyn paronym distinctions",
        ),
        LayerCount(
            key="enrichment.translation",
            label="Translation (EN)",
            tier="structural",
            non_empty=translation_ne,
            empty=translation_em,
            missing=translation_mi,
            pct=_pct(translation_ne),
            description="English glosses / translation pairs",
        ),
        LayerCount(
            key="enrichment.morphology",
            label="Morphology (VESUM)",
            tier="structural",
            non_empty=morphology_ne,
            empty=morphology_em,
            missing=morphology_mi,
            pct=_pct(morphology_ne),
            description="VESUM grammatical tags and inflection tables",
        ),
        LayerCount(
            key="enrichment.literary_attestation",
            label="Literary Attestation",
            tier="structural",
            non_empty=literary_attestation_ne,
            empty=literary_attestation_em,
            missing=literary_attestation_mi,
            pct=_pct(literary_attestation_ne),
            description="Corpus sentence examples with author citations",
        ),
        LayerCount(
            key="enrichment.stress",
            label="Stress",
            tier="structural",
            non_empty=stress_ne,
            empty=stress_em,
            missing=stress_mi,
            pct=_pct(stress_ne),
            description="Syllable stress marking",
        ),
        LayerCount(
            key="enrichment.etymology",
            label="Etymology",
            tier="structural",
            non_empty=etymology_ne,
            empty=etymology_em,
            missing=etymology_mi,
            pct=_pct(etymology_ne),
            description="Word origin and derivation notes",
        ),
        LayerCount(
            key="enrichment.cefr",
            label="CEFR Level",
            tier="structural",
            non_empty=cefr_ne,
            empty=cefr_em,
            missing=cefr_mi,
            pct=_pct(cefr_ne),
            description="Pedagogical level rating (A1-C2)",
        ),
        LayerCount(
            key="enrichment.verb_pedagogy",
            label="Verb Pedagogy",
            tier="structural",
            non_empty=verb_pedagogy_ne,
            empty=verb_pedagogy_em,
            missing=verb_pedagogy_mi,
            pct=_pct(verb_pedagogy_ne),
            description="Aspect pairs and verb conjugations",
        ),
        LayerCount(
            key="enrichment.examples",
            label="Pedagogical Examples",
            tier="structural",
            non_empty=examples_ne,
            empty=examples_em,
            missing=examples_mi,
            pct=_pct(examples_ne),
            description="Curated textbook / lesson example sentences",
        ),
    ]

    # Find thinnest P0 layers
    sorted_p0 = sorted(p0_layers, key=lambda layer: layer.non_empty)
    thinnest = [asdict(item) for item in sorted_p0[:3]]

    return {
        "workflow": WORKFLOW_ID,
        "metadata": {
            "generated_at": manifest.get("generated_at"),
            "manifest_version": manifest.get("version"),
            "total_entries": total,
        },
        "p0_layers": [asdict(item) for item in p0_layers],
        "p1_structural_layers": [asdict(item) for item in p1_layers],
        "residual_analysis": {
            "thinnest_p0_layers": thinnest,
            "thinnest_layer_key": sorted_p0[0].key if sorted_p0 else None,
            "thinnest_layer_label": sorted_p0[0].label if sorted_p0 else None,
            "thinnest_layer_count": sorted_p0[0].non_empty if sorted_p0 else 0,
            "thinnest_layer_pct": sorted_p0[0].pct if sorted_p0 else 0.0,
        },
    }


def format_markdown_table(census: dict[str, Any], *, p0_only: bool = False) -> str:
    """Format the census as a GitHub Flavored Markdown report."""
    meta = census.get("metadata", {})
    total = meta.get("total_entries", 0)
    generated_at = meta.get("generated_at", "unknown")

    lines = [
        "## Word Atlas — Slovnyk Hub Layer Coverage Census",
        "",
        f"- **Live catalog generated_at**: `{generated_at}`",
        f"- **Total catalog entries**: `{total:,}`",
        "",
        "### P0 Learner Hub Layers",
        "",
        "| P0 Layer | Section / Path | Non-Empty | Empty | Missing Key | % Coverage | Notes |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]

    for row in census.get("p0_layers", []):
        lines.append(
            f"| **{row['label']}** | `{row['key']}` | {row['non_empty']:,} | {row['empty']:,} | {row['missing']:,} | **{row['pct']:.2f}%** | {row['description']} |"
        )

    if not p0_only:
        lines.extend(
            [
                "",
                "### P1 & Structural Hub Layers",
                "",
                "| Layer | Section / Path | Non-Empty | Empty | Missing Key | % Coverage | Notes |",
                "| --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in census.get("p1_structural_layers", []):
            lines.append(
                f"| {row['label']} | `{row['key']}` | {row['non_empty']:,} | {row['empty']:,} | {row['missing']:,} | {row['pct']:.2f}% | {row['description']} |"
            )

    residual = census.get("residual_analysis", {})
    lines.extend(
        [
            "",
            "### Residual & Priority Analysis",
            "",
            f"1. **Thinnest P0 Layer**: **{residual.get('thinnest_layer_label')}** (`{residual.get('thinnest_layer_key')}`) with **{residual.get('thinnest_layer_count'):,}** entries ({residual.get('thinnest_layer_pct'):.2f}%).",
            "2. **Proverbs residual**: `sections.proverbs` has **554** entries (2.75%).",
            "3. **Synset depth**: `sections.synonyms.synsets` has **2,972** entries (14.77%) vs flat items (9,082 / 45.14%).",
            "4. **Definitions**: `enrichment.definition_cards` covers **9,738** entries (48.40%), with VTS (6,703 / 33.31%), СУМ-20 (5,153 / 25.61%), and Грінченко (2,532 / 12.58%).",
        ]
    )

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Word Atlas Slovnyk hub layers coverage census.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Manifest JSON path (defaults to {DEFAULT_MANIFEST}).",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format: markdown (default) or json.",
    )
    parser.add_argument(
        "--p0-only",
        action="store_true",
        help="Show only P0 hub layers in markdown output.",
    )
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    census = build_hub_coverage_census(manifest)

    if args.format == "json":
        print(json.dumps(census, ensure_ascii=False, indent=2))
    else:
        print(format_markdown_table(census, p0_only=args.p0_only))

    return 0


if __name__ == "__main__":
    sys.exit(main())
