#!/usr/bin/env python3
"""Import VESUM morphological dictionary into SQLite.

Downloads dict_corp_vis.txt.bz2 from GitHub (v6.7.5, ~17 MB),
parses the visual/indented format, and builds a SQLite database
with ~5-6M inflected forms indexed by word_form and lemma.

Usage:
    .venv/bin/python scripts/rag/import_vesum.py
    .venv/bin/python scripts/rag/import_vesum.py --skip-download  # if file already exists
"""

import argparse
import bz2
import sqlite3
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import VESUM_DB_PATH, VESUM_DIR, VESUM_URL

DICT_FILE = VESUM_DIR / "dict_corp_vis.txt"
BZ2_FILE = VESUM_DIR / "dict_corp_vis.txt.bz2"


def download(url: str, dest: Path) -> None:
    """Download file with progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    print(f"  → {dest}")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            print(f"\r  {mb:.1f}/{total_mb:.1f} MB ({pct}%)", end="", flush=True)

    urllib.request.urlretrieve(url, str(dest), reporthook=reporthook)
    print()


def decompress(bz2_path: Path, out_path: Path) -> None:
    """Decompress .bz2 file."""
    print(f"Decompressing {bz2_path.name}...")
    with bz2.open(bz2_path, "rb") as fin, open(out_path, "wb") as fout:
        while True:
            chunk = fin.read(1024 * 1024)
            if not chunk:
                break
            fout.write(chunk)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  → {out_path} ({size_mb:.1f} MB)")


def parse_line(line: str) -> tuple[str, str] | None:
    """Parse a VESUM line into (word_form, tags).

    Returns None for empty/comment lines.
    Strips inline comments (# ...).
    """
    # Strip inline comments
    if "#" in line:
        line = line[:line.index("#")]
    line = line.rstrip()
    if not line or not line.strip():
        return None

    # Split on whitespace: first token = word_form, rest = tags
    parts = line.split(None, 1)
    if len(parts) < 2:
        return None

    return parts[0], parts[1]


def build_db(dict_path: Path, db_path: Path) -> None:
    """Parse VESUM dict file and build SQLite database."""
    print(f"Building SQLite database at {db_path}...")

    # Remove existing DB
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE forms (
            word_form TEXT NOT NULL,
            lemma TEXT NOT NULL,
            tags TEXT NOT NULL,
            pos TEXT NOT NULL
        )
    """)

    current_lemma = None
    batch = []
    total = 0
    skipped_bad = 0
    batch_size = 50_000

    with open(dict_path, encoding="utf-8") as f:
        for line in f:
            is_indented = line.startswith("  ")
            parsed = parse_line(line)
            if parsed is None:
                continue

            word_form, tags = parsed

            # Skip entries tagged 'bad'
            if "bad" in tags.split(":"):
                skipped_bad += 1
                # Still update lemma if this was a headword
                if not is_indented:
                    current_lemma = word_form
                continue

            # Extract POS (first colon-separated token)
            pos = tags.split(":")[0]

            if not is_indented:
                # New headword = new lemma
                current_lemma = word_form

            lemma = current_lemma or word_form

            batch.append((word_form, lemma, tags, pos))

            if len(batch) >= batch_size:
                cur.executemany(
                    "INSERT INTO forms (word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
                    batch,
                )
                total += len(batch)
                print(f"\r  Inserted {total:,} forms...", end="", flush=True)
                batch.clear()

    # Insert remaining
    if batch:
        cur.executemany(
            "INSERT INTO forms (word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
            batch,
        )
        total += len(batch)

    print(f"\r  Inserted {total:,} forms total.    ")
    print(f"  Skipped {skipped_bad:,} 'bad' entries.")

    # Create indexes
    print("  Creating indexes...")
    cur.execute("CREATE INDEX idx_form ON forms(word_form)")
    cur.execute("CREATE INDEX idx_lemma ON forms(lemma)")

    conn.commit()
    conn.close()

    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"  Database ready: {size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Import VESUM dictionary into SQLite")
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download if dict file already exists",
    )
    args = parser.parse_args()

    # Step 1: Download and decompress
    if DICT_FILE.exists() and args.skip_download:
        print(f"Using existing {DICT_FILE}")
    else:
        if not BZ2_FILE.exists():
            download(VESUM_URL, BZ2_FILE)
        decompress(BZ2_FILE, DICT_FILE)

    # Step 2: Build SQLite
    build_db(DICT_FILE, VESUM_DB_PATH)

    # Step 3: Quick verification
    conn = sqlite3.connect(str(VESUM_DB_PATH))
    cur = conn.cursor()
    count = cur.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
    lemma_count = cur.execute("SELECT COUNT(DISTINCT lemma) FROM forms").fetchone()[0]
    print(f"\nVerification:")
    print(f"  Total forms: {count:,}")
    print(f"  Distinct lemmas: {lemma_count:,}")

    # Test lookups
    test_words = ["берізонька", "горонька", "слізонька", "коза", "кіт"]
    for word in test_words:
        rows = cur.execute(
            "SELECT lemma, pos, tags FROM forms WHERE word_form = ?", (word,)
        ).fetchall()
        status = f"✅ found ({len(rows)} match{'es' if len(rows) != 1 else ''})" if rows else "❌ not found"
        print(f"  '{word}': {status}")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
