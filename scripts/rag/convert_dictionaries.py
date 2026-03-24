#!/usr/bin/env python3
"""Convert downloaded JSON dictionaries to JSONL chunks for RAG ingestion.

Converts:
- СУМ-11 (Ukrainian explanatory dictionary, 127K entries)
- Балла EN→UK (English-Ukrainian, 79K entries)
- Фразеологічний словник (Ukrainian idioms, 25K entries)

Source: https://github.com/bakustarver/ukr-dictionaries-list-opensource

Usage:
    .venv/bin/python scripts/rag/convert_dictionaries.py --sum11
    .venv/bin/python scripts/rag/convert_dictionaries.py --balla
    .venv/bin/python scripts/rag/convert_dictionaries.py --frazeolohichnyi
    .venv/bin/python scripts/rag/convert_dictionaries.py --all
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def strip_html(html: str) -> str:
    """Strip HTML tags and clean up text."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", html)
    # Fix HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&#x27;", "'").replace("&quot;", '"')
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def convert_sum11():
    """Convert СУМ-11 to JSONL."""
    src = PROJECT_ROOT / "data" / "sum11" / "Formats" / "Json" / "ukr-ukr_SUM-11_or_1" / "ukr-ukr_SUM-11_or_1.json"
    out = PROJECT_ROOT / "data" / "sum11" / "chunks.jsonl"

    print(f"Loading СУМ-11 from {src.name}...")
    data = json.loads(src.read_text("utf-8"))

    entries = {k: v for k, v in data.items() if not k.startswith("##")}
    print(f"  {len(entries)} entries")

    with open(out, "w", encoding="utf-8") as f:
        for i, (word, html) in enumerate(entries.items()):
            text = strip_html(str(html))
            chunk = {
                "id": f"sum11-{i:06d}",
                "word": word,
                "text": f"{word}: {text}",
                "definition": text,
                "source": "СУМ-11",
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"  ✅ Written {len(entries)} entries to {out.name}")


def convert_balla():
    """Convert Балла EN→UK to JSONL."""
    src = PROJECT_ROOT / "data" / "balla-en-uk" / "Formats" / "Json" / "en-ua_angloukrayinskii_slovnik_miballa_engukr" / "eng-ukr_Balla_v1.3.json"
    out = PROJECT_ROOT / "data" / "balla-en-uk" / "chunks.jsonl"

    print(f"Loading Балла EN→UK from {src.name}...")
    data = json.loads(src.read_text("utf-8"))

    entries = {k: v for k, v in data.items() if not k.startswith("##")}
    print(f"  {len(entries)} entries")

    with open(out, "w", encoding="utf-8") as f:
        for i, (word, html) in enumerate(entries.items()):
            text = strip_html(str(html))
            chunk = {
                "id": f"balla-{i:06d}",
                "word": word,
                "text": f"{word}: {text}",
                "definition": text,
                "source": "Балла EN→UK",
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"  ✅ Written {len(entries)} entries to {out.name}")


def convert_frazeolohichnyi():
    """Convert Фразеологічний словник to JSONL."""
    src = PROJECT_ROOT / "data" / "frazeolohichnyi" / "Formats" / "Json" / "ukr-ukr_frazeolohicnhyi_slovnyk" / "fl.frasesUkUk.json"
    out = PROJECT_ROOT / "data" / "frazeolohichnyi" / "chunks.jsonl"

    print(f"Loading Фразеологічний словник from {src.name}...")
    data = json.loads(src.read_text("utf-8"))

    entries = {k: v for k, v in data.items() if not k.startswith("##") and not k.startswith("{{")}
    print(f"  {len(entries)} entries (after filtering metadata)")

    with open(out, "w", encoding="utf-8") as f:
        count = 0
        for i, (phrase, html) in enumerate(entries.items()):
            text = strip_html(str(html))
            # Clean up stress markup artifacts
            clean_phrase = re.sub(r"\{?\[/?'?\]\}?", "", phrase).strip()
            if len(clean_phrase) < 3:
                continue
            chunk = {
                "id": f"fraz-{i:06d}",
                "word": clean_phrase,
                "text": f"{clean_phrase}: {text}",
                "definition": text,
                "source": "Фразеологічний словник",
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            count += 1

    print(f"  ✅ Written {count} entries to {out.name}")


def main():
    parser = argparse.ArgumentParser(description="Convert dictionaries to JSONL")
    parser.add_argument("--sum11", action="store_true")
    parser.add_argument("--balla", action="store_true")
    parser.add_argument("--frazeolohichnyi", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all or args.sum11:
        convert_sum11()
    if args.all or args.balla:
        convert_balla()
    if args.all or args.frazeolohichnyi:
        convert_frazeolohichnyi()

    if not any([args.all, args.sum11, args.balla, args.frazeolohichnyi]):
        parser.print_help()


if __name__ == "__main__":
    main()
