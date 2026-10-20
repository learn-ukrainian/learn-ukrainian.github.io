#!/usr/bin/env python3
"""Report how many PULS A1-B1 and Atlas words slovnyk_me_entries answers, per dictionary."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.wiki.slovnyk_me import normalize_word

PULS_LEVELS = ("A1", "A2", "B1")


def _has_table(conn: SQLiteConnection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _pairs(conn: SQLiteConnection, table: str) -> set[tuple[str, str]]:
    if not _has_table(conn, table):
        return set()
    return {(word, slug) for word, slug in conn.execute(f"SELECT normalized_word, dictionary_slug FROM {table}")}


def coverage(sources_db: Path, atlas_db: Path) -> dict:
    """Per target list and dictionary: words with an entry, words with a recorded 404, list size."""
    with closing(open_readonly(sources_db)) as conn:
        puls = {
            level: {
                normalize_word(word)
                for (word,) in conn.execute("SELECT word FROM puls_cefr WHERE level = ?", (level,))
                if normalize_word(word)
            }
            for level in PULS_LEVELS
        }
        found = _pairs(conn, "slovnyk_me_entries")
        missed = _pairs(conn, "slovnyk_me_lookup_misses")
        rows = conn.execute("SELECT count(*) FROM slovnyk_me_entries").fetchone()[0] if _has_table(conn, "slovnyk_me_entries") else 0
    with closing(open_readonly(atlas_db)) as conn:
        atlas = {normalize_word(lemma) for (lemma,) in conn.execute("SELECT lemma FROM articles")} - {""}
    targets = {"puls_a1_b1": set().union(*puls.values()), **{f"puls_{k.lower()}": v for k, v in puls.items()}, "atlas": atlas}
    slugs = sorted({slug for _, slug in found | missed})
    report: dict = {"slovnyk_me_entries": rows, "targets": {name: len(words) for name, words in targets.items()}, "dictionaries": {}}
    for slug in slugs:
        in_dictionary = {word for word, s in found if s == slug}
        recorded_404 = {word for word, s in missed if s == slug}
        report["dictionaries"][slug] = {
            name: {"found": len(words & in_dictionary), "not_found": len(words & recorded_404)}
            for name, words in targets.items()
        }
    return report


def render(report: dict) -> str:
    names = list(report["targets"])
    lines = [
        f"slovnyk_me_entries rows: {report['slovnyk_me_entries']}",
        "targets: " + ", ".join(f"{name}={size}" for name, size in report["targets"].items()),
        "",
        "| dictionary | " + " | ".join(f"{name} found / not_found" for name in names) + " |",
        "| --- |" + " --- |" * len(names),
    ]
    for slug, per_target in report["dictionaries"].items():
        cells = " | ".join(f"{per_target[n]['found']} / {per_target[n]['not_found']}" for n in names)
        lines.append(f"| {slug} | {cells} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Example:\n  .venv/bin/python scripts/ingest/slovnyk_me_coverage.py "
            "--sources-db data/sources.db --atlas-db data/atlas.db --out batch_state/reports/before.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--sources-db", type=Path, required=True, help="Local sources.db to read (read-only).")
    parser.add_argument("--atlas-db", type=Path, required=True, help="Local atlas.db whose articles.lemma is the Atlas list.")
    parser.add_argument("--out", type=Path, help="Also write the report as JSON to this path.")
    args = parser.parse_args(argv)
    report = coverage(args.sources_db, args.atlas_db)
    print(render(report))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
