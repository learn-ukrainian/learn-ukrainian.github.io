#!/usr/bin/env python3
"""Determine contested calque items in the UA-GEC gold fixture.

This script implements a deterministic heritage-defense rule to flag gold calque
items where the original (flagged) form is attested as native/valid Ukrainian
in local lexicographic databases.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def is_archaic(tags: str | None) -> bool:
    """Helper to check if 'arch' tag exists in VESUM tag string."""
    if not tags:
        return False
    return "arch" in tags.split(":")


def get_vesum_lemmas(conn_v: sqlite3.Connection, word: str) -> set[str]:
    """Query vesum database for non-archaic lemmas for the given word form."""
    lemmas = set()
    for q in (word, word.lower()):
        try:
            rows = conn_v.execute(
                "SELECT lemma, tags FROM forms WHERE word_form = ?",
                (q,),
            ).fetchall()
            for r in rows:
                if not is_archaic(r["tags"]):
                    lemmas.add(r["lemma"])
        except sqlite3.OperationalError:
            pass
    return lemmas


def escape_fts5_phrase(term: str) -> str:
    """Build a safe FTS5 phrase query for a term."""
    cleaned = term.replace('"', " ").strip()
    if not cleaned:
        return ""
    return f'"{cleaned}"'


def get_heritage_evidence(conn_s: sqlite3.Connection, word: str, lemmas: set[str]) -> list[dict[str, str]]:
    """Query sources database for headword attestation in Grinchenko or ESUM."""
    evidence = []
    queries = {word} | lemmas
    for q in queries:
        if not q:
            continue

        # 1. Grinchenko check
        try:
            rows = conn_s.execute(
                "SELECT word FROM grinchenko WHERE word = ? COLLATE NOCASE",
                (q,),
            ).fetchall()
            for r in rows:
                evidence.append({"table": "grinchenko", "headword": r["word"]})

            if not rows:
                rows = conn_s.execute(
                    "SELECT word FROM grinchenko WHERE word LIKE ? COLLATE NOCASE LIMIT 5",
                    (f"{q}%",),
                ).fetchall()
                for r in rows:
                    evidence.append({"table": "grinchenko", "headword": r["word"]})
        except sqlite3.OperationalError:
            pass

        # 2. ESUM exact check
        try:
            rows = conn_s.execute(
                "SELECT lemma FROM esum_etymology_meta WHERE lemma = ? COLLATE NOCASE",
                (q,),
            ).fetchall()
            for r in rows:
                evidence.append({"table": "esum", "headword": r["lemma"]})
        except sqlite3.OperationalError:
            pass

        # 3. ESUM FTS check
        fts_q = escape_fts5_phrase(q)
        if fts_q:
            try:
                rows = conn_s.execute(
                    "SELECT lemma FROM esum_etymology WHERE esum_etymology MATCH ? LIMIT 5",
                    (fts_q,),
                ).fetchall()
                for r in rows:
                    evidence.append({"table": "esum", "headword": r["lemma"]})
            except sqlite3.OperationalError:
                pass

    # Deduplicate and sort to guarantee byte-identical sidecars
    seen = set()
    unique_evidence = []
    for ev in evidence:
        key = (ev["table"], ev["headword"])
        if key not in seen:
            seen.add(key)
            unique_evidence.append(ev)
    unique_evidence.sort(key=lambda x: (x["table"], x["headword"]))
    return unique_evidence


def process_fixture(
    fixture_path: Path,
    vesum_db: Path,
    sources_db: Path,
) -> dict[str, Any]:
    """Process a gold fixture and identify contested items."""
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found at {fixture_path}")

    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    sidecar: dict[str, Any] = {}

    conn_v = sqlite3.connect(str(vesum_db))
    conn_v.row_factory = sqlite3.Row
    conn_s = sqlite3.connect(str(sources_db))
    conn_s.row_factory = sqlite3.Row

    try:
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue

            # Only flag F/Calque items
            if item.get("tag") != "F/Calque":
                sidecar[item_id] = {"contested": False, "evidence": []}
                continue

            error_form = item.get("error", "")
            lemmas = get_vesum_lemmas(conn_v, error_form)
            if not lemmas:
                sidecar[item_id] = {"contested": False, "evidence": []}
                continue

            evidence = get_heritage_evidence(conn_s, error_form, lemmas)
            is_contested = len(evidence) > 0
            sidecar[item_id] = {
                "contested": is_contested,
                "evidence": evidence,
            }
    finally:
        conn_v.close()
        conn_s.close()

    return sidecar


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-path",
        type=Path,
        default=PROJECT_ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json",
        help="Path to the gold fixture JSON file.",
    )
    parser.add_argument(
        "--vesum-db",
        type=Path,
        default=PROJECT_ROOT / "data" / "vesum.db",
        help="Path to vesum.db.",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=PROJECT_ROOT / "data" / "sources.db",
        help="Path to sources.db.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Custom path to write the sidecar JSON. Defaults to <fixture>.contested.json next to fixture.",
    )

    args = parser.parse_args()

    try:
        sidecar = process_fixture(
            args.fixture_path,
            args.vesum_db,
            args.sources_db,
        )
    except Exception as e:
        print(f"Error processing fixture: {e}", file=sys.stderr)
        return 1

    output_path = args.output or args.fixture_path.with_suffix(".contested.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort keys for stable ordering
    sorted_sidecar = {k: sidecar[k] for k in sorted(sidecar.keys())}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_sidecar, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote sidecar to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
