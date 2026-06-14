#!/usr/bin/env python3
"""#M-11 verify-before-promote gate for the Word Atlas lexicon manifest.

Run AFTER ``enrich_manifest.py`` regenerates ``site/src/data/lexicon-manifest.json``
and BEFORE committing it (the commit auto-deploys). Deterministic gates alone are
NECESSARY BUT NOT SUFFICIENT (memory #M-11): this script runs the reproducible
structural hazard scans + a coverage report + a sample dump for human/LLM eyeball.

Exit code 0 = no hazards (still eyeball the sample); 2 = a hazard fired (do NOT commit).

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

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

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


def run(manifest_path: Path, sample: int, baseline_path: Path | None) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    cov = coverage(entries)

    print(f"=== COVERAGE ({manifest_path.name}) ===")
    base_cov = None
    if baseline_path and baseline_path.exists():
        base = json.loads(baseline_path.read_text(encoding="utf-8"))
        base_cov = coverage(base.get("entries", []))
    for k, v in cov.items():
        delta = f"  (was {base_cov[k]})" if base_cov and base_cov.get(k) != v else ""
        print(f"  {k:18} {v}{delta}")

    haz = hazards(manifest, entries)
    print("\n=== HAZARD SCANS ===")
    for name, hits in haz.items():
        status = "CLEAN" if not hits else f"{len(hits)} — {hits[:8]}"
        print(f"  {name:18} {status}")

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

    has_hazard = any(haz.values())
    print("\n=== VERDICT:", "HAZARD — do NOT commit" if has_hazard else "no structural hazards (eyeball the sample before commit)", "===")
    return 2 if has_hazard else 0


def main() -> int:
    p = argparse.ArgumentParser(description="Verify the Atlas lexicon manifest before promote (#M-11).")
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest JSON to verify.")
    p.add_argument("--baseline", type=Path, default=None, help="Optional prior manifest for coverage deltas.")
    p.add_argument("--sample", type=int, default=12, help="How many spread-sampled entries to print (0 = none).")
    args = p.parse_args()
    return run(args.manifest, args.sample, args.baseline)


if __name__ == "__main__":
    sys.exit(main())
