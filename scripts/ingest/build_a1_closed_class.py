"""Generate the words-only C29 closed-class attestations from the local PULS table."""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

import yaml

from scripts.curriculum.validate.a1_reference import CLOSED_CLASS_PATH, _closed_class_from_bytes, normalize

try:
    from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
except ModuleNotFoundError as exc:
    # Script execution puts the script directory on sys.path, so the
    # top-level package is absent (exc.name == "scripts"). Any other
    # import failure must propagate.
    if exc.name != "scripts":
        raise
    # lib.readonly_sqlite lives in scripts/, which file execution does not put on sys.path.
    _scripts_dir = next(
        parent for parent in Path(__file__).resolve().parents if parent.name == "scripts"
    )
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from lib.readonly_sqlite import open_readonly as _open_readonly  # type: ignore[no-redef]

CLASSES = {"займенник": "pron", "сполучник": "conj", "прийменник": "prep", "частка": "part"}
# PULS comma-separated rows attest each spelling with the row's class and level.


def build_inventory(db_path: Path) -> dict:
    """Expand every A1 closed-class PULS row; retain no glosses or unit text."""
    words = {}
    with _open_readonly(db_path) as connection:
        rows = connection.execute("SELECT word, level, pos FROM puls_cefr WHERE level = 'A1'").fetchall()
    for word, level, pos in rows:
        if pos not in CLASSES:
            continue
        for spelling in word.split(","):
            lemma = normalize(spelling)
            if not re.fullmatch(r"[а-яіїєґ’\-]+", lemma):
                raise ValueError("PULS A1 closed-class row is not words-only")
            cls = CLASSES[pos]
            words[lemma, cls] = {"lemma": lemma, "kind": "word", "class": cls, "level": level, "source": "PULS"}
    payload = {"version": 1, "kind": "atlas_source_inventory", "sources": [
        {"id": "puls-a1-closed-class", "source_family": "puls", "extraction_mode": "curated_key_word",
         "title": "PULS A1 closed-class words", "path": "puls_cefr",
         "headwords": [words[key] for key in sorted(words)]},
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
                        help="Output YAML path (default: scripts/curriculum/validate/data/a1-closed-class.yaml)")
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
