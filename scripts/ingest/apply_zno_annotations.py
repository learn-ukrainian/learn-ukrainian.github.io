#!/usr/bin/env python3
"""
Apply zno_annotations from a worksheet YAML file to the zno_tasks table in sources.db.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply zno_annotations to zno_tasks table in sources.db.")
    parser.add_argument(
        "--db",
        required=True,
        help="Path to the SQLite database file (e.g. data/sources.db)",
    )
    parser.add_argument(
        "--worksheet",
        required=True,
        help="Path to the paronym worksheet YAML file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to database; print planned updates and sample rows.",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    worksheet_path = Path(args.worksheet)

    if not db_path.exists():
        print(f"Error: Database file does not exist: {db_path}", file=sys.stderr)
        return 1

    if not worksheet_path.exists():
        print(f"Error: Worksheet file does not exist: {worksheet_path}", file=sys.stderr)
        return 1

    # Load worksheet
    try:
        with open(worksheet_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error parsing worksheet YAML: {e}", file=sys.stderr)
        return 1

    if not data or "zno_annotations" not in data:
        print("Error: 'zno_annotations' key missing from worksheet", file=sys.stderr)
        return 1

    annotations = data["zno_annotations"]

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT id, topic_norm, task_subtype, paronym_pair, stress_word FROM zno_tasks")
        db_tasks = {
            row[0]: {
                "topic_norm": row[1] or "",
                "task_subtype": row[2] or "",
                "paronym_pair": row[3] or "",
                "stress_word": row[4] or "",
            }
            for row in cursor.fetchall()
        }
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}", file=sys.stderr)
        conn.close()
        return 1

    updated_count = 0
    skipped_count = 0
    conflict_count = 0

    updates_to_apply = []
    conflicts_found = []

    for annotation in annotations:
        task_id = annotation.get("id")
        if task_id is None:
            continue

        if task_id not in db_tasks:
            # Task not found in DB - might be a test/trimmed DB, skip
            continue

        db_row = db_tasks[task_id]

        prop_topic_norm = annotation.get("topic_norm")
        prop_task_subtype = annotation.get("task_subtype")
        prop_paronym_pair = annotation.get("paronym_pair")
        prop_stress_word = annotation.get("stress_word")

        prop_topic_norm_norm = prop_topic_norm if prop_topic_norm is not None else ""
        prop_task_subtype_norm = prop_task_subtype if prop_task_subtype is not None else ""
        prop_paronym_pair_norm = prop_paronym_pair if prop_paronym_pair is not None else ""
        prop_stress_word_norm = prop_stress_word if prop_stress_word is not None else ""

        has_conflict = False
        has_diff = False

        for col, prop_norm in [
            ("topic_norm", prop_topic_norm_norm),
            ("task_subtype", prop_task_subtype_norm),
            ("paronym_pair", prop_paronym_pair_norm),
            ("stress_word", prop_stress_word_norm),
        ]:
            db_norm = db_row[col]

            if db_norm != prop_norm:
                if db_norm == "":
                    has_diff = True
                else:
                    has_conflict = True
                    conflicts_found.append(
                        {
                            "id": task_id,
                            "column": col,
                            "db_value": db_norm,
                            "proposed_value": prop_norm,
                        }
                    )

        if has_conflict:
            conflict_count += 1
        elif has_diff:
            updated_count += 1
            updates_to_apply.append(
                (
                    prop_topic_norm_norm,
                    prop_task_subtype_norm,
                    prop_paronym_pair_norm,
                    prop_stress_word_norm,
                    task_id,
                )
            )
        else:
            skipped_count += 1

    # Print conflicts if any
    if conflicts_found:
        print("Conflicts detected:", file=sys.stderr)
        for conflict in conflicts_found:
            print(
                f"  Task ID {conflict['id']}, column '{conflict['column']}': "
                f"DB has '{conflict['db_value']}', proposed is '{conflict['proposed_value']}'",
                file=sys.stderr,
            )
        print(f"Summary: {updated_count} updated / {skipped_count} skipped-identical / {conflict_count} conflicts")
        conn.close()
        return 2

    # Print summary line
    print(f"Summary: {updated_count} updated / {skipped_count} skipped-identical / {conflict_count} conflicts")

    if args.dry_run:
        print(f"Planned updates: {updated_count}")
        if updated_count > 0:
            print("Sample updates (up to 5):")
            for prop_topic_norm, prop_task_subtype, prop_paronym_pair, prop_stress_word, task_id in updates_to_apply[
                :5
            ]:
                orig = db_tasks[task_id]
                changes = []
                if orig["topic_norm"] != prop_topic_norm:
                    changes.append(f"topic_norm: '{orig['topic_norm']}' -> '{prop_topic_norm}'")
                if orig["task_subtype"] != prop_task_subtype:
                    changes.append(f"task_subtype: '{orig['task_subtype']}' -> '{prop_task_subtype}'")
                if orig["paronym_pair"] != prop_paronym_pair:
                    changes.append(f"paronym_pair: '{orig['paronym_pair']}' -> '{prop_paronym_pair}'")
                if orig["stress_word"] != prop_stress_word:
                    changes.append(f"stress_word: '{orig['stress_word']}' -> '{prop_stress_word}'")
                print(f"  Task ID {task_id}: {', '.join(changes)}")
        conn.close()
        return 0

    # Apply updates if not dry-run
    if updated_count > 0:
        try:
            with conn:
                conn.executemany(
                    """
                    UPDATE zno_tasks
                    SET topic_norm = ?, task_subtype = ?, paronym_pair = ?, stress_word = ?
                    WHERE id = ?
                """,
                    updates_to_apply,
                )
        except sqlite3.Error as e:
            print(f"Error applying updates to database: {e}", file=sys.stderr)
            conn.close()
            return 1

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
