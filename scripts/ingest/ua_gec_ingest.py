"""
Ingest UA-GEC (Ukrainian Grammatical Error Corpus) error pairs into sources.db.
Source: ua-gec by Grammarly Ukraine, MIT licensed.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from ua_gec import Corpus

# Confirmed from H2 PR #2049: F/Style dropped.
INCLUDED_TAGS = {"F/Calque", "F/Collocation", "G/Case", "G/Gender"}

def ingest(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")

        # Create table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ua_gec_errors (
                id INTEGER PRIMARY KEY,
                error TEXT NOT NULL,
                correct TEXT NOT NULL,
                error_type TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                annotator_id TEXT NOT NULL,
                partition TEXT NOT NULL,
                is_native INTEGER,
                source_lang TEXT
            )
        """)

        # Create FTS5 table
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS ua_gec_errors_fts
            USING fts5(error, correct, error_type, content='ua_gec_errors', content_rowid='id', tokenize='unicode61')
        """)

        # Triggers to keep FTS in sync
        conn.execute("DROP TRIGGER IF EXISTS ua_gec_errors_ai")
        conn.execute("DROP TRIGGER IF EXISTS ua_gec_errors_ad")
        conn.execute("DROP TRIGGER IF EXISTS ua_gec_errors_au")

        conn.execute("""
            CREATE TRIGGER ua_gec_errors_ai AFTER INSERT ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type)
                VALUES (new.id, new.error, new.correct, new.error_type);
            END
        """)
        conn.execute("""
            CREATE TRIGGER ua_gec_errors_ad AFTER DELETE ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(ua_gec_errors_fts, rowid, error, correct, error_type)
                VALUES('delete', old.id, old.error, old.correct, old.error_type);
            END
        """)
        conn.execute("""
            CREATE TRIGGER ua_gec_errors_au AFTER UPDATE ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(ua_gec_errors_fts, rowid, error, correct, error_type)
                VALUES('delete', old.id, old.error, old.correct, old.error_type);
                INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type)
                VALUES (new.id, new.error, new.correct, new.error_type);
            END
        """)

        # Clean existing data for idempotency
        conn.execute("DELETE FROM ua_gec_errors")
        conn.execute("DELETE FROM ua_gec_errors_fts")

        rows = 0
        # Iterate through all partitions and layers
        for layer in ("gec-only", "gec-fluency"):
            for partition in ("train", "test"):
                corpus = Corpus(partition=partition, annotation_layer=layer)
                for doc in corpus:
                    for ann in doc.annotated.iter_annotations():
                        if ann.meta.get("error_type") not in INCLUDED_TAGS:
                            continue

                        conn.execute(
                            "INSERT INTO ua_gec_errors(error, correct, error_type, doc_id, annotator_id, partition, is_native, source_lang) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (ann.source_text, ann.top_suggestion, ann.meta["error_type"],
                             doc.meta.doc_id, doc.meta.annotator_id, f"{layer}/{partition}",
                             int(doc.meta.is_native if doc.meta.is_native is not None else 0),
                             doc.meta.source_language)
                        )
                        rows += 1

        conn.commit()

        # Optimization
        conn.execute("INSERT INTO ua_gec_errors_fts(ua_gec_errors_fts) VALUES('optimize')")
        conn.commit()

        return rows
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest UA-GEC errors into sources.db")
    parser.add_argument("--db", type=Path, required=True, help="Path to sources.db")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Error: Database {args.db} does not exist.")
        sys.exit(1)

    print(f"Starting ingestion into {args.db}...")
    inserted_rows = ingest(args.db)
    print(f"Successfully ingested {inserted_rows} error pairs.")
