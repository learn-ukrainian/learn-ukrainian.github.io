#!/usr/bin/env python3
"""Calculate Ukrainian vs English word ratio in a content file.

Returns JSON with word counts and percentages for use by LLM agents.

Usage:
    .venv/bin/python scripts/calc_immersion.py curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md

Output (JSON):
    {
        "ukrainian_words": 2800,
        "english_words": 400,
        "total_words": 3200,
        "ukrainian_percent": 87.5,
        "english_percent": 12.5,
        "file": "curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md"
    }
"""

import json
import re
import sys
from pathlib import Path


def count_words(text: str) -> dict:
    """Count Ukrainian (Cyrillic) and English (Latin) words in text."""
    # Ukrainian words: sequences of Cyrillic chars (including apostrophe for Ukrainian)
    uk_words = re.findall(r"[а-яіїєґА-ЯІЇЄҐёЁ'ʼ]+", text)
    # English words: sequences of Latin chars (min 2 chars to skip stray letters)
    en_words = re.findall(r"\b[a-zA-Z]{2,}\b", text)

    uk_count = len(uk_words)
    en_count = len(en_words)
    total = uk_count + en_count

    if total == 0:
        return {
            "ukrainian_words": 0,
            "english_words": 0,
            "total_words": 0,
            "ukrainian_percent": 0.0,
            "english_percent": 0.0,
        }

    return {
        "ukrainian_words": uk_count,
        "english_words": en_count,
        "total_words": total,
        "ukrainian_percent": round(uk_count * 100 / total, 1),
        "english_percent": round(en_count * 100 / total, 1),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: calc_immersion.py <content_file>", file=sys.stderr)
        return 1

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(json.dumps({"error": f"File not found: {filepath}"}))
        return 1

    text = filepath.read_text(encoding="utf-8")
    result = count_words(text)
    result["file"] = str(filepath)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
