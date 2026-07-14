#!/usr/bin/env python3
"""#M-11 verify-before-promote gate for the Word Atlas lexicon manifest.

Run AFTER ``enrich_manifest.py`` regenerates ``site/src/data/lexicon-manifest.json``
and BEFORE committing it (the commit auto-deploys). Deterministic gates alone are
NECESSARY BUT NOT SUFFICIENT (memory #M-11): this script runs the reproducible
structural hazard scans + a coverage report + a sample dump for human/LLM eyeball.

Exit code 0 = clean (still eyeball the sample); 2 = a structural hazard OR a §8
conformance gate fired (do NOT commit). The §8 conformance pass was added after
#3124: the structural hazard scan alone is NECESSARY BUT NOT SUFFICIENT — it gave
a false-clean on the re-enrich whose ``(etymology of base form X)`` suffix turned
the real ``test_atlas_conformance`` gate RED on main. This gate now runs the same
``validate_atlas_conformance.validate()`` the required CI test runs, so the
verify-before-promote step catches what previously only detonated post-merge.

Hazard philosophy — STRUCTURAL over semantic:
  The reliable, false-positive-free hazards are STRUCTURAL: HTML-entity leaks,
  gloss chunk-id leaks, empty-but-present sections. A token *stoplist* for "junk
  synonyms" is deliberately MINIMAL and reserved for DEFINITIVELY cross-domain
  garbage (e.g. варити→"фальсифікувати"/"бариги", the auto-translated WordNet
  noise #3092 removed). It must NOT be used to reject dialectal/archaic synonyms:
  e.g. шлях→кам'яниця and річка→звір LOOK wrong but are authoritative DIALECTAL
  road/stream terms (Караванський marks them "д."/"г."). Rejecting those would
  repeat the блискучий false-positive. When unsure, surface in the sample for a
  human call — do NOT add it to JUNK_SYNONYMS.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_VESUM = ROOT / "data" / "vesum.db"
DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"
DEFAULT_CURRICULUM = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
# Curated (lemma, section) retractions the shrink gate permits even without a
# gate-ran provenance marker (e.g. a manually-edited manifest). Co-located with this
# script so it is always present in worktrees (unlike gitignored data/).
DEFAULT_SHRINK_ALLOWLIST = ROOT / "scripts" / "lexicon" / "shrink_allowlist.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.manifest_io import GATE_REJECTED, load_manifest

# DEFINITIVELY cross-domain auto-translation junk that must never be a synonym.
# Keep MINIMAL (see module docstring) — only tokens with zero defensible sense
# overlap with any plausible lemma. NOT a place for dialectal/archaic terms.
JUNK_SYNONYMS: frozenset[str] = frozenset({
    "фальсифікувати",  # WordNet noise once attached to варити (#3092)
    "бариги",
    "барига",
})

_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);")
_CHUNK_RE = re.compile(r"_s\d{4}\b|\bchunk[_-]?id\b", re.IGNORECASE)


def _synonym_items(entry: dict) -> list[str]:
    syn = (entry.get("sections") or {}).get("synonyms") or {}
    out: list[str] = []
    for it in syn.get("items") or []:
        if isinstance(it, str):
            out.append(it)
        elif isinstance(it, dict) and it.get("text"):
            out.append(str(it["text"]))
    return out


def coverage(entries: list[dict]) -> dict[str, int]:
    def enr(e: dict, k: str) -> bool:
        return bool((e.get("enrichment") or {}).get(k))

    return {
        "entries": len(entries),
        "synonyms": sum(1 for e in entries if _synonym_items(e)),
        "wiki_reference": sum(1 for e in entries if e.get("wiki_reference")),
        "etymology": sum(1 for e in entries if enr(e, "etymology")),
        "definition_cards": sum(1 for e in entries if enr(e, "definition_cards")),
        "meaning": sum(1 for e in entries if enr(e, "meaning")),
        "pronunciation": sum(1 for e in entries if e.get("pronunciation")),
        "heritage_status": sum(1 for e in entries if e.get("heritage_status")),
    }


def hazards(manifest: dict, entries: list[dict]) -> dict[str, list]:
    junk: list[tuple[str, str]] = []
    for e in entries:
        for tok in _synonym_items(e):
            if tok.strip().casefold() in JUNK_SYNONYMS:
                junk.append((e.get("lemma", "?"), tok))

    raw = json.dumps(manifest, ensure_ascii=False)
    entity = sorted(set(_ENTITY_RE.findall(raw)))

    chunk = [
        e.get("lemma", "?")
        for e in entries
        if isinstance(e.get("gloss"), str) and _CHUNK_RE.search(e["gloss"])
    ]

    # Present-but-empty sections (structural breakage — a section dict with no items).
    empty_sections: list[str] = []
    for e in entries:
        for name, sec in (e.get("sections") or {}).items():
            if isinstance(sec, dict) and "items" in sec and not sec.get("items"):
                empty_sections.append(f"{e.get('lemma', '?')}:{name}")

    return {
        "junk_synonyms": junk,
        "html_entities": entity,
        "gloss_chunk_leaks": chunk,
        "empty_sections": empty_sections,
    }


def _section_item_count(section: object) -> int:
    """Number of rendered items in a section (0 for a missing/malformed section)."""
    if not isinstance(section, dict):
        return 0
    items = section.get("items")
    return len(items) if isinstance(items, list) else 0


def _load_shrink_allowlist(path: Path | None) -> set[tuple[str, str]]:
    """Load curated ``(lemma, section)`` retractions permitted to shrink (#5077).

    Shape (YAML)::

        version: 1
        kind: atlas_shrink_allowlist
        retractions:
          - lemma: ключ
            section: synonyms
            reason: WordNet auto-translation junk (джерело/живець wrong sense)
    """
    if not path or not path.exists():
        return set()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    allow: set[tuple[str, str]] = set()
    for row in data.get("retractions") or []:
        if isinstance(row, dict) and row.get("lemma") and row.get("section"):
            allow.add((str(row["lemma"]), str(row["section"])))
    return allow


def shrink_regressions(
    entries: list[dict],
    baseline_entries: list[dict],
    *,
    allowlist: set[tuple[str, str]],
) -> list[tuple[str, str, int, int]]:
    """Per-section item-count regressions vs the hydrated baseline (#5077).

    The NONEMPTY->EMPTY hazard scan catches only fully-stripped sections; it misses
    partial shrinks (1,748 on the 2026-07-13 go-live). A section that lost items — or
    vanished — relative to the baseline is a hazard UNLESS its retraction is justified:

      * the entry's ``gate_provenance`` records the gate ran and retracted (``rejected``
        — a quality win, e.g. WordNet auto-translation junk), or
      * the ``(lemma, section)`` pair is on the explicit curated allowlist.

    An unexplained regression is the offline gate-did-not-run strip/shrink bug and
    fails verification. Returns ``(lemma, section, baseline_count, current_count)``.
    """
    base_by_lemma = {str(e.get("lemma")): e for e in baseline_entries if e.get("lemma")}
    regressions: list[tuple[str, str, int, int]] = []
    for entry in entries:
        lemma = str(entry.get("lemma") or "")
        base = base_by_lemma.get(lemma)
        if not base:
            continue
        base_sections = base.get("sections")
        if not isinstance(base_sections, dict):
            continue
        provenance = entry.get("gate_provenance") or {}
        cur_sections = entry.get("sections") if isinstance(entry.get("sections"), dict) else {}
        for name, base_sec in base_sections.items():
            base_n = _section_item_count(base_sec)
            if base_n == 0:
                continue
            if _section_item_count(cur_sections.get(name)) >= base_n:
                continue
            if provenance.get(name) == GATE_REJECTED:
                continue  # gate ran and retracted — quality win (#5077 design pt 4)
            if (lemma, name) in allowlist:
                continue  # curated intended retraction
            regressions.append((lemma, name, base_n, _section_item_count(cur_sections.get(name))))
    return regressions


def conformance(
    manifest: dict,
    *,
    curriculum_path: Path = DEFAULT_CURRICULUM,
    vesum_path: Path = DEFAULT_VESUM,
    sources_path: Path = DEFAULT_SOURCES_DB,
) -> list:
    """Run the deterministic §8 Atlas conformance gates on the manifest.

    Autopsy follow-up to #3124 (``fixture-only-feature-latent-gate-break``): the
    structural hazard scan is necessary but NOT sufficient. This runs the SAME
    ``validate()`` the required ``test_atlas_conformance`` CI check runs, so the
    verify-before-promote gate would have caught the kaikki-attribution RED before
    it ever reached main.

    Mirrors ``tests/test_atlas_conformance.py``: lemma↔VESUM membership is enforced
    only when ``data/vesum.db`` exists (967MB, gitignored). When it is absent ONLY
    the ``lemma_in_vesum`` gate is skipped; every other §8 gate still enforces.
    A VESUM miss is cross-checked against the heritage corpus (Грінченко/ЕСУМ via
    ``data/sources.db``) before flagging, so authentic VESUM-gap words are not
    false-flagged (#3211); absent sources.db → the curated allowlist fallback.
    """
    if str(ROOT) not in sys.path:  # allow `python scripts/lexicon/verify_manifest.py`
        sys.path.insert(0, str(ROOT))
    from scripts.audit.validate_atlas_conformance import validate

    curriculum = (
        yaml.safe_load(curriculum_path.read_text(encoding="utf-8"))
        if curriculum_path.exists()
        else {}
    )
    # Pass paths, not opened lookups: validate() opens read-only VESUM/heritage
    # lookups and closes them in its finally block.
    return validate(
        manifest,
        vesum=vesum_path if vesum_path.exists() else None,
        curriculum=curriculum,
        heritage=sources_path if sources_path.exists() else None,
    )


def run(
    manifest_path: Path,
    sample: int,
    baseline_path: Path | None,
    *,
    run_conformance: bool = False,
    curriculum_path: Path = DEFAULT_CURRICULUM,
    vesum_path: Path = DEFAULT_VESUM,
    sources_path: Path = DEFAULT_SOURCES_DB,
    shrink_allowlist_path: Path | None = None,
) -> int:
    manifest = load_manifest(manifest_path)
    entries = manifest.get("entries", [])
    cov = coverage(entries)

    print(f"=== COVERAGE ({manifest_path.name}) ===")
    base_entries: list[dict] | None = None
    if baseline_path and baseline_path.exists():
        base = json.loads(baseline_path.read_text(encoding="utf-8"))
        base_entries = base.get("entries", [])
    base_cov = coverage(base_entries) if base_entries is not None else None
    for k, v in cov.items():
        delta = f"  (was {base_cov[k]})" if base_cov and base_cov.get(k) != v else ""
        print(f"  {k:18} {v}{delta}")

    haz = hazards(manifest, entries)
    print("\n=== HAZARD SCANS ===")
    for name, hits in haz.items():
        status = "CLEAN" if not hits else f"{len(hits)} — {hits[:8]}"
        print(f"  {name:18} {status}")

    # #5077 shrink gate: needs the hydrated baseline to compare per-section item counts.
    shrink: list[tuple[str, str, int, int]] = []
    if base_entries is not None:
        allowlist = _load_shrink_allowlist(shrink_allowlist_path)
        shrink = shrink_regressions(entries, base_entries, allowlist=allowlist)
        print("\n=== SHRINK GATE (per-section item count vs baseline, #5077) ===")
        if not shrink:
            print("  CLEAN — no unexplained section shrink")
        else:
            for lemma, name, base_n, cur_n in shrink[:20]:
                print(f"  {lemma:16} {name:12} {base_n} -> {cur_n}")
            if len(shrink) > 20:
                print(f"  ... and {len(shrink) - 20} more")

    if sample > 0:
        print(f"\n=== SAMPLE (every {max(1, len(entries) // sample)}th entry — eyeball for sense) ===")
        step = max(1, len(entries) // sample)
        for e in entries[::step][:sample]:
            syn = _synonym_items(e)
            enr = e.get("enrichment") or {}
            flags = "".join(
                c for c, ok in (("e", bool(enr.get("etymology"))), ("w", bool(e.get("wiki_reference"))))
                if ok
            )
            print(f"  {e.get('lemma', '?'):16} [{flags:2}] syn={syn[:8]}")

    conf: list = []
    if run_conformance:
        conf = conformance(
            manifest, curriculum_path=curriculum_path, vesum_path=vesum_path, sources_path=sources_path
        )
        vesum_note = "" if vesum_path.exists() else " (lemma_in_vesum skipped — no data/vesum.db)"
        print(f"\n=== CONFORMANCE (§8 atlas gates){vesum_note} ===")
        if not conf:
            print("  CLEAN — 0 violations")
        else:
            by_gate: dict[str, int] = {}
            for v in conf:
                by_gate[v.gate] = by_gate.get(v.gate, 0) + 1
            for gate, n in sorted(by_gate.items()):
                examples = [f"{v.lemma}: {v.detail}" for v in conf if v.gate == gate][:5]
                print(f"  {gate:28} {n} — {examples}")

    has_hazard = any(haz.values())
    has_conformance_fail = bool(conf)
    has_shrink = bool(shrink)
    failed = has_hazard or has_conformance_fail or has_shrink
    if failed:
        reasons = []
        if has_hazard:
            reasons.append("structural hazard")
        if has_conformance_fail:
            reasons.append(f"{len(conf)} conformance violation(s)")
        if has_shrink:
            reasons.append(f"{len(shrink)} unexplained section shrink(s)")
        verdict = f"{' + '.join(reasons)} — do NOT commit"
    else:
        verdict = "clean (eyeball the sample before commit)"
    print("\n=== VERDICT:", verdict, "===")
    return 2 if failed else 0


def main() -> int:
    p = argparse.ArgumentParser(description="Verify the Atlas lexicon manifest before promote (#M-11).")
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest JSON to verify.")
    p.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Prior (hydrated) manifest for coverage deltas AND the #5077 shrink gate.",
    )
    p.add_argument("--sample", type=int, default=12, help="How many spread-sampled entries to print (0 = none).")
    p.add_argument(
        "--skip-conformance",
        action="store_true",
        help="Skip the §8 conformance gates and run structural hazards only.",
    )
    p.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM, help="curriculum.yaml for cross-link gate.")
    p.add_argument("--vesum", type=Path, default=DEFAULT_VESUM, help="VESUM db for the lemma_in_vesum gate.")
    p.add_argument(
        "--sources",
        type=Path,
        default=DEFAULT_SOURCES_DB,
        help="sources.db for the Грінченко/ЕСУМ heritage fallback on VESUM-gap lemmas (#3211).",
    )
    p.add_argument(
        "--shrink-allowlist",
        type=Path,
        default=DEFAULT_SHRINK_ALLOWLIST,
        help="Curated (lemma, section) retractions the #5077 shrink gate permits.",
    )
    args = p.parse_args()
    return run(
        args.manifest,
        args.sample,
        args.baseline,
        run_conformance=not args.skip_conformance,
        curriculum_path=args.curriculum,
        vesum_path=args.vesum,
        sources_path=args.sources,
        shrink_allowlist_path=args.shrink_allowlist,
    )


if __name__ == "__main__":
    sys.exit(main())
