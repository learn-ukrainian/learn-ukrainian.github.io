"""Generate the words-only C29 closed-class attestations from the local PULS table."""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

import yaml

from scripts.curriculum.validate.a1_reference import CLOSED_CLASS_PATH, _closed_class_from_bytes, normalize

CLASSES = {"займенник": "pron", "сполучник": "conj", "прийменник": "prep", "частка": "part"}
# Printed pages of the first dedicated grammar units in the owned A1 workbook.
# PULS groups these spellings in comma rows rather than attesting them individually.
REFERENCE_UNITS = {("і", "conj"): 47, ("й", "conj"): 47, ("в", "prep"): 41, ("у", "prep"): 41}


def build_inventory(db_path: Path) -> dict:
    """Expand every A1 closed-class PULS row; retain no glosses or unit text."""
    words = {}
    with sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        rows = connection.execute("SELECT word, level, pos FROM puls_cefr WHERE level = 'A1'").fetchall()
    for word, level, pos in rows:
        if pos not in CLASSES:
            continue
        for spelling in word.split(","):
            lemma = normalize(spelling)
            if not re.fullmatch(r"[а-яіїєґ’\-]+", lemma):
                raise ValueError("PULS A1 closed-class row is not words-only")
            cls = CLASSES[pos]
            if (lemma, cls) in REFERENCE_UNITS:
                continue
            words[lemma, cls] = {"lemma": lemma, "kind": "word", "class": cls, "level": level, "source": "PULS"}
    for (lemma, cls), page in REFERENCE_UNITS.items():
        words[lemma, cls] = {"lemma": lemma, "kind": "word", "class": cls, "level": "A1", "source": "reference_units", "page": page}
    payload = {"version": 1, "kind": "atlas_source_inventory", "sources": [
        {"id": "puls-a1-closed-class", "source_family": "puls", "extraction_mode": "curated_key_word",
         "title": "PULS A1 closed-class words", "path": "puls_cefr",
         "headwords": [words[key] for key in sorted(words) if words[key]["source"] == "PULS"]},
        {"id": "ohoiko-a1-closed-class", "source_family": "ohoiko", "extraction_mode": "curated_key_word",
         "title": "A1 workbook closed-class grammar attestations", "path": "oho-ukrainian-grammar-workbook-a1.pdf",
         "headwords": [words[key] for key in sorted(words) if words[key]["source"] == "reference_units"]},
    ]}
    _closed_class_from_bytes(yaml.safe_dump(payload, allow_unicode=True).encode())
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build words-only, class-specific A1 attestations from PULS.\n"
                    "Use for C29 inventory regeneration; this does not assign levels to other classes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  .venv/bin/python -m scripts.ingest.build_a1_closed_class --db data/sources.db\n"
               "  .venv/bin/python -m scripts.ingest.build_a1_closed_class --db /path/sources.db --output /tmp/a1.yaml\n"
               "Outputs: YAML inventory only; database opened read-only.\n"
               "Exit codes: 0 generated and validated; 1 source or output failure.\n"
               "Related: #9582; scripts/curriculum/validate/a1_reference.py",
    )
    parser.add_argument("--db", type=Path, required=True, help="Existing sources SQLite database (read-only), e.g. data/sources.db")
    parser.add_argument("--output", type=Path, default=CLOSED_CLASS_PATH,
                        help="Output YAML path (default: registry/lexicon/source-inventory/a1-closed-class.yaml)")
    args = parser.parse_args(argv)
    try:
        payload = build_inventory(args.db)
        args.output.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"A1 closed-class generation failed: {error}")
        return 1
    print(f"Generated {sum(len(s['headwords']) for s in payload['sources'])} words/classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
