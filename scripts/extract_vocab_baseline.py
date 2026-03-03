#!/usr/bin/env python3
"""
Extract vocabulary baseline from A1 module content using VESUM.

Reads .md content → tokenizes Ukrainian words → verifies against VESUM SQLite
→ generates vocabulary/{slug}.yaml with lemma + pos fields (no translation).

Phase C of the pipeline refines these (adds translations, usage, examples).

Usage:
    .venv/bin/python scripts/extract_vocab_baseline.py a1
    .venv/bin/python scripts/extract_vocab_baseline.py a1 --force   # overwrite existing
    .venv/bin/python scripts/extract_vocab_baseline.py a1 --dry-run # preview only
"""

import argparse
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Setup project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en"
VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"

# POS tags we keep (content words). VESUM uses: noun, verb, adj, adv, numr, ...
KEEP_POS = {"noun", "verb", "adj", "adv"}

# VESUM pos → schema pos mapping
POS_MAP = {
    "noun": "noun",
    "verb": "verb",
    "adj": "adj",
    "adv": "adv",
}

# Maximum vocab items per module (A1 target)
MAX_ITEMS = 30

# Minimum word length to consider (skip single-letter tokens)
MIN_WORD_LEN = 2

# Minimum frequency — word must appear at least this many times in the module
MIN_FREQ = 1


def tokenize_ukrainian(text: str) -> list[str]:
    """Extract Ukrainian word tokens from markdown text."""
    # Strip markdown formatting, links, code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^---$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)

    # Extract Cyrillic words (Ukrainian alphabet)
    tokens = re.findall(r"[а-яіїєґА-ЯІЇЄҐʼ']+", text)
    return [t.lower() for t in tokens if len(t) >= MIN_WORD_LEN]


def lookup_vesum(conn: sqlite3.Connection, word_forms: list[str]) -> dict[str, dict]:
    """
    Batch-lookup word forms in VESUM. Returns lemma → {pos, count} for content words.

    Deduplicates by lemma, keeping the most frequent POS if a lemma has multiple.
    """
    cursor = conn.cursor()
    lemma_counts: Counter = Counter()
    lemma_pos: dict[str, Counter] = {}

    for wf in word_forms:
        cursor.execute(
            "SELECT DISTINCT lemma, pos FROM forms WHERE word_form = ?", (wf,)
        )
        rows = cursor.fetchall()
        for lemma, pos in rows:
            if pos not in KEEP_POS:
                continue
            lemma_counts[lemma] += 1
            if lemma not in lemma_pos:
                lemma_pos[lemma] = Counter()
            lemma_pos[lemma][pos] += 1

    # Build final dict: pick most common POS per lemma
    result = {}
    for lemma, count in lemma_counts.items():
        if count < MIN_FREQ:
            continue
        best_pos = lemma_pos[lemma].most_common(1)[0][0]
        result[lemma] = {"pos": POS_MAP[best_pos], "count": count}

    return result


def generate_vocab_yaml(lemmas: dict[str, dict], max_items: int = MAX_ITEMS) -> dict:
    """Build vocab YAML structure sorted by frequency (most frequent first)."""
    sorted_lemmas = sorted(lemmas.items(), key=lambda x: -x[1]["count"])[:max_items]
    items = []
    for lemma, info in sorted_lemmas:
        items.append({"lemma": lemma, "pos": info["pos"]})
    return {"items": items}


def is_valid_vocab(vocab_path: Path) -> bool:
    """Check if an existing vocab file is valid (parseable with items key)."""
    if not vocab_path.exists():
        return False
    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return isinstance(data, dict) and "items" in data and len(data["items"]) > 0
    except Exception:
        return False


def process_module(
    md_path: Path, vocab_dir: Path, conn: sqlite3.Connection,
    force: bool = False, dry_run: bool = False,
) -> str:
    """Process a single module. Returns status string."""
    slug = md_path.stem
    vocab_path = vocab_dir / f"{slug}.yaml"

    if not force and is_valid_vocab(vocab_path):
        return "SKIP (valid vocab exists)"

    # Read and tokenize
    text = md_path.read_text(encoding="utf-8")
    tokens = tokenize_ukrainian(text)
    if not tokens:
        return "SKIP (no Ukrainian tokens)"

    # Lookup in VESUM
    lemmas = lookup_vesum(conn, tokens)
    if not lemmas:
        return "SKIP (no VESUM matches)"

    # Generate YAML
    vocab_data = generate_vocab_yaml(lemmas)
    item_count = len(vocab_data["items"])

    if dry_run:
        return f"DRY-RUN ({item_count} lemmas)"

    # Write YAML
    vocab_dir.mkdir(parents=True, exist_ok=True)
    with open(vocab_path, "w", encoding="utf-8") as f:
        yaml.dump(
            vocab_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    return f"WROTE ({item_count} lemmas)"


def main():
    parser = argparse.ArgumentParser(description="Extract vocab baseline from module content via VESUM")
    parser.add_argument("level", help="Level directory name (e.g., a1)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing valid vocab files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    level_dir = CURRICULUM / args.level
    if not level_dir.exists():
        print(f"ERROR: Level directory not found: {level_dir}", file=sys.stderr)
        sys.exit(1)

    if not VESUM_DB.exists():
        print(f"ERROR: VESUM database not found: {VESUM_DB}", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(level_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: No .md files found in {level_dir}", file=sys.stderr)
        sys.exit(1)

    vocab_dir = level_dir / "vocabulary"
    conn = sqlite3.connect(str(VESUM_DB))

    wrote = 0
    skipped = 0
    errors = 0

    print(f"Processing {len(md_files)} modules in {args.level}...\n")
    for md_path in md_files:
        try:
            status = process_module(md_path, vocab_dir, conn, args.force, args.dry_run)
            if status.startswith("WROTE") or status.startswith("DRY-RUN"):
                wrote += 1
            else:
                skipped += 1
            print(f"  {md_path.stem:<42} {status}")
        except Exception as e:
            errors += 1
            print(f"  {md_path.stem:<42} ERROR: {e}", file=sys.stderr)

    conn.close()
    print(f"\nDone: {wrote} written | {skipped} skipped | {errors} errors")


if __name__ == "__main__":
    main()
