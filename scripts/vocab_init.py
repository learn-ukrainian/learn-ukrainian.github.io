#!/usr/bin/env python3
"""
vocab_init.py

Initialize a fresh SQLite vocabulary database for curriculum.

Usage:
    python3 scripts/vocab_init.py [curriculum] [--force]

Examples:
    python3 scripts/vocab_init.py l2-uk-en
    python3 scripts/vocab_init.py l2-uk-en --force

Creates:
    curriculum/{curriculum}/vocabulary.db
"""

import sqlite3
import sys
import os
from pathlib import Path

# Configuration
CURRICULUM_DIR = Path(__file__).parent.parent / "curriculum"
DEFAULT_CURRICULUM = "l2-uk-en"

# Database Schema
SCHEMA = """
-- Lemmas: single words
CREATE TABLE IF NOT EXISTS lemmas (
  id TEXT PRIMARY KEY,
  uk TEXT UNIQUE NOT NULL,
  ipa TEXT,
  en TEXT,
  pos TEXT DEFAULT 'noun',
  gender TEXT,
  first_module INTEGER,
  level TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Expressions: multi-word units (idioms, collocations, phrases)
CREATE TABLE IF NOT EXISTS expressions (
  id TEXT PRIMARY KEY,
  uk TEXT UNIQUE NOT NULL,
  ipa TEXT,
  en TEXT,
  type TEXT DEFAULT 'phrase',  -- idiom, collocation, phrase, proverb
  literal_en TEXT,             -- literal translation for idioms
  register TEXT DEFAULT 'neutral',  -- formal, informal, neutral
  first_module INTEGER,
  level TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Expression components: links expressions to their component lemmas
CREATE TABLE IF NOT EXISTS expression_components (
  expression_id TEXT NOT NULL REFERENCES expressions(id) ON DELETE CASCADE,
  lemma_id TEXT REFERENCES lemmas(id) ON DELETE SET NULL,
  word TEXT NOT NULL,          -- The word as it appears (may differ from lemma)
  position INTEGER NOT NULL,   -- Word position in expression (0-indexed)
  PRIMARY KEY (expression_id, position)
);

-- Module vocabulary: tracks which vocab appears in which modules
CREATE TABLE IF NOT EXISTS module_vocabulary (
  module_num INTEGER NOT NULL,
  entry_type TEXT NOT NULL,    -- 'lemma' or 'expression'
  entry_id TEXT NOT NULL,
  is_new INTEGER DEFAULT 1,    -- 1 if first introduced, 0 if review
  PRIMARY KEY (module_num, entry_type, entry_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_lemmas_uk ON lemmas(uk);
CREATE INDEX IF NOT EXISTS idx_lemmas_first_module ON lemmas(first_module);
CREATE INDEX IF NOT EXISTS idx_lemmas_level ON lemmas(level);

CREATE INDEX IF NOT EXISTS idx_expressions_uk ON expressions(uk);
CREATE INDEX IF NOT EXISTS idx_expressions_first_module ON expressions(first_module);
CREATE INDEX IF NOT EXISTS idx_expressions_type ON expressions(type);

CREATE INDEX IF NOT EXISTS idx_expr_components_lemma ON expression_components(lemma_id);
CREATE INDEX IF NOT EXISTS idx_module_vocab_module ON module_vocabulary(module_num);

-- Trigger to update updated_at on lemmas
CREATE TRIGGER IF NOT EXISTS lemmas_updated_at
  AFTER UPDATE ON lemmas
  BEGIN
    UPDATE lemmas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
  END;

-- Trigger to update updated_at on expressions
CREATE TRIGGER IF NOT EXISTS expressions_updated_at
  AFTER UPDATE ON expressions
  BEGIN
    UPDATE expressions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
  END;
"""


def main():
    """Initialize vocabulary database."""
    # Parse arguments
    args = sys.argv[1:]
    curriculum = args[0] if args and not args[0].startswith('--') else DEFAULT_CURRICULUM
    force = '--force' in args

    curriculum_path = CURRICULUM_DIR / curriculum
    db_path = curriculum_path / "vocabulary.db"

    # Validate curriculum path
    if not curriculum_path.exists():
        print(f"Error: Curriculum not found: {curriculum_path}")
        sys.exit(1)

    # Check if database exists
    if db_path.exists():
        if force:
            print(f"Removing existing database: {db_path}\n")
            db_path.unlink()
        else:
            print(f"Error: Database already exists: {db_path}")
            print("Use --force to overwrite.")
            sys.exit(1)

    print("=== Vocabulary Database Initialization ===\n")
    print(f"Curriculum: {curriculum}")
    print(f"Database: {db_path}\n")

    # Create database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")

    # Create schema
    print("Creating schema...")
    conn.executescript(SCHEMA)
    conn.commit()

    # Verify tables
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    print("\nCreated tables:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  - {table} ({count} rows)")

    # Show indexes
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%' 
        ORDER BY name
    """)
    indexes = [row[0] for row in cursor.fetchall()]

    print("\nCreated indexes:")
    for index in indexes:
        print(f"  - {index}")

    conn.close()

    print(f"\n✅ Database initialized: {db_path}")
    print("\nNext steps:")
    print("  1. Run vocab:scan to populate from module MDs")
    print("  2. Run vocab:enrich to update MDs from DB")
    print("\n=== Done ===\n")


if __name__ == "__main__":
    main()
