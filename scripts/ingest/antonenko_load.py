import argparse
import json
import sqlite3
import sys


def main():
    parser = argparse.ArgumentParser(description="Load Antonenko-Davydovych data into SQLite")
    parser.add_argument("--input", required=True, help="Input jsonl file")
    parser.add_argument("--db", default="data/sources.db", help="Path to sources.db")
    args = parser.parse_args()

    # Connect to the DB
    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    # Run the migration
    with open("migrations/expand_antonenko_table.sql", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # Load data
    inserted = 0
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)

            # Idempotent insert
            try:
                cursor.execute("""
                    INSERT INTO style_guide (word, word_lower, section, text, source, excerpt_full, page)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(word, page) DO UPDATE SET
                        text=excluded.text,
                        excerpt_full=excluded.excerpt_full
                """, (
                    item["headword"],
                    item["headword"].lower(),
                    "", # section
                    item["source_excerpt"],
                    'Антоненко-Давидович "Як ми говоримо"',
                    item["commentary"],
                    item["page"]
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting {item['headword']}: {e}", file=sys.stderr)

    conn.commit()
    conn.close()

    print(f"Loaded {inserted} items into style_guide table.")

if __name__ == "__main__":
    main()
