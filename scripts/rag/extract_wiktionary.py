#!/usr/bin/env python3
"""Extract synonym, antonym, and translation data from Ukrainian Wiktionary dump.

Reads ukwiktionary XML dump (bz2 compressed) and extracts structured data:
- Synonyms (Синоніми)
- Antonyms (Антоніми)
- Definitions (Значення)
- Translations (Переклад)

Output: data/wiktionary/chunks.jsonl — one entry per word with all extracted fields.

Usage:
    .venv/bin/python scripts/rag/extract_wiktionary.py

Source: https://dumps.wikimedia.org/ukwiktionary/latest/
"""

from __future__ import annotations

import bz2
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DUMP_PATH = PROJECT_ROOT / "data" / "wiktionary" / "ukwiktionary.xml.bz2"
OUTPUT_PATH = PROJECT_ROOT / "data" / "wiktionary" / "chunks.jsonl"


def _extract_section(content: str, heading: str) -> list[str]:
    """Extract items from a wikitext section (==== Heading ====)."""
    pattern = re.compile(
        rf"====\s*{re.escape(heading)}\s*====\s*\n(.*?)(?=\n====|\n===|\Z)",
        re.DOTALL,
    )
    items = []
    for match in pattern.finditer(content):
        section = match.group(1)
        for line in section.strip().split("\n"):
            line = line.strip()
            if line.startswith(("*", "#")):
                # Clean wikitext markup
                text = line.lstrip("*# ")
                # Extract [[linked words]]
                text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", text)
                text = re.sub(r"'''([^']+)'''", r"\1", text)
                text = re.sub(r"''([^']+)''", r"\1", text)
                # Remove template markup {{...}}
                text = re.sub(r"\{\{[^}]*\}\}", "", text)
                text = text.strip(" ,;—")
                if text and len(text) > 1 and text != "—":
                    # Split comma-separated synonyms
                    for word in re.split(r"[,;]", text):
                        word = word.strip()
                        if word and len(word) > 1 and word != "—":
                            items.append(word)
    return items


def _extract_definitions(content: str) -> list[str]:
    """Extract definitions from Значення section."""
    pattern = re.compile(
        r"====\s*Значення\s*====\s*\n(.*?)(?=\n====|\n===|\Z)",
        re.DOTALL,
    )
    defs = []
    for match in pattern.finditer(content):
        section = match.group(1)
        for line in section.strip().split("\n"):
            line = line.strip()
            if line.startswith("#") and not line.startswith("#*"):
                text = line.lstrip("# ")
                text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", text)
                text = re.sub(r"'''([^']+)'''", r"\1", text)
                text = re.sub(r"''([^']+)''", r"\1", text)
                text = re.sub(r"\{\{[^}]+\}\}", "", text)
                text = text.strip()
                if text and len(text) > 2:
                    defs.append(text)
    return defs


def extract():
    """Extract all data from the Wiktionary dump."""
    if not DUMP_PATH.exists():
        print(f"❌ Dump not found: {DUMP_PATH}")
        print("Download: curl -sL https://dumps.wikimedia.org/ukwiktionary/latest/"
              "ukwiktionary-latest-pages-articles-multistream.xml.bz2 -o data/wiktionary/ukwiktionary.xml.bz2")
        return

    print(f"Reading {DUMP_PATH.name} (streaming bz2)...")

    count = 0
    written = 0

    with bz2.open(str(DUMP_PATH), "rt", encoding="utf-8") as f, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as out:

        title = ""
        text_buf: list[str] = []
        in_text = False
        ns = "0"  # namespace

        for line in f:
            if "<title>" in line:
                title = line.strip().replace("<title>", "").replace("</title>", "")
            elif "<ns>" in line:
                ns = line.strip().replace("<ns>", "").replace("</ns>", "")
            elif "<text" in line:
                in_text = True
                # Handle text on same line as tag
                after = line.split(">", 1)[-1] if ">" in line else ""
                text_buf = [after]
            elif in_text:
                text_buf.append(line)
                if "</text>" in line:
                    in_text = False
                    count += 1

                    # Skip non-article pages
                    if ns != "0":
                        continue
                    # Skip template/category pages
                    if title.startswith(("Шаблон:", "Категорія:", "Вікісловник:", "Додаток:")):
                        continue

                    content = "".join(text_buf)

                    # Extract data
                    synonyms = _extract_section(content, "Синоніми")
                    antonyms = _extract_section(content, "Антоніми")
                    definitions = _extract_definitions(content)

                    # Only write if we have useful data
                    if synonyms or antonyms or definitions:
                        entry = {
                            "id": f"wikt-{written:06d}",
                            "word": title,
                            "definitions": definitions,
                            "synonyms": synonyms,
                            "antonyms": antonyms,
                            "source": "Вікісловник",
                        }
                        # Build searchable text
                        parts = [title]
                        if definitions:
                            parts.append("Значення: " + "; ".join(definitions[:3]))
                        if synonyms:
                            parts.append("Синоніми: " + ", ".join(synonyms[:10]))
                        if antonyms:
                            parts.append("Антоніми: " + ", ".join(antonyms[:10]))
                        entry["text"] = ". ".join(parts)

                        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        written += 1

                    if count % 10000 == 0:
                        print(f"  Scanned {count} pages, extracted {written} entries...")

    print(f"\n✅ Done: {count} pages scanned, {written} entries written to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    extract()
