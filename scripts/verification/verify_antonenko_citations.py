"""Audit every admitted pattern's literal anchor against its cited book chunk.

Run from the import root with the task-prescribed project interpreter:
-m scripts.verification.verify_antonenko_citations [--database PATH].
The database is opened read-only; neither corpus text nor private paths are
printed. This checks citation presence, not the semantic validity of a rule.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from lib.readonly_sqlite import SQLiteConnection, open_readonly  # type: ignore[no-redef]

from scripts.verification.antonenko_citations import EVIDENCE_FORMS
from scripts.verification.antonenko_patterns import PATTERNS, SOURCE_FILE, PhrasePattern
from scripts.verification.check_text import _sources_path_resolved


def normalize(text: str) -> str:
    """Ignore line wrapping, case, apostrophe and dash typography only."""
    return " ".join(text.casefold().translate(str.maketrans("’ʼ`‘–‑‐", "''''---")).split())


def audit_citations(conn: SQLiteConnection, patterns: tuple[PhrasePattern, ...] = PATTERNS) -> dict:
    """Fail on absent/wrong-source chunks, absent anchors, or inventory drift."""
    failures = []
    expected = {p.id for p in patterns}
    for orphan in sorted(set(EVIDENCE_FORMS) - expected):
        failures.append({"pattern_id": orphan, "reason": "orphan_anchor"})
    for pattern in patterns:
        row = conn.execute("SELECT source_file, text FROM textbooks WHERE chunk_id = ?", (pattern.chunk_id,)).fetchone()
        anchor = EVIDENCE_FORMS.get(pattern.id)
        if row is None:
            reason = "missing_chunk"
        elif row[0] != SOURCE_FILE:
            reason = "wrong_source"
        elif not anchor:
            reason = "missing_anchor"
        elif normalize(anchor) not in normalize(row[1]):
            reason = "absent_form"
        else:
            continue
        failures.append({"pattern_id": pattern.id, "chunk_id": pattern.chunk_id, "reason": reason})
    failed_patterns = {f["pattern_id"] for f in failures} & expected
    return {
        "patterns": len(patterns),
        "chunks": len({p.chunk_id for p in patterns}),
        "verified": len(patterns) - len(failed_patterns),
        "failures": failures,
    }


def main() -> int:
    """Print a privacy-safe receipt and exit nonzero when citations fail."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=None, help="Sources SQLite database (read-only).")
    args = parser.parse_args()
    path = args.database or _sources_path_resolved()
    with open_readonly(path) as conn:
        result = audit_citations(conn)
    print(json.dumps(result, ensure_ascii=False))
    return int(bool(result["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
