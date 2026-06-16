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


# A gloss CLAUSE is a morphological "form of" / spelling-variant / misspelling meta-note —
# useful as a form→lemma signal, NOT a learner-facing translation. Wiktionary often appends
# such a note to a real translation in the same gloss string ("what, alternative form of що")
# or behind a leading qualifier ("common misspelling of X"), so the match must (a) tolerate a
# leading qualifier word and (b) be applied per comma/semicolon clause, not just at string
# start. #2882.
_META_CLAUSE_RE = re.compile(
    r"^(?:(?:a|an|the|common|informal|colloquial|dialectal|regional|rare|dated|slang|"
    r"chiefly|mainly|eye|endearing)\s+)*"
    r"(inflection|misspelling|alternative (form|spelling)|obsolete (form|spelling)|"
    r"superseded spelling|romani[sz]ation|abbreviation|initialism|clipping|contraction|"
    r"eye dialect|pronunciation spelling|archaic (form|spelling)|"
    r"dated (form|spelling)|rare (form|spelling)|nonstandard (form|spelling)|"
    r"diminutive) of\b",
    re.IGNORECASE,
)
_FORM_OF_RE = re.compile(
    r"\b(nominative|genitive|dative|accusative|instrumental|vocative|locative|prepositional|"
    r"singular|plural|dual|first-person|second-person|third-person|imperfective|perfective|"
    r"comparative|superlative|participle|imperative|infinitive|gerund|present|past|future|"
    r"indicative|subjunctive|conditional|passive|active|verbal noun)\b.*\bof\b\s*[Ѐ-ӿ]",
    re.IGNORECASE,
)
# A clause made up ENTIRELY of grammatical-form descriptors ("accusative singular",
# "nominative/vocative plural") is an inflected-form gloss, NOT a translation. Wiktionary
# emits these bare (no "of <lemma>" tail) on non-lemma form entries. Requires >= 2 tokens so a
# real one-word gloss that happens to be a grammatical term ("present", "plural") survives. #2882.
_GRAMMATICAL_TOKEN = (
    r"nominative|genitive|dative|accusative|instrumental|vocative|locative|prepositional|"
    r"singular|plural|dual|animate|inanimate|masculine|feminine|neuter|"
    r"first-person|second-person|third-person|present|past|future|imperfective|perfective|"
    r"indicative|subjunctive|imperative|conditional|comparative|superlative"
)
_GRAMMATICAL_FORM_RE = re.compile(rf"^(?:(?:{_GRAMMATICAL_TOKEN})[\s/]*)+$", re.IGNORECASE)
_TOKEN_SPLIT_RE = re.compile(r"[\s/]+")
_CLAUSE_SPLIT_RE = re.compile(r"\s*[;,]\s*")


def _is_grammatical_form(clause: str) -> bool:
    c = clause.strip()
    return bool(_GRAMMATICAL_FORM_RE.match(c)) and len(_TOKEN_SPLIT_RE.split(c)) >= 2


def _is_meta_clause(clause: str) -> bool:
    return bool(
        _META_CLAUSE_RE.match(clause)
        or _FORM_OF_RE.search(clause)
        or _is_grammatical_form(clause)
    )


def _clean_gloss(gloss: str) -> str:
    """Drop meta clauses (form-of / misspelling / spelling-variant), keep real translations.

    Non-destructive when no meta clause is present — the original gloss is returned
    unchanged so good glosses keep their exact formatting.
    """
    g = gloss.strip()
    if ":" in g:
        prefix, suffix = g.split(":", 1)
        if _is_meta_clause(prefix):
            return _clean_gloss(suffix) if suffix.strip() else ""
    clauses = _CLAUSE_SPLIT_RE.split(g)
    if len(clauses) == 1:
        return "" if _is_meta_clause(g) else g
    kept = [c for c in clauses if c and not _is_meta_clause(c)]
    if len(kept) == len(clauses):
        return g  # nothing dropped — preserve original
    return ", ".join(kept).strip()


def extract_glosses(entry: dict[str, Any]) -> list[str]:
    """Real English translation glosses (form-of / misspelling / spelling-variant dropped)."""
    out: list[str] = []
    for sense in entry.get("senses") or []:
        if not isinstance(sense, dict):
            continue
        for gloss in sense.get("glosses") or []:
            if not isinstance(gloss, str):
                continue
            cleaned = _clean_gloss(clean_text(gloss))
            if len(cleaned) >= 2 and cleaned not in out:
                out.append(cleaned)
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
            glosses = extract_glosses(obj)
            if entry_has_gloss(obj):
                gloss_entries += 1
            if not ipa and not etymology and not pos and not glosses:
                continue

            kept_entries += 1
            row = raw.setdefault(
                key,
                {
                    "ipa": [],
                    "etymology_texts": [],
                    "pos": [],
                    "glosses": [],
                },
            )
            for item in ipa:
                if item not in row["ipa"]:
                    row["ipa"].append(item)
            if etymology and etymology not in row["etymology_texts"]:
                row["etymology_texts"].append(etymology)
            if pos and pos not in row["pos"]:
                row["pos"].append(pos)
            for gloss in glosses:
                if gloss not in row["glosses"]:
                    row["glosses"].append(gloss)

    lookup: dict[str, dict[str, Any]] = {}
    for key in sorted(raw):
        row = raw[key]
        lookup[key] = {
            "ipa": row["ipa"],
            "etymology_text": "\n\n".join(row["etymology_texts"]),
            "pos": sorted(row["pos"]),
            "glosses": row["glosses"][:6],
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
