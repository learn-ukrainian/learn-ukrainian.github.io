"""Convert Grinchenko dictionary JSON to JSONL for RAG ingestion.

Input: data/grinchenko/json_raw/.../ua-ru-hrinchenko.json
Output: data/grinchenko/chunks.jsonl
"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "grinchenko"
INPUT_JSON = (
    DATA_DIR
    / "json_raw"
    / "Formats"
    / "Json"
    / "ukr-ru_slovar_grinchenka_uaru_dlia_lingvo"
    / "ua-ru-hrinchenko.json"
)
OUTPUT_JSONL = DATA_DIR / "chunks.jsonl"


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags, keeping text content."""

    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def get_text(self):
        return "".join(self.result).strip()


def strip_html(html_str: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    extractor = HTMLTextExtractor()
    extractor.feed(html_str)
    text = extractor.get_text()
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    print(f"Reading {INPUT_JSON}...")
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    skipped = 0

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for key, html_value in data.items():
            # Skip meta keys
            if key.startswith("##"):
                continue

            # Skip empty keys
            word = key.strip()
            if not word:
                skipped += 1
                continue

            # Strip HTML to get plain text definition
            definition = strip_html(html_value)
            if not definition:
                skipped += 1
                continue

            count += 1
            entry = {
                "id": f"gr-{count:06d}",
                "word": word,
                "definition": definition,
                "source": "Грінченко",
            }
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Written {count} entries to {OUTPUT_JSONL}")
    print(f"Skipped {skipped} empty/meta entries")

    # Show sample
    with open(OUTPUT_JSONL, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            entry = json.loads(line)
            print(f"\nSample {i + 1}: {entry['word']}")
            print(f"  {entry['definition'][:120]}...")


if __name__ == "__main__":
    main()
