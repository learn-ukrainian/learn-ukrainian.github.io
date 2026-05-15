"""Add ``author_uk`` (Cyrillic) column to ``textbooks`` and back-fill it.

This migration retires runtime transliteration from the textbook matcher.
Historically, ``textbooks.author`` stored Latin-romanized author names
(``zabolotnyi``, ``glazova``, ``golub``) because scraping pipelines used
Russian-mediated romanization schemes. Plan files cite authors in
Cyrillic (``Заболотний``, ``Глазова``, ``Голуб``), so the runtime matcher
maintained a Cyrillic→Latin translit dictionary and matched via
``source_file LIKE %-translit-%`` patterns.

After this migration:

* ``textbooks.author_uk`` holds the canonical Cyrillic form of the author.
* The runtime matcher queries ``WHERE author_uk = ? AND grade = ?`` —
  no transliteration, no LIKE patterns.
* The Latin ``author`` column stays for backwards compatibility with
  archived analytics and corpus-naming history (Latin source_file strings
  on disk are renamed in a separate follow-up PR).

The ``_LATIN_TO_UK`` dict below is the ONLY place transliteration is still
acknowledged in the codebase. It's a one-time bridge from the
Latin-named past to the Cyrillic-clean future. New ingestion paths must
supply ``author_uk`` explicitly (see ``scripts/wiki/build_sources_db.py``
and ``scripts/ingest/*``).

See ADR ``docs/decisions/2026-05-15-cyrillic-native-matcher.md`` for the
decolonization rationale.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"


@dataclass
class MigrationStatus:
    column_added: bool = False
    rows_updated: int = 0
    unmapped_authors: list[str] = field(default_factory=list)
    total_rows: int = 0
    populated_author_uk: int = 0


# Inverted from the historical _TEXTBOOK_AUTHOR_TRANSLITS dict
# (plus the 6 entries added in PR #2013 and additional corpus authors
# discovered via SELECT DISTINCT author FROM textbooks). Latin keys are
# matched verbatim against textbooks.author.
_LATIN_TO_UK: dict[str, str] = {
    # Core mova/lit textbook authors (originally in TRANSLITS)
    "karaman": "Караман",
    "zakhariychuk": "Захарійчук",
    "zaharijchuk": "Захарійчук",
    "zahariichuk": "Захарійчук",
    "kravcova": "Кравцова",
    "kravtsova": "Кравцова",
    "avramenko": "Авраменко",
    "glazova": "Глазова",
    "hlazova": "Глазова",
    "zabolotnyi": "Заболотний",
    "zabolotnij": "Заболотний",
    "zakharchuk": "Захарчук",
    "vashulenko": "Вашуленко",
    "bolshakova": "Большакова",
    "mishhenko": "Міщенко",
    "mishchenko": "Міщенко",
    "litvinova": "Літвінова",
    "golub": "Голуб",
    "varzatska": "Варзацька",
    "ponomarova": "Пономарова",
    # Additional textbook authors present in the corpus
    "borzenko": "Борзенко",
    "burnejko": "Бурнейко",
    "galimov": "Галімов",
    "gisem": "Гісем",
    # Хлібовська: front-matter of 7-klas/8-klas/11-klas history textbooks
    # confirms Х (Kh), not Г — the Latin transliteration here is unusual
    # (h→Х instead of the more common h→Г). Verified via in-corpus
    # textbook front-matter (2026-05-15 audit).
    "hlibovska": "Хлібовська",
    "kovalenko": "Коваленко",
    "onatiy": "Онатій",
    "pometun": "Пометун",
    "savchenko": "Савченко",
    "savchuk": "Савчук",
    "schupak": "Щупак",
    "shchupak": "Щупак",
    "voron": "Ворон",
    # Non-textbook author-name strings already stored in Latin/English on
    # ingestion (literary works, podcast, style-guide author). Map them
    # to Cyrillic so author_uk is uniformly Cyrillic when populated.
    "Anna Ohoiko": "Анна Огоїко",
    "Borys Antonenko-Davydovych": "Борис Антоненко-Давидович",
    "Mykola Pohribnyi": "Микола Погрібний",
    "Ukrainian Lessons Podcast": "Ukrainian Lessons Podcast",
}


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _ensure_column(conn: sqlite3.Connection, *, dry_run: bool) -> bool:
    """Add author_uk column to textbooks if missing. Returns True if added.

    In dry-run mode, returns whether the column WOULD be added but does
    not touch the schema.
    """
    if _has_column(conn, "textbooks", "author_uk"):
        return False
    if not dry_run:
        conn.execute("ALTER TABLE textbooks ADD COLUMN author_uk TEXT DEFAULT ''")
    return True


def _distinct_authors(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT author FROM textbooks WHERE author IS NOT NULL AND author != ''"
    ).fetchall()
    return [row[0] for row in rows]


def _author_uk_for(latin: str) -> str | None:
    """Return canonical Cyrillic form for a stored ``textbooks.author`` value.

    If the input is already Cyrillic (post-migration ingestion), return it
    unchanged. Otherwise look up the Latin key.
    """
    if not latin:
        return None
    if any("Ѐ" <= ch <= "ӿ" for ch in latin):
        return latin
    return _LATIN_TO_UK.get(latin)


def _backfill(
    conn: sqlite3.Connection,
    *,
    dry_run: bool,
    column_exists: bool,
) -> tuple[int, list[str]]:
    """Back-fill author_uk from author. Returns (rows_updated, unmapped).

    If ``column_exists`` is False (dry-run before ALTER TABLE), the
    idempotency filter is skipped — we count all rows with a non-empty
    author as "would update".
    """
    updated_total = 0
    unmapped: list[str] = []
    for author in _distinct_authors(conn):
        author_uk = _author_uk_for(author)
        if author_uk is None:
            unmapped.append(author)
            continue
        if column_exists:
            count_sql = """
                SELECT COUNT(*) FROM textbooks
                WHERE author = ?
                  AND (author_uk IS NULL OR author_uk = '')
            """
        else:
            count_sql = "SELECT COUNT(*) FROM textbooks WHERE author = ?"
        cursor = conn.execute(count_sql, (author,))
        count = int(cursor.fetchone()[0])
        if count == 0:
            continue
        if not dry_run:
            conn.execute(
                """
                UPDATE textbooks SET author_uk = ?
                WHERE author = ?
                  AND (author_uk IS NULL OR author_uk = '')
                """,
                (author_uk, author),
            )
        updated_total += count
    return updated_total, unmapped


def _backfill_orphan_rows_from_source_file(
    conn: sqlite3.Connection,
    *,
    dry_run: bool,
    column_exists: bool,
) -> int:
    """Back-fill author_uk for rows with empty ``author`` by parsing ``source_file``.

    Some legacy textbook chunks were ingested with an empty ``author``
    column (e.g. ``4-klas-ukrmova-zaharijchuk`` — 195 rows with author='').
    The Latin author is embedded in the source_file slug, so we can still
    derive author_uk via the _LATIN_TO_UK bridge with a LIKE match on
    each Latin key.

    Returns the number of rows updated (or that WOULD be updated under dry-run).
    """
    if not column_exists:
        return 0
    updated_total = 0
    for latin, cyrillic in _LATIN_TO_UK.items():
        # source_file slug shape: {N}-klas-{...}-{translit}[-{year-or-suffix}]
        pattern_mid = f"%-{latin}-%"
        pattern_end = f"%-{latin}"
        count = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM textbooks
                WHERE (author IS NULL OR author = '')
                  AND (author_uk IS NULL OR author_uk = '')
                  AND (source_file LIKE ? OR source_file LIKE ?)
                """,
                (pattern_mid, pattern_end),
            ).fetchone()[0]
        )
        if count == 0:
            continue
        if not dry_run:
            conn.execute(
                """
                UPDATE textbooks SET author_uk = ?
                WHERE (author IS NULL OR author = '')
                  AND (author_uk IS NULL OR author_uk = '')
                  AND (source_file LIKE ? OR source_file LIKE ?)
                """,
                (cyrillic, pattern_mid, pattern_end),
            )
        updated_total += count
    return updated_total


def apply(conn: sqlite3.Connection, *, dry_run: bool = False) -> MigrationStatus:
    """Apply the migration idempotently."""
    had_column_before = _has_column(conn, "textbooks", "author_uk")
    column_added = _ensure_column(conn, dry_run=dry_run)
    updated, unmapped = _backfill(
        conn, dry_run=dry_run, column_exists=had_column_before
    )
    updated += _backfill_orphan_rows_from_source_file(
        conn,
        dry_run=dry_run,
        column_exists=had_column_before or not dry_run,
    )
    if not dry_run:
        conn.commit()
    total_rows = int(conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0])
    if had_column_before or not dry_run:
        populated_author_uk = int(
            conn.execute(
                "SELECT COUNT(*) FROM textbooks "
                "WHERE author_uk IS NOT NULL AND author_uk != ''"
            ).fetchone()[0]
        )
    else:
        # Dry-run before column exists: nothing is populated yet.
        populated_author_uk = 0
    return MigrationStatus(
        column_added=column_added,
        rows_updated=updated,
        unmapped_authors=unmapped,
        total_rows=total_rows,
        populated_author_uk=populated_author_uk,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing.",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise SystemExit(f"Sources DB not found: {args.db}")

    with sqlite3.connect(str(args.db)) as conn:
        status = apply(conn, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}column_added={status.column_added}")
    print(f"{prefix}rows_updated={status.rows_updated}")
    print(
        f"{prefix}populated_author_uk={status.populated_author_uk}/"
        f"{status.total_rows} (rows with Cyrillic author_uk / total textbook rows)"
    )
    if status.unmapped_authors:
        print(f"{prefix}WARNING: unmapped Latin authors (no Cyrillic mapping):")
        for name in sorted(status.unmapped_authors):
            print(f"{prefix}  - {name}")
    else:
        print(f"{prefix}all distinct authors mapped to Cyrillic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
