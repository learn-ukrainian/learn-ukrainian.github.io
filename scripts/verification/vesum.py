"""VESUM SQLite lookup helpers.

This module owns the local VESUM morphological dictionary connection and the
public verification API previously embedded in ``scripts.rag.query``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.rag.config import VESUM_DB_PATH

_vesum_conn = None


def get_vesum_conn():
    """Lazy-load SQLite connection to VESUM dictionary."""
    global _vesum_conn
    if _vesum_conn is None:
        import sqlite3

        if not VESUM_DB_PATH.exists():
            raise FileNotFoundError(
                f"VESUM database not found at {VESUM_DB_PATH}. "
                "Run: .venv/bin/python scripts/rag/import_vesum.py"
            )
        _vesum_conn = sqlite3.connect(str(VESUM_DB_PATH), check_same_thread=False)
        _vesum_conn.row_factory = sqlite3.Row
    return _vesum_conn


def verify_word(word: str, pos_filter: str | None = None) -> list[dict]:
    """Check if a word form exists in VESUM.

    Returns list of {lemma, pos, tags} matches. Empty list = not found.
    """
    conn = get_vesum_conn()
    if pos_filter:
        rows = conn.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form = ? AND pos = ?",
            (word, pos_filter),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form = ?",
            (word,),
        ).fetchall()
    return [{"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


def verify_words(words: list[str], pos_filter: str | None = None) -> dict[str, list[dict]]:
    """Batch-verify multiple word forms against VESUM in a single query.

    Returns dict mapping each word to its list of matches.
    Words not found map to an empty list.
    """
    if not words:
        return {}
    conn = get_vesum_conn()
    placeholders = ",".join("?" * len(words))
    if pos_filter:
        rows = conn.execute(
            f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders}) AND pos = ?",
            (*words, pos_filter),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders})",
            words,
        ).fetchall()
    result: dict[str, list[dict]] = {w: [] for w in words}
    for r in rows:
        result[r["word_form"]].append({"lemma": r["lemma"], "pos": r["pos"], "tags": r["tags"]})
    return result


def verify_lemma(lemma: str) -> list[dict]:
    """Get all inflected forms of a lemma.

    Returns list of {word_form, pos, tags} for every form.
    """
    conn = get_vesum_conn()
    rows = conn.execute(
        "SELECT word_form, pos, tags FROM forms WHERE lemma = ? ORDER BY pos, tags",
        (lemma,),
    ).fetchall()
    return [{"word_form": r["word_form"], "pos": r["pos"], "tags": r["tags"]} for r in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the VESUM morphological dictionary")
    subparsers = parser.add_subparsers(dest="command", required=True)

    word_parser = subparsers.add_parser("word", help="Verify a Ukrainian word form")
    word_parser.add_argument("query", help="Word form to check")
    word_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    word_parser.add_argument("--json", action="store_true", help="Print raw JSON")

    words_parser = subparsers.add_parser("words", help="Batch-verify Ukrainian word forms")
    words_parser.add_argument("query", nargs="+", help="Word forms to check")
    words_parser.add_argument("--pos", type=str, help="Filter by POS, e.g. noun, verb, adj")
    words_parser.add_argument("--json", action="store_true", help="Print raw JSON")

    lemma_parser = subparsers.add_parser("lemma", help="Get all forms of a lemma")
    lemma_parser.add_argument("query", help="Lemma to look up")
    lemma_parser.add_argument("--json", action="store_true", help="Print raw JSON")

    args = parser.parse_args()

    if args.command == "word":
        matches = verify_word(args.query, pos_filter=args.pos)
        if args.json:
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        elif not matches:
            print(f"'{args.query}' not found in VESUM")
        else:
            print(f"'{args.query}' - {len(matches)} match(es):")
            for match in matches:
                print(
                    f"  lemma={match['lemma']}  pos={match['pos']}  "
                    f"tags={match['tags']}"
                )
    elif args.command == "words":
        results = verify_words(args.query, pos_filter=args.pos)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            found = sum(1 for matches in results.values() if matches)
            print(f"Found: {found}/{len(args.query)}")
            for word in args.query:
                matches = results.get(word, [])
                status = "FOUND" if matches else "NOT FOUND"
                print(f"{word}: {status}")
    elif args.command == "lemma":
        forms = verify_lemma(args.query)
        if args.json:
            print(json.dumps(forms, ensure_ascii=False, indent=2))
        elif not forms:
            print(f"Lemma '{args.query}' not found in VESUM")
        else:
            print(f"'{args.query}' - {len(forms)} form(s):")
            for form in forms:
                print(f"  {form['word_form']:20s}  {form['tags']}")


if __name__ == "__main__":
    main()
