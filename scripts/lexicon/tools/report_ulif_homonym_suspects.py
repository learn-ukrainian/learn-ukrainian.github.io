#!/usr/bin/env python3
"""Read-only list of homonym-suspect spellings in the legacy ULIF dump.

A spelling is suspect when any of these hold for an ``ok`` row in
``ulif_entries``:

* the ``ukrainian-word-stress`` trie has more than one reading with different
  stress positions;
* VESUM has more than one distinct lemma/sense ``source_comment`` on that
  word form;
* the stored ``canonical_headword``, with stress marks removed, differs from
  the query only by capitalisation.

The legacy ``ulif_entries`` table is opened ``mode=ro`` and is not modified.
The spelling list is written under ``batch_state/`` (gitignored).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import unicodedata
from collections.abc import Callable, Iterable
from pathlib import Path

REASON_TRIE = "trie_stress"
REASON_VESUM = "vesum_comment"
REASON_CASE = "capitalisation"


def _connect_readonly(path: Path) -> sqlite3.Connection:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _strip_marks(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def capitalisation_differs(lemma: str, canonical_headword: str) -> bool:
    """True when the stressed headword and the query differ only by case."""
    if not canonical_headword:
        return False
    bare = " ".join(_strip_marks(canonical_headword).split())
    query = " ".join(lemma.split())
    return bare.casefold() == query.casefold() and bare != query


def vesum_multi_comment_spellings(conn: sqlite3.Connection) -> set[str]:
    """Word forms that carry more than one distinct non-empty VESUM comment."""
    rows = conn.execute(
        """
        SELECT word_form
        FROM forms_all
        WHERE source_comment IS NOT NULL AND TRIM(source_comment) != ''
        GROUP BY word_form
        HAVING COUNT(DISTINCT source_comment) > 1
        """
    )
    return {str(row[0]) for row in rows}


def collect_suspects(
    entries: Iterable[tuple[str, str]],
    *,
    vesum_comments: set[str],
    stress_position_sets: Callable[[str], set[tuple[int, ...]]],
) -> list[tuple[str, str]]:
    """Return sorted ``(spelling, reason-list)`` rows.

    ``stress_position_sets`` returns the distinct stress-position tuples for
    one spelling. More than one tuple means the trie cannot treat the spelling
    as a single reading.
    """
    found: dict[str, set[str]] = {}
    for lemma, canonical in entries:
        spelling = " ".join(lemma.split())
        if not spelling:
            continue
        reasons = found.setdefault(spelling, set())
        if capitalisation_differs(spelling, canonical):
            reasons.add(REASON_CASE)
        if spelling in vesum_comments:
            reasons.add(REASON_VESUM)
        positions = stress_position_sets(spelling)
        if len(positions) > 1:
            reasons.add(REASON_TRIE)
    listed = [(spelling, ",".join(sorted(reasons))) for spelling, reasons in found.items() if reasons]
    listed.sort()
    return listed


def _trie_position_sets() -> Callable[[str], set[tuple[int, ...]]]:
    """Return distinct stress-position tuples from the offline stress trie."""
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.verification.stress import _load_trie, _parse_dictionary_value, _trie_value

    trie = _load_trie()
    cache: dict[str, set[tuple[int, ...]]] = {}

    def positions(spelling: str) -> set[tuple[int, ...]]:
        cached = cache.get(spelling)
        if cached is not None:
            return cached
        value = _trie_value(trie, spelling)
        if value is None:
            found: set[tuple[int, ...]] = set()
        else:
            found = {tuple(accents) for _tags, accents in _parse_dictionary_value(value)}
        cache[spelling] = found
        return found

    return positions


def load_ok_entries(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    rows = conn.execute(
        """
        SELECT lemma, canonical_headword
        FROM ulif_entries
        WHERE status = 'ok'
        ORDER BY lemma
        """
    )
    return [(str(row[0]), str(row[1] or "")) for row in rows]


def write_report(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"{spelling}\t{reasons}\n" for spelling, reasons in rows)
    path.write_text(body, encoding="utf-8")


def build_report(
    dump_path: Path,
    vesum_path: Path,
    out_path: Path,
    *,
    stress_position_sets: Callable[[str], set[tuple[int, ...]]] | None = None,
) -> int:
    """Read both databases read-only, write the suspect list, and return the count."""
    dump = _connect_readonly(dump_path)
    vesum = _connect_readonly(vesum_path)
    try:
        entries = load_ok_entries(dump)
        comments = vesum_multi_comment_spellings(vesum)
    finally:
        dump.close()
        vesum.close()
    positions = stress_position_sets or _trie_position_sets()
    rows = collect_suspects(entries, vesum_comments=comments, stress_position_sets=positions)
    write_report(out_path, rows)
    print(f"homonym_suspect_count={len(rows)}")
    print(f"wrote {out_path}")
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, required=True, help="Legacy ulif_dump SQLite (read-only)")
    parser.add_argument("--vesum", type=Path, required=True, help="VESUM SQLite (read-only)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("batch_state/ulif-homonym-suspects.txt"),
        help="Gitignored report path",
    )
    args = parser.parse_args(argv)
    try:
        build_report(args.dump, args.vesum, args.out)
    except FileNotFoundError as exc:
        print(f"missing database: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
