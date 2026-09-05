"""Read-only SQLite census for #4593; presence is not curriculum completeness."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

SUBJECTS = (
    "algebra", "fizyka", "khimiya", "matematyka", "informatyka", "biolohiya", "heohrafiya",
)
PROBES = ("алгоритм", "рівняння", "фотосинтез", "валентність", "прискорення")


def census(db_path: Path) -> dict:
    """Read one consistent snapshot, without creating or modifying the database.

    All-grade totals reproduce the driver census. The separate 5–11 grid
    deliberately reports absence without calling every cell a required book:
    subject start grades and integrated alternatives belong to the curriculum
    denominator, not to an observed SQLite row count.
    """
    conn = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("BEGIN")
        total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
        subjects = {}
        for subject in SUBJECTS:
            rows = conn.execute(
                "SELECT source_file, grade, COUNT(*) FROM textbooks "
                "WHERE subject = ? GROUP BY source_file, grade ORDER BY source_file, grade",
                (subject,),
            ).fetchall()
            grades = {}
            for grade in range(5, 12):
                matching = [row for row in rows if str(row[1]) == str(grade)]
                grades[str(grade)] = {
                    "files": len({row[0] for row in matching}),
                    "chunks": sum(row[2] for row in matching),
                }
            subjects[subject] = {
                "files": len({row[0] for row in rows}),
                "chunks": sum(row[2] for row in rows),
                "grades_5_11": grades,
                "absent_grades_5_11": [int(g) for g, counts in grades.items() if not counts["chunks"]],
                "sources": [
                    {"source_file": source, "grade": grade, "chunks": count}
                    for source, grade, count in rows
                ],
            }
        probes = {}
        placeholders = ",".join("?" for _ in SUBJECTS)
        for term in PROBES:
            probes[term] = {
                "all_textbooks": conn.execute(
                    "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH ?", (term,),
                ).fetchone()[0],
                "stem_grades_5_11": conn.execute(
                    "SELECT COUNT(*) FROM textbooks_fts JOIN textbooks t ON t.id = textbooks_fts.rowid "
                    f"WHERE textbooks_fts MATCH ? AND t.subject IN ({placeholders}) "
                    "AND t.grade IN ('5','6','7','8','9','10','11')",
                    (term, *SUBJECTS),
                ).fetchone()[0],
            }
        return {
            "schema_version": "stem_sqlite_census.v1",
            "observed_at": datetime.now(UTC).isoformat(),
            "scope": "SQLite presence and FTS hits only; not edition, text-quality, or curriculum-completeness proof",
            "grade_denominator": "data/textbook_curriculum_denominator.yaml",
            "total_textbook_chunks": total,
            "subjects": subjects,
            "fts_probes": probes,
        }
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report live STEM source files, subject/grade counts, and FTS probes.\n"
            "Use for #4593 evidence, not to certify full curriculum or source quality."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.ingest.verify_stem_coverage "
            "--db /home/ops/learn-ukrainian/data/sources.db\n"
            "Outputs: JSON on stdout; no files written or database changes.\n"
            "Exit codes: 0 = census read successfully (gaps may remain); 2 = database/read failure.\n"
            "Related: #4593; scripts/ingest/incremental_textbook_ingest.py; "
            "data/textbook_curriculum_denominator.yaml"
        ),
    )
    parser.add_argument(
        "--db", type=Path, required=True,
        help="Existing SQLite sources database; required, no implicit worktree copy (e.g. /path/to/sources.db)",
    )
    args = parser.parse_args(argv)
    try:
        report = census(args.db)
    except (sqlite3.Error, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
