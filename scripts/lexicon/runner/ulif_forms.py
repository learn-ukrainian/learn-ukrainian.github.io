"""Build, verify, and report stress disagreements for ULIF derived forms.

This module populates `ulif_forms`, `ulif_forms_failures`, and `ulif_forms_build`
tables in an isolated copy of sources.db using the content-addressed raw cache.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.runner import ulif_dictua_parse
from scripts.wiki import sources_db

ULIF_FORMS_PARSER_VERSION = ulif_dictua_parse.ULIF_FORMS_PARSER_VERSION


def build_ulif_forms(
    db_path: str | Path,
    raw_cache_path: str | Path | None = None,
    report_path: str | Path | None = None,
    batch_size: int = 500,
) -> dict[str, Any]:
    """Build derived form rows for all verified ULIF entries into `ulif_forms`."""
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")

    target_db = Path(db_path).resolve()
    if not target_db.is_file():
        raise FileNotFoundError(f"Database not found: {target_db}")

    raw_cache = Path(raw_cache_path).resolve() if raw_cache_path is not None else ulif_raw_cache.cache_path(target_db)

    conn = sqlite3.connect(str(target_db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    sources_db.ensure_ulif_dictua_schema(conn)

    verified_entries = conn.execute(
        """
        SELECT id, normalized_query, homonym_index, canonical_headword,
               grammatical_label, sense_gloss, raw_response_ref, homonym_checked
        FROM ulif_dictua_entries
        WHERE homonym_checked = 1
        ORDER BY id
        """
    ).fetchall()
    total_verified = len(verified_entries)

    started_at = datetime.now(UTC).isoformat()
    source_fp = sources_db.compute_ulif_source_fingerprint(conn)

    conn.execute("DELETE FROM ulif_forms")
    conn.execute("DELETE FROM ulif_forms_failures")
    conn.execute(
        """
        INSERT INTO ulif_forms_build (
            id, state, parser_version, total_entries, entries_done,
            entries_failed, total_forms, started_at, finished_at, source_fingerprint
        )
        VALUES (1, 'building', ?, ?, 0, 0, 0, ?, '', ?)
        ON CONFLICT(id) DO UPDATE SET
            state = 'building',
            parser_version = excluded.parser_version,
            total_entries = excluded.total_entries,
            entries_done = 0,
            entries_failed = 0,
            total_forms = 0,
            started_at = excluded.started_at,
            finished_at = '',
            source_fingerprint = excluded.source_fingerprint
        """,
        (ULIF_FORMS_PARSER_VERSION, total_verified, started_at, source_fp),
    )
    conn.commit()

    raw_conn = ulif_raw_cache.open_cache(raw_cache, create=False)
    failures_by_reason: dict[str, int] = defaultdict(int)
    mismatches: list[dict[str, Any]] = []

    try:
        for offset in range(0, total_verified, batch_size):
            batch = verified_entries[offset : offset + batch_size]
            entry_ids = [entry["id"] for entry in batch]
            batch_form_rows: list[tuple] = []
            batch_failure_rows: list[tuple] = []

            for entry in batch:
                entry_id = int(entry["id"])
                ref = str(entry["raw_response_ref"] or "")
                homonym_index = int(entry["homonym_index"] or 1)
                stored_headword = str(entry["canonical_headword"] or "")
                stored_grammar = str(entry["grammatical_label"] or "")
                stored_gloss = str(entry["sense_gloss"] or "")

                sec_rows = conn.execute(
                    """
                    SELECT kind, source_order, sense_or_group_id, payload_json
                    FROM ulif_dictua_sections
                    WHERE entry_id = ?
                    ORDER BY kind, source_order
                    """,
                    (entry_id,),
                ).fetchall()
                entry_fp = sources_db.compute_ulif_entry_fingerprint(entry, sec_rows)

                if not ref:
                    reason = "missing_raw_manifest"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                if not ref.startswith("sha256:") or len(ref) != 71:
                    reason = "corrupt_raw_manifest"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                manifest_sha = ref.removeprefix("sha256:")
                manifest_bytes = None
                try:
                    manifest_bytes = ulif_raw_cache.get(manifest_sha, conn=raw_conn)
                except FileNotFoundError:
                    reason = "missing_cache_file"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue
                except ValueError:
                    reason = "corrupt_raw_manifest"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue
                except Exception:
                    reason = "raw_cache_error"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                if manifest_bytes is None:
                    reason = "missing_raw_manifest"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                manifest = None
                try:
                    manifest = json.loads(manifest_bytes)
                except Exception:
                    manifest = None

                if not isinstance(manifest, dict):
                    reason = "malformed_manifest"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                if "paradigm" not in manifest:
                    reason = "raw_entry_page_absent"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    if stored_headword:
                        row = ulif_dictua_parse.base_lemma_row(
                            stored_headword,
                            stored_grammar,
                            homonym_index=homonym_index,
                            is_invariable=False,
                        )
                        batch_form_rows.append((
                            entry_id,
                            row["entry_key"],
                            row["form_unstressed"],
                            row["form_stressed"],
                            json.dumps(row["stress_vowel_indices"]),
                            json.dumps(row["grammatical_tags"], ensure_ascii=False),
                            json.dumps(row["unmapped_labels"], ensure_ascii=False),
                            row["variant_order"],
                            row["preposition"],
                            int(row["marked_asterisk"]),
                            int(row["is_lemma"]),
                            int(row["is_invariable"]),
                            int(row["dual_stress_flag"]),
                            row["pedagogical_stressed_form"],
                            "",
                            ULIF_FORMS_PARSER_VERSION,
                            entry_fp,
                        ))
                    continue

                par_ref = manifest.get("paradigm")
                if not par_ref or not isinstance(par_ref, str) or not par_ref.startswith("sha256:") or len(par_ref) != 71:
                    reason = "corrupt_raw_paradigm_blob"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                par_sha = par_ref.removeprefix("sha256:")
                par_bytes = None
                try:
                    par_bytes = ulif_raw_cache.get(par_sha, conn=raw_conn)
                except FileNotFoundError:
                    reason = "missing_cache_file"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue
                except ValueError:
                    reason = "corrupt_raw_paradigm_blob"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue
                except Exception:
                    reason = "raw_cache_error"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                if par_bytes is None:
                    reason = "missing_raw_paradigm_blob"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                par_html = par_bytes.decode("utf-8", errors="replace")
                try:
                    parsed = ulif_dictua_parse.parse_ulif_entry(par_html, homonym_index=homonym_index)
                except Exception as ex:
                    reason = f"extraction_failed: {type(ex).__name__}: {ex}"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                parsed_headword = parsed.get("canonical_headword") or ""
                forms = parsed.get("forms") or []

                if not parsed_headword or not forms or forms[0]["form_unstressed"] == "":
                    reason = "extraction_failed: empty_article"
                    locator = f"ulif:entry:{entry_id}"
                    batch_failure_rows.append((entry_id, reason, locator))
                    failures_by_reason[reason] += 1
                    continue

                parsed_grammar = parsed.get("grammatical_label") or ""
                parsed_gloss = parsed.get("sense_gloss") or ""

                mismatch_fields = []
                if stored_headword != parsed_headword:
                    mismatch_fields.append("canonical_headword")
                if stored_grammar != parsed_grammar:
                    mismatch_fields.append("grammatical_label")
                if stored_gloss != parsed_gloss:
                    mismatch_fields.append("sense_gloss")

                if mismatch_fields:
                    mismatches.append({
                        "entry_id": entry_id,
                        "locator": f"ulif:entry:{entry_id}",
                        "fields": mismatch_fields,
                        "stored_headword": stored_headword,
                        "parsed_headword": parsed_headword,
                        "stored_grammar": stored_grammar,
                        "parsed_grammar": parsed_grammar,
                        "stored_gloss": stored_gloss,
                        "parsed_gloss": parsed_gloss,
                    })

                for f in forms:
                    batch_form_rows.append((
                        entry_id,
                        f["entry_key"],
                        f["form_unstressed"],
                        f["form_stressed"],
                        json.dumps(f["stress_vowel_indices"]),
                        json.dumps(f["grammatical_tags"], ensure_ascii=False),
                        json.dumps(f["unmapped_labels"], ensure_ascii=False),
                        f["variant_order"],
                        f["preposition"],
                        int(f["marked_asterisk"]),
                        int(f["is_lemma"]),
                        int(f["is_invariable"]),
                        int(f["dual_stress_flag"]),
                        f["pedagogical_stressed_form"],
                        par_sha,
                        ULIF_FORMS_PARSER_VERSION,
                        entry_fp,
                    ))

            placeholders = ",".join("?" * len(entry_ids))
            conn.execute(f"DELETE FROM ulif_forms WHERE entry_id IN ({placeholders})", entry_ids)
            conn.execute(f"DELETE FROM ulif_forms_failures WHERE entry_id IN ({placeholders})", entry_ids)

            if batch_form_rows:
                conn.executemany(
                    """
                    INSERT INTO ulif_forms (
                        entry_id, entry_key, form_unstressed, form_stressed,
                        stress_vowel_indices, grammatical_tags, unmapped_labels,
                        variant_order, preposition, marked_asterisk, is_lemma,
                        is_invariable, dual_stress_flag, pedagogical_stressed_form,
                        source_page_sha256, parser_version, source_entry_fingerprint
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch_form_rows,
                )

            if batch_failure_rows:
                conn.executemany(
                    """
                    INSERT INTO ulif_forms_failures (entry_id, reason, locator)
                    VALUES (?, ?, ?)
                    """,
                    batch_failure_rows,
                )

            conn.commit()

        done_count = conn.execute(
            """
            SELECT count(DISTINCT entry_id) FROM ulif_forms
            WHERE entry_id NOT IN (SELECT entry_id FROM ulif_forms_failures)
            """
        ).fetchone()[0]
        failed_count = conn.execute("SELECT count(*) FROM ulif_forms_failures").fetchone()[0]
        total_forms = conn.execute("SELECT count(*) FROM ulif_forms").fetchone()[0]
        finished_at = datetime.now(UTC).isoformat()

        state = "complete" if (done_count + failed_count == total_verified) else "failed"

        conn.execute(
            """
            UPDATE ulif_forms_build
            SET state = ?, entries_done = ?, entries_failed = ?, total_forms = ?, finished_at = ?, source_fingerprint = ?
            WHERE id = 1
            """,
            (state, done_count, failed_count, total_forms, finished_at, source_fp),
        )
        conn.commit()

        report = {
            "state": state,
            "parser_version": ULIF_FORMS_PARSER_VERSION,
            "source_fingerprint": source_fp,
            "total_verified": total_verified,
            "entries_done": done_count,
            "entries_failed": failed_count,
            "total_forms": total_forms,
            "failures_by_reason": dict(failures_by_reason),
            "mismatches_count": len(mismatches),
            "mismatches": mismatches,
            "mismatches_sample": mismatches[:100],
            "started_at": started_at,
            "finished_at": finished_at,
        }

        if report_path is not None:
            rep_path = Path(report_path)
            rep_path.parent.mkdir(parents=True, exist_ok=True)
            rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            if mismatches:
                sidecar_path = rep_path.with_suffix(".mismatches.jsonl")
                with sidecar_path.open("w", encoding="utf-8") as sf:
                    for m in mismatches:
                        sf.write(json.dumps(m, ensure_ascii=False) + "\n")

        return report
    except BaseException:
        try:
            conn.execute(
                "UPDATE ulif_forms_build SET state = 'failed', finished_at = ? WHERE id = 1",
                (datetime.now(UTC).isoformat(),),
            )
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        raw_conn.close()
        conn.close()


def verify_ulif_forms(db_path: str | Path) -> dict[str, Any]:
    """Verify that `ulif_forms` build is complete, consistent, and covers all verified entries."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")

    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing = {"ulif_forms", "ulif_forms_failures", "ulif_forms_build"} - tables
        if missing:
            return {"verified": False, "error": f"Missing tables: {sorted(missing)}"}

        build_row = conn.execute("SELECT * FROM ulif_forms_build WHERE id = 1").fetchone()
        if build_row is None:
            return {"verified": False, "error": "ulif_forms_build table is empty"}
        if build_row["state"] != "complete":
            return {"verified": False, "error": f"ulif_forms_build state is {build_row['state']!r}, expected 'complete'"}
        if build_row["parser_version"] != ULIF_FORMS_PARSER_VERSION:
            return {"verified": False, "error": f"stale parser_version: {build_row['parser_version']!r}"}

        current_source_fp = sources_db.compute_ulif_source_fingerprint(conn)
        stored_source_fp = build_row["source_fingerprint"]
        if not stored_source_fp or stored_source_fp != current_source_fp:
            return {
                "verified": False,
                "error": f"stale source_fingerprint: expected {current_source_fp!r}, got {stored_source_fp!r}",
            }

        unaccounted = conn.execute(
            """
            SELECT count(*) FROM ulif_dictua_entries e
            WHERE homonym_checked = 1
              AND NOT EXISTS (SELECT 1 FROM ulif_forms f WHERE f.entry_id = e.id)
              AND NOT EXISTS (SELECT 1 FROM ulif_forms_failures x WHERE x.entry_id = e.id)
            """
        ).fetchone()[0]
        if unaccounted != 0:
            return {"verified": False, "error": f"Found {unaccounted} verified entries with neither forms nor failure recorded"}

        empty_forms = conn.execute("SELECT count(*) FROM ulif_forms WHERE form_unstressed = ''").fetchone()[0]
        if empty_forms != 0:
            return {"verified": False, "error": f"Found {empty_forms} form rows with empty form_unstressed"}

        total_verified = conn.execute("SELECT count(*) FROM ulif_dictua_entries WHERE homonym_checked = 1").fetchone()[0]
        done_count = conn.execute(
            """
            SELECT count(DISTINCT entry_id) FROM ulif_forms
            WHERE entry_id NOT IN (SELECT entry_id FROM ulif_forms_failures)
            """
        ).fetchone()[0]
        failed_count = conn.execute("SELECT count(*) FROM ulif_forms_failures").fetchone()[0]
        total_forms = conn.execute("SELECT count(*) FROM ulif_forms").fetchone()[0]

        if done_count != build_row["entries_done"] or failed_count != build_row["entries_failed"]:
            return {
                "verified": False,
                "error": (
                    f"Count mismatch: live (done={done_count}, failed={failed_count}) != "
                    f"recorded (done={build_row['entries_done']}, failed={build_row['entries_failed']})"
                ),
            }

        return {
            "verified": True,
            "total_verified": total_verified,
            "entries_done": done_count,
            "entries_failed": failed_count,
            "total_forms": total_forms,
            "parser_version": build_row["parser_version"],
            "source_fingerprint": stored_source_fp,
            "finished_at": build_row["finished_at"],
        }
    finally:
        conn.close()


def generate_disagreement_report(
    db_path: str | Path,
    out_path: str | Path,
    *,
    all_rows: bool = False,
) -> dict[str, Any]:
    """Compare ULIF form stresses against the stress oracle trie and report disagreements."""
    from scripts.verification.stress import verify_stress

    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")

    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """
            SELECT entry_id, entry_key, form_unstressed, form_stressed, pedagogical_stressed_form
            FROM ulif_forms
            ORDER BY entry_id, id
            """
        )

        disagreements: list[dict[str, Any]] = []
        total_checked = 0
        agreed_count = 0
        disagreed_count = 0
        not_applicable_count = 0
        stress_cache: dict[str, Any] = {}

        for row in cursor:
            total_checked += 1
            unstressed = row["form_unstressed"]
            if unstressed not in stress_cache:
                stress_cache[unstressed] = verify_stress(unstressed)
            res = stress_cache[unstressed]
            status = res.get("status")
            matches = res.get("matches") or []
            oracle_stresses = sorted({m.get("stressed_form") for m in matches if m.get("stressed_form")})

            ulif_stressed = row["form_stressed"]
            pedagogical = row["pedagogical_stressed_form"]
            agrees = (ulif_stressed in oracle_stresses) or (pedagogical in oracle_stresses)

            if status == "invalid_input":
                not_applicable_count += 1
                disagreements.append({
                    "entry_id": row["entry_id"],
                    "entry_key": row["entry_key"],
                    "form_unstressed": unstressed,
                    "ulif_stressed": ulif_stressed,
                    "oracle_status": status,
                    "oracle_stresses": "",
                    "disagreement_type": "oracle_not_applicable",
                    "agrees": None,
                })
            elif agrees:
                agreed_count += 1
                if all_rows:
                    disagreements.append({
                        "entry_id": row["entry_id"],
                        "entry_key": row["entry_key"],
                        "form_unstressed": unstressed,
                        "ulif_stressed": ulif_stressed,
                        "oracle_status": status,
                        "oracle_stresses": ",".join(oracle_stresses),
                        "disagreement_type": "none",
                        "agrees": True,
                    })
            else:
                disagreed_count += 1
                dtype = "not_found" if status == "not_found" else ("stress_mismatch" if oracle_stresses else status)
                disagreements.append({
                    "entry_id": row["entry_id"],
                    "entry_key": row["entry_key"],
                    "form_unstressed": unstressed,
                    "ulif_stressed": ulif_stressed,
                    "oracle_status": status,
                    "oracle_stresses": ",".join(oracle_stresses),
                    "disagreement_type": dtype,
                    "agrees": False,
                })

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".json":
            out.write_text(
                json.dumps(
                    {
                        "total_checked": total_checked,
                        "agreed_count": agreed_count,
                        "disagreed_count": disagreed_count,
                        "not_applicable_count": not_applicable_count,
                        "records": disagreements,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        else:
            header = "entry_id\tentry_key\tform_unstressed\tulif_stressed\toracle_status\toracle_stresses\tdisagreement_type\tagrees\n"
            lines = [header]
            for d in disagreements:
                lines.append(
                    f"{d['entry_id']}\t{d['entry_key']}\t{d['form_unstressed']}\t{d['ulif_stressed']}\t{d['oracle_status']}\t{d['oracle_stresses']}\t{d['disagreement_type']}\t{d['agrees']}\n"
                )
            out.write_text("".join(lines), encoding="utf-8")

        return {
            "total_checked": total_checked,
            "agreed_count": agreed_count,
            "disagreed_count": disagreed_count,
            "not_applicable_count": not_applicable_count,
            "output_file": str(out),
        }
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.lexicon.runner.ulif_forms",
        description=(
            "Build and verify derived morphological forms and stress disagreement reports for ULIF entries.\n"
            "Use this offline runner tool on an isolated copy of sources.db with raw cache access; do NOT run directly against production data/sources.db."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms build --db /path/to/sources-copy.db --raw-cache /path/to/ulif_raw.sqlite --report /path/to/build-report.json\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms verify --db /path/to/sources-copy.db\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms disagreement-report --db /path/to/sources-copy.db --out /path/to/stress-disagreements.tsv\n\n"
            "Outputs:\n"
            "  build: populates ulif_forms, ulif_forms_failures, and ulif_forms_build tables in the target database, and optionally writes a JSON report.\n"
            "  verify: prints verification summary to stdout.\n"
            "  disagreement-report: writes TSV or JSON comparison against the ukrainian-word-stress trie.\n\n"
            "Exit codes:\n"
            "  0: Command completed successfully.\n"
            "  1: Error encountered (build failure, verification mismatch, or missing file).\n\n"
            "Related:\n"
            "  docs/atlas/word-cards/ulif-source-records.md, issue #9250."
        ),
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    build_p = subparsers.add_parser(
        "build",
        help="Build ulif_forms and ulif_forms_failures tables from verified entries.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms build --db /scratch/sources-copy.db --raw-cache /scratch/ulif_raw.sqlite --report /scratch/report.json"
        ),
    )
    build_p.add_argument(
        "--db",
        required=True,
        help="Path to target sources.db SQLite copy (required; e.g. /scratch/sources-copy.db)",
    )
    build_p.add_argument(
        "--raw-cache",
        default=None,
        help="Path to external ulif_raw.sqlite cache (default: derived from --db or primary checkout)",
    )
    build_p.add_argument(
        "--report",
        default=None,
        help="Optional destination path for JSON build report (e.g. /scratch/report.json)",
    )
    build_p.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of entries per database commit batch (default: 500)",
    )

    verify_p = subparsers.add_parser(
        "verify",
        help="Verify ulif_forms tables consistency and completeness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms verify --db /scratch/sources-copy.db"
        ),
    )
    verify_p.add_argument(
        "--db",
        required=True,
        help="Path to target sources.db SQLite copy (required; e.g. /scratch/sources-copy.db)",
    )

    disagree_p = subparsers.add_parser(
        "disagreement-report",
        help="Generate stress disagreement report against the stress trie.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  .venv/bin/python -m scripts.lexicon.runner.ulif_forms disagreement-report --db /scratch/sources-copy.db --out /scratch/disagreements.tsv"
        ),
    )
    disagree_p.add_argument(
        "--db",
        required=True,
        help="Path to target sources.db SQLite copy (required; e.g. /scratch/sources-copy.db)",
    )
    disagree_p.add_argument(
        "--out",
        required=True,
        help="Output file path (.tsv or .json; e.g. /scratch/disagreements.tsv)",
    )
    disagree_p.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Include all checked form rows in the report instead of only disagreements (default: False)",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "build":
        try:
            report = build_ulif_forms(
                db_path=args.db,
                raw_cache_path=args.raw_cache,
                report_path=args.report,
                batch_size=args.batch_size,
            )
            print(f"Build {report['state']}: done={report['entries_done']}, failed={report['entries_failed']}, forms={report['total_forms']}")
            return 0 if report["state"] == "complete" else 1
        except Exception as e:
            print(f"Build error: {e}", file=sys.stderr)
            return 1

    if args.subcommand == "verify":
        try:
            res = verify_ulif_forms(db_path=args.db)
            if res.get("verified"):
                print(f"Verification PASSED: {res['entries_done']} entries with {res['total_forms']} forms, {res['entries_failed']} failures.")
                return 0
            else:
                print(f"Verification FAILED: {res.get('error')}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Verification error: {e}", file=sys.stderr)
            return 1

    if args.subcommand == "disagreement-report":
        try:
            res = generate_disagreement_report(db_path=args.db, out_path=args.out, all_rows=args.all)
            print(f"Disagreement report generated: {res['disagreed_count']} disagreements / {res['total_checked']} checked forms written to {res['output_file']}")
            return 0
        except Exception as e:
            print(f"Disagreement report error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
