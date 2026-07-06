#!/usr/bin/env python3
"""
Extract new synonym pairs from manifest and compute their attestation status.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

import yaml

# Add script paths to sys.path so we can import from scripts
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.generate_practice_deck import (
    CEFR_RANK,
    RealVesumVerifier,
    _build_lexeme,
    _plain,
    _section_items,
    _valid_synonym_distractors,
    is_practice_eligible,
    read_manifest,
)
from scripts.lexicon.enrich_manifest import _slovnyk_cache_path


def word_in_text(word: str, text: str) -> bool:
    if not text:
        return False
    w_plain = _plain(word)
    t_clean = text.casefold().replace("\u0301", "").replace("́", "").replace("’", "'").replace("ʼ", "'")
    words = re.findall(r"[a-zа-яєіїґ'-]+", t_clean)
    return w_plain in words

def load_slovnyk_cache(lemma: str) -> dict[str, Any] | None:
    try:
        path = _slovnyk_cache_path(lemma)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def main() -> int:
    parser = argparse.ArgumentParser(description="Verify synonym pairs from manifest")
    parser.add_argument("--manifest", type=Path, default=Path("site/src/data/lexicon-manifest.json"), help="Path to manifest JSON")
    parser.add_argument("--verdicts", type=Path, default=Path("data/lexicon/synonym_pair_verdicts.yaml"), help="Path to verdicts YAML")
    parser.add_argument("--out", type=Path, required=True, help="Path to write new pairs JSONL")
    args = parser.parse_args()

    # Load adjudicated keys from verdicts YAML if it exists
    adjudicated_keys = set()
    if args.verdicts.exists():
        try:
            with open(args.verdicts, encoding="utf-8") as f:
                verdicts_data = yaml.safe_load(f) or {}
            for item in verdicts_data.get("approved", []):
                a_p = _plain(item["a"])
                b_p = _plain(item["b"])
                if a_p > b_p:
                    a_p, b_p = b_p, a_p
                adjudicated_keys.add((a_p, b_p, item["polarity"]))
            for item in verdicts_data.get("rejected", []):
                a_p = _plain(item["a"])
                b_p = _plain(item["b"])
                if a_p > b_p:
                    a_p, b_p = b_p, a_p
                adjudicated_keys.add((a_p, b_p, item["polarity"]))
            print(f"Loaded {len(adjudicated_keys)} adjudicated keys from {args.verdicts}")
        except Exception as e:
            print(f"Warning: failed to load verdicts file {args.verdicts}: {e}", file=sys.stderr)
    else:
        print(f"Verdicts file {args.verdicts} not found, treating all pairs as new.")

    # 1. Read manifest and build lexemes (reusing deck builder semantics)
    if not args.manifest.exists():
        print(f"Error: manifest file {args.manifest} does not exist", file=sys.stderr)
        return 1

    print("Loading manifest and verifying words with VESUM...")
    entries = read_manifest(args.manifest)
    verifier = RealVesumVerifier()
    eligible = [entry for entry in entries if is_practice_eligible(entry)]

    lexemes_by_entry = []
    for entry in eligible:
        lexeme = _build_lexeme(entry, verifier)
        if lexeme:
            lexemes_by_entry.append((entry, lexeme))

    all_lexemes = [lexeme for _, lexeme in lexemes_by_entry]
    by_plain_lemma = {}
    for lexeme in all_lexemes:
        by_plain_lemma.setdefault(_plain(lexeme["lemma"]), lexeme)

    # 2. Extract candidate pairs
    candidate_pairs = []
    seen_pair_keys = set()
    for entry, lexeme in lexemes_by_entry:
        for polarity, section_name in (("synonym", "synonyms"), ("antonym", "antonyms")):
            for target_label in _section_items(entry, section_name):
                target = by_plain_lemma.get(_plain(target_label))
                if not target:
                    continue
                if CEFR_RANK[lexeme["cefr"]] < CEFR_RANK["B1"]:
                    continue
                if CEFR_RANK[target["cefr"]] > CEFR_RANK[lexeme["cefr"]]:
                    continue
                distractors = _valid_synonym_distractors(target, lexeme, all_lexemes)
                if len(distractors) < 3:
                    continue

                a_orig = lexeme["lemma"]
                b_orig = target["lemma"]
                a_plain = _plain(a_orig)
                b_plain = _plain(b_orig)
                if a_plain > b_plain:
                    a_plain, b_plain = b_plain, a_plain
                    a_orig, b_orig = b_orig, a_orig

                key = (a_plain, b_plain, polarity)
                if key not in seen_pair_keys:
                    seen_pair_keys.add(key)
                    candidate_pairs.append({
                        "a": a_orig,
                        "b": b_orig,
                        "a_plain": a_plain,
                        "b_plain": b_plain,
                        "polarity": polarity,
                        "key": key
                    })

    # Filter out already adjudicated pairs
    new_pairs = [p for p in candidate_pairs if p["key"] not in adjudicated_keys]
    print(f"Found {len(candidate_pairs)} candidate pairs total, {len(new_pairs)} are new.")

    if not new_pairs:
        # Write empty list or touch the output file
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("")
        print("No new pairs to verify.")
        return 0

    # 3. Compute deterministic attestation
    # Load wiktionary from sources.db in memory for fast lookup
    print("Loading wiktionary table from data/sources.db...")
    wiktionary_data = {}
    sources_db_path = PROJECT_ROOT / "data" / "sources.db"
    if sources_db_path.exists():
        try:
            conn = sqlite3.connect(sources_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, synonyms, antonyms FROM wiktionary")
            for word, syns, ants in cursor.fetchall():
                w_plain = _plain(word)
                combined_text = (syns or "") + " " + (ants or "")
                wiktionary_data.setdefault(w_plain, []).append(combined_text)
            conn.close()
        except Exception as e:
            print(f"Warning: failed to load wiktionary from sources.db: {e}", file=sys.stderr)
    else:
        print("Warning: data/sources.db not found; skipping wiktionary check.", file=sys.stderr)

    # Pre-load slovnyk_cache for all unique words in new pairs to avoid multiple disk reads
    unique_words = set()
    for p in new_pairs:
        unique_words.add(p["a"])
        unique_words.add(p["b"])

    print(f"Loading slovnyk_cache for {len(unique_words)} words...")
    slovnyk_caches = {}
    for word in unique_words:
        cache = load_slovnyk_cache(word)
        if cache:
            slovnyk_caches[word] = cache

    # Process new pairs
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Open out file to write JSONL
    print(f"Writing verified new pairs to {args.out}...")
    with open(args.out, "w", encoding="utf-8") as out_f:
        for p in new_pairs:
            a_orig = p["a"]
            b_orig = p["b"]
            a_plain = p["a_plain"]
            b_plain = p["b_plain"]
            polarity = p["polarity"]

            attest_sources = set()

            # Check Wiktionary
            # Check if b_plain is a word in a_plain's wiktionary text
            for text in wiktionary_data.get(a_plain, []):
                if word_in_text(b_plain, text):
                    attest_sources.add("wiktionary")
            # Check if a_plain is a word in b_plain's wiktionary text
            for text in wiktionary_data.get(b_plain, []):
                if word_in_text(a_plain, text):
                    attest_sources.add("wiktionary")

            # Check slovnyk_cache
            # For a
            cache_a = slovnyk_caches.get(a_orig)
            if cache_a and "lookups" in cache_a:
                lookups = cache_a["lookups"] or {}
                # Check synonyms
                syn_lookup = lookups.get("synonyms")
                if syn_lookup and word_in_text(b_plain, syn_lookup.get("text", "")):
                    attest_sources.add("synonyms")
                # Check synonyms_karavansky
                kar_lookup = lookups.get("synonyms_karavansky")
                if kar_lookup and word_in_text(b_plain, kar_lookup.get("text", "")):
                    attest_sources.add("synonyms_karavansky")

            # For b
            cache_b = slovnyk_caches.get(b_orig)
            if cache_b and "lookups" in cache_b:
                lookups = cache_b["lookups"] or {}
                # Check synonyms
                syn_lookup = lookups.get("synonyms")
                if syn_lookup and word_in_text(a_plain, syn_lookup.get("text", "")):
                    attest_sources.add("synonyms")
                # Check synonyms_karavansky
                kar_lookup = lookups.get("synonyms_karavansky")
                if kar_lookup and word_in_text(a_plain, kar_lookup.get("text", "")):
                    attest_sources.add("synonyms_karavansky")

            attested = len(attest_sources) > 0

            output_obj = {
                "a": a_orig,
                "b": b_orig,
                "polarity": polarity,
                "attested": attested,
                "attest_sources": sorted(list(attest_sources))
            }

            # Print to stdout
            print(json.dumps(output_obj, ensure_ascii=False))
            # Write to JSONL file
            out_f.write(json.dumps(output_obj, ensure_ascii=False) + "\n")

    print("Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
