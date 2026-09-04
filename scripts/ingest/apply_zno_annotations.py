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


def load_annotations(worksheet_path: Path) -> list[dict[str, object]]:
    """Load the reviewed ZNO annotations from their checked-in worksheet."""
    with worksheet_path.open(encoding="utf-8") as worksheet:
        data = yaml.safe_load(worksheet)
    if not isinstance(data, dict) or "zno_annotations" not in data:
        raise ValueError("'zno_annotations' key missing from worksheet")
    annotations = data["zno_annotations"]
    if not isinstance(annotations, list):
        raise ValueError("'zno_annotations' must be a list")
    return annotations


def plan_annotations(
    conn: sqlite3.Connection, annotations: list[dict[str, object]]
) -> tuple[list[tuple[str, str, str, str, int]], list[dict[str, object]], dict[int, dict[str, str]], int]:
    """Return all safe worksheet updates without changing the database.

    Existing reviewed values are immutable unless the worksheet explicitly
    lists the column in ``override_fields``.  Keeping planning separate lets a
    clean HTML ingest re-apply the worksheet in its own transaction and lets
    the command-line tool retain its all-or-nothing conflict refusal.
    """
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
    updates: list[tuple[str, str, str, str, int]] = []
    conflicts: list[dict[str, object]] = []
    skipped = 0

    for annotation in annotations:
        task_id = annotation.get("id")
        if not isinstance(task_id, int) or task_id not in db_tasks:
            continue
        db_row = db_tasks[task_id]
        override_fields = annotation.get("override_fields", [])
        if not isinstance(override_fields, list) or not all(
            isinstance(field, str) and field in {"topic_norm", "task_subtype", "paronym_pair", "stress_word"}
            for field in override_fields
        ):
            raise ValueError(f"Task ID {task_id} has invalid override_fields")
        override_fields_set = set(override_fields)
        proposed = {
            "topic_norm": annotation.get("topic_norm") or "",
            "task_subtype": annotation.get("task_subtype") or "",
            "paronym_pair": annotation.get("paronym_pair") or "",
            "stress_word": annotation.get("stress_word") or "",
        }
        has_conflict = False
        has_diff = False
        for column, proposed_value in proposed.items():
            existing_value = db_row[column]
            if existing_value == proposed_value:
                continue
            if existing_value == "" or column in override_fields_set:
                has_diff = True
            else:
                has_conflict = True
                conflicts.append(
                    {
                        "id": task_id,
                        "column": column,
                        "db_value": existing_value,
                        "proposed_value": proposed_value,
                    }
                )
        if has_conflict:
            continue
        if has_diff:
            updates.append(
                (
                    str(proposed["topic_norm"]),
                    str(proposed["task_subtype"]),
                    str(proposed["paronym_pair"]),
                    str(proposed["stress_word"]),
                    task_id,
                )
            )
        else:
            skipped += 1
    return updates, conflicts, db_tasks, skipped


def apply_worksheet_annotations(conn: sqlite3.Connection, worksheet_path: Path) -> dict[str, object]:
    """Re-apply reviewed worksheet metadata after a source-only HTML ingest."""
    updates, conflicts, _db_tasks, skipped = plan_annotations(conn, load_annotations(worksheet_path))
    if conflicts:
        raise ValueError(f"worksheet conflicts: {conflicts}")
    if updates:
        conn.executemany(
            """
            UPDATE zno_tasks
            SET topic_norm = ?, task_subtype = ?, paronym_pair = ?, stress_word = ?
            WHERE id = ?
            """,
            updates,
        )
    return {"updated": len(updates), "skipped": skipped}


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

    try:
        annotations = load_annotations(worksheet_path)
    except Exception as e:
        print(f"Error parsing worksheet YAML: {e}", file=sys.stderr)
        return 1

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    try:
        updates_to_apply, conflicts_found, db_tasks, skipped_count = plan_annotations(conn, annotations)
    except (sqlite3.OperationalError, ValueError) as e:
        print(f"Database error: {e}", file=sys.stderr)
        conn.close()
        return 1
    updated_count = len(updates_to_apply)
    conflict_count = len({int(conflict["id"]) for conflict in conflicts_found})

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
            conn.executemany(
                """
                UPDATE zno_tasks
                SET topic_norm = ?, task_subtype = ?, paronym_pair = ?, stress_word = ?
                WHERE id = ?
                """,
                updates_to_apply,
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error applying updates to database: {e}", file=sys.stderr)
            conn.close()
            return 1

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
