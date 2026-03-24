#!/usr/bin/env python3
"""Convert Phase 2 raw data to JSONL for RAG ingestion.

Converts:
1. dmklinger UK→EN (words.json → chunks.jsonl)
2. Ukrajinet WordNet (ukrajinet.xml → chunks.jsonl)
3. UberText frequency (csv.xz → SQLite)
4. СУМ-11 register labels (extract розм./книжн./заст. from existing chunks)

Usage:
    .venv/bin/python scripts/rag/convert_phase2.py --dmklinger
    .venv/bin/python scripts/rag/convert_phase2.py --ukrajinet
    .venv/bin/python scripts/rag/convert_phase2.py --ubertext-freq
    .venv/bin/python scripts/rag/convert_phase2.py --sum11-registers
    .venv/bin/python scripts/rag/convert_phase2.py --all
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def convert_dmklinger():
    """Convert dmklinger UK→EN words.json to JSONL."""
    src = PROJECT_ROOT / "data" / "dmklinger-uk-en" / "words.json"
    out = PROJECT_ROOT / "data" / "dmklinger-uk-en" / "chunks.jsonl"

    print("Converting dmklinger UK→EN...")
    with open(src, encoding="utf-8") as f:
        words = json.load(f)

    with open(out, "w", encoding="utf-8") as f:
        for i, entry in enumerate(words):
            word = entry.get("word", "")
            pos = entry.get("pos", "")
            defs = entry.get("defs", [])
            if not word or not defs:
                continue
            chunk = {
                "id": f"dmk-{i:06d}",
                "word": word,
                "pos": pos,
                "translations": defs[:10],
                "text": f"{word} ({pos}): {'; '.join(defs[:5])}",
                "source": "dmklinger UK→EN",
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"  ✅ {len(words)} entries → {out.name}")


def convert_ukrajinet():
    """Convert Ukrajinet WordNet XML to JSONL."""
    src = PROJECT_ROOT / "data" / "ukrajinet" / "ukrajinet.xml"
    out = PROJECT_ROOT / "data" / "ukrajinet" / "chunks.jsonl"

    print("Converting Ukrajinet WordNet...")

    tree = ET.parse(src)
    root = tree.getroot()

    # Find the Lexicon element
    lexicon = root.find("Lexicon")
    if lexicon is None:
        # Try with namespace
        for child in root:
            if "Lexicon" in child.tag:
                lexicon = child
                break

    if lexicon is None:
        print("  ❌ Could not find Lexicon element")
        return

    # Extract LexicalEntries (words) and Synsets
    entries_by_id: dict[str, dict] = {}
    synsets: dict[str, list[str]] = {}

    for elem in lexicon:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "LexicalEntry":
            entry_id = elem.attrib.get("id", "")
            lemma = elem.find("Lemma")
            if lemma is None:
                for child in elem:
                    if "Lemma" in (child.tag.split("}")[-1] if "}" in child.tag else child.tag):
                        lemma = child
                        break
            if lemma is not None:
                word = lemma.attrib.get("writtenForm", "")
                pos = lemma.attrib.get("partOfSpeech", "")
                entries_by_id[entry_id] = {"word": word, "pos": pos}

                # Find Sense elements to link to synsets
                for child in elem:
                    child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_tag == "Sense":
                        synset_id = child.attrib.get("synset", "")
                        if synset_id:
                            if synset_id not in synsets:
                                synsets[synset_id] = []
                            synsets[synset_id].append(word)

    # Build synonym groups from synsets
    written = 0
    with open(out, "w", encoding="utf-8") as f:
        for synset_id, words in sorted(synsets.items()):
            if len(words) < 1:
                continue
            chunk = {
                "id": f"ukrnet-{written:06d}",
                "synset_id": synset_id,
                "words": words,
                "text": f"Синоніми: {', '.join(words)}",
                "source": "Ukrajinet WordNet",
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            written += 1

    multi = sum(1 for w in synsets.values() if len(w) > 1)
    print(f"  ✅ {written} synsets ({multi} with 2+ synonyms) → {out.name}")
    print(f"  Total unique words: {len(entries_by_id)}")


def convert_ubertext_freq():
    """Import UberText frequency list into SQLite for fast lookups."""
    import lzma

    src = PROJECT_ROOT / "data" / "ubertext-freq" / "ubertext_freq.csv.xz"
    db_path = PROJECT_ROOT / "data" / "ubertext-freq" / "frequency.db"

    print("Converting UberText frequency list to SQLite...")
    print(f"  Source: {src.name} (this may take a minute)...")

    db = sqlite3.connect(str(db_path))
    db.execute("DROP TABLE IF EXISTS freq")
    db.execute("""
        CREATE TABLE freq (
            lemma TEXT,
            pos TEXT,
            count INTEGER,
            doc_count INTEGER,
            freq_by_pos REAL,
            freq_in_corpus REAL,
            doc_frequency REAL
        )
    """)

    count = 0
    batch = []
    with lzma.open(str(src), "rt", encoding="utf-8") as f:
        f.readline()  # skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 7:
                continue
            batch.append(tuple(parts[:7]))
            if len(batch) >= 50000:
                db.executemany(
                    "INSERT INTO freq VALUES (?,?,?,?,?,?,?)", batch
                )
                count += len(batch)
                batch = []
                if count % 500000 == 0:
                    print(f"    {count:,} rows...")

    if batch:
        db.executemany("INSERT INTO freq VALUES (?,?,?,?,?,?,?)", batch)
        count += len(batch)

    db.execute("CREATE INDEX idx_freq_lemma ON freq(lemma)")
    db.execute("CREATE INDEX idx_freq_count ON freq(count DESC)")
    db.commit()
    db.close()

    print(f"  ✅ {count:,} frequency rows → {db_path.name}")


def extract_sum11_registers():
    """Extract stylistic register labels from СУМ-11 definitions."""
    src = PROJECT_ROOT / "data" / "sum11" / "chunks.jsonl"
    out = PROJECT_ROOT / "data" / "sum11" / "registers.jsonl"

    print("Extracting register labels from СУМ-11...")

    # Standard Ukrainian dictionary register abbreviations
    register_patterns = {
        "розм.": "розмовне",      # colloquial
        "книжн.": "книжне",       # bookish/literary
        "офіц.": "офіційне",      # official
        "заст.": "застаріле",     # archaic
        "діал.": "діалектне",     # dialectal
        "жарт.": "жартівливе",   # humorous
        "зневажл.": "зневажливе", # pejorative
        "вульг.": "вульгарне",   # vulgar
        "поет.": "поетичне",     # poetic
        "спец.": "спеціальне",   # specialized/technical
        "наук.": "наукове",      # scientific
        "перен.": "переносне",   # figurative
    }

    count = 0
    labeled = 0
    with open(src, encoding="utf-8") as fin, \
         open(out, "w", encoding="utf-8") as fout:
        for line in fin:
            entry = json.loads(line)
            word = entry.get("word", "")
            definition = entry.get("definition", "")
            count += 1

            # Find register labels in the definition
            registers = []
            for abbr, full_name in register_patterns.items():
                if abbr in definition[:200]:  # Check near the start
                    registers.append(full_name)

            if registers:
                labeled += 1
                chunk = {
                    "word": word,
                    "registers": registers,
                }
                fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"  ✅ {labeled}/{count} words have register labels → {out.name}")
    # Show distribution
    from collections import Counter
    reg_counts: Counter[str] = Counter()
    with open(out, encoding="utf-8") as f:
        for line in f:
            for r in json.loads(line)["registers"]:
                reg_counts[r] += 1
    for reg, cnt in reg_counts.most_common():
        print(f"    {cnt:>6}  {reg}")


def main():
    parser = argparse.ArgumentParser(description="Convert Phase 2 data")
    parser.add_argument("--dmklinger", action="store_true")
    parser.add_argument("--ukrajinet", action="store_true")
    parser.add_argument("--ubertext-freq", action="store_true")
    parser.add_argument("--sum11-registers", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.all or args.dmklinger:
        convert_dmklinger()
    if args.all or args.ukrajinet:
        convert_ukrajinet()
    if args.all or args.ubertext_freq:
        convert_ubertext_freq()
    if args.all or args.sum11_registers:
        extract_sum11_registers()


if __name__ == "__main__":
    main()
