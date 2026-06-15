#!/usr/bin/env python3
"""Build a compact Ukrainian Kaikki lookup for Word Atlas enrichment.

The raw Kaikki extract is large enough that Atlas builds must not stream it
every time. This script parses the local JSONL once and writes a compact lookup
keyed by stress-stripped lowercased lemma:

    data/lexicon/kaikki_uk_lookup.json

Input defaults to the local cache path used by the fillability assessment. It
does not download anything.

Run from the repo root:

    timeout 1800 .venv/bin/python scripts/lexicon/build_kaikki_lookup.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lexicon.assess_kaikki_fillability import is_clean_lemma, normalize_stress

DEFAULT_KAIKKI = Path.home() / ".cache" / "learn-ukrainian-kaikki" / "kaikki-uk.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "lexicon" / "kaikki_uk_lookup.json"
KAIKKI_SOURCE = "kaikki/Wiktionary (CC BY-SA 3.0)"

_SPACE_RE = re.compile(r"\s+")


def lookup_key(word: str) -> str:
    """Return the stress-stripped lowercased lookup key used by the Atlas."""
    return normalize_stress(str(word or "")).strip().lower()


def clean_text(text: object) -> str:
    """Collapse line noise while preserving the source wording."""
    return _SPACE_RE.sub(" ", str(text or "")).strip()


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = clean_text(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def extract_ipa(entry: dict[str, Any]) -> list[str]:
    """Extract source IPA strings from ``sounds[].ipa``."""
    out: list[str] = []
    seen: set[str] = set()
    sounds = entry.get("sounds")
    if not isinstance(sounds, list):
        return out
    for sound in sounds:
        if not isinstance(sound, dict):
            continue
        ipa = clean_text(sound.get("ipa"))
        if ipa and ipa not in seen:
            seen.add(ipa)
            out.append(ipa)
    return out


def entry_has_gloss(entry: dict[str, Any]) -> bool:
    """Mirror the fillability parser's ``senses[].glosses`` field traversal."""
    senses = entry.get("senses")
    if not isinstance(senses, list):
        return False
    for sense in senses:
        if not isinstance(sense, dict):
            continue
        if _string_items(sense.get("glosses")):
            return True
    return False


# A gloss is a real English TRANSLATION only if it is not a morphological "form of",
# spelling-variant, or misspelling meta-gloss (those are useful as a form→lemma signal,
# not as a learner-facing translation). #2882.
_META_GLOSS_RE = re.compile(
    r"^(inflection|misspelling|alternative (form|spelling)|obsolete (form|spelling)|"
    r"superseded spelling|romani[sz]ation|abbreviation|initialism|clipping|contraction|"
    r"synonym|antonym|eye dialect|pronunciation spelling|archaic (form|spelling)|"
    r"dated (form|spelling)|rare (form|spelling)|nonstandard (form|spelling)|"
    r"(a )?diminutive) of\b",
    re.IGNORECASE,
)
_FORM_OF_RE = re.compile(
    r"\b(nominative|genitive|dative|accusative|instrumental|vocative|locative|prepositional|"
    r"singular|plural|dual|first-person|second-person|third-person|imperfective|perfective|"
    r"comparative|superlative|participle|imperative|infinitive|gerund|present|past|future|"
    r"indicative|subjunctive|conditional)\b.*\bof\b\s*[Ѐ-ӿ]",
    re.IGNORECASE,
)


def _is_translation_gloss(gloss: str) -> bool:
    g = gloss.strip()
    if len(g) < 2:
        return False
    if _META_GLOSS_RE.match(g):
        return False
    return not _FORM_OF_RE.search(g)


def extract_glosses(entry: dict[str, Any]) -> list[str]:
    """Real English translation glosses (form-of / misspelling / spelling-variant dropped)."""
    out: list[str] = []
    for sense in entry.get("senses") or []:
        if not isinstance(sense, dict):
            continue
        for gloss in sense.get("glosses") or []:
            if not isinstance(gloss, str):
                continue
            g = clean_text(gloss)
            if g and _is_translation_gloss(g) and g not in out:
                out.append(g)
    return out[:6]


def build_lookup(path: Path) -> dict[str, dict[str, Any]]:
    """Stream a Kaikki JSONL file and return the compact Atlas lookup."""
    raw: dict[str, dict[str, Any]] = {}
    total_lines = 0
    uk_entries = 0
    kept_entries = 0
    gloss_entries = 0

    with Path(path).expanduser().open(encoding="utf-8") as handle:
        for line in handle:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("lang_code") and obj.get("lang_code") != "uk":
                continue
            uk_entries += 1

            word = clean_text(obj.get("word"))
            if not word or not is_clean_lemma(word):
                continue
            key = lookup_key(word)
            if not key:
                continue

            ipa = extract_ipa(obj)
            etymology = clean_text(obj.get("etymology_text"))
            pos = clean_text(obj.get("pos"))
            if entry_has_gloss(obj):
                gloss_entries += 1
            if not ipa and not etymology and not pos:
                continue

            kept_entries += 1
            row = raw.setdefault(
                key,
                {
                    "ipa": [],
                    "etymology_texts": [],
                    "pos": [],
                },
            )
            for item in ipa:
                if item not in row["ipa"]:
                    row["ipa"].append(item)
            if etymology and etymology not in row["etymology_texts"]:
                row["etymology_texts"].append(etymology)
            if pos and pos not in row["pos"]:
                row["pos"].append(pos)

    lookup: dict[str, dict[str, Any]] = {}
    for key in sorted(raw):
        row = raw[key]
        lookup[key] = {
            "ipa": row["ipa"],
            "etymology_text": "\n\n".join(row["etymology_texts"]),
            "pos": sorted(row["pos"]),
        }

    print(
        f"read {total_lines} lines; uk entries {uk_entries}; kept {kept_entries}; "
        f"gloss entries {gloss_entries}; lookup lemmas {len(lookup)}"
    )
    return lookup


def write_lookup(lookup: dict[str, dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(lookup, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {output}: {output.stat().st_size} bytes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build compact Kaikki Ukrainian lookup JSON")
    parser.add_argument("--kaikki", type=Path, default=DEFAULT_KAIKKI, help="Path to local Kaikki uk JSONL")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="Output lookup JSON")
    args = parser.parse_args(argv)

    if not args.kaikki.expanduser().exists():
        parser.error(f"Kaikki file not found: {args.kaikki}")

    lookup = build_lookup(args.kaikki)
    write_lookup(lookup, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
