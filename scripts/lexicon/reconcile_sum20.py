"""Report SUM-20 staging versus official ingest differences without writes (#10655)."""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path

from scripts.lexicon.sum20_store import Sum20StoreError, open_sources
from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.storage.topology import main_checkout_root
from scripts.wiki.sum20_official import normalize_sum20_lookup

DIFFERENCE_EXAMPLE_LIMIT = 20


def _comparison_payload(headword: str, text: str, identity: str, *, staging: bool) -> tuple[str, str]:
    """Discard transport wrappers for comparison only; never write normalized text.

    Mirror pages prepend a separate lemma before the article heading and append
    a source footer. Whitespace differs around punctuation in the official HTML
    extraction. Source URLs and retrieval timestamps outside the article are
    not comparison inputs. Lexical characters, case and punctuation in the
    article itself are retained.
    """
    body = re.sub(r"<[^>]+>", "", html.unescape(text)).strip()
    if staging:
        body = re.sub(rf"^{re.escape(identity)}\s+", "", body, count=1)
        body = re.sub(r"\s+Джерело:\s*(?:Словник української мови|https?://).*$", "", body, flags=re.DOTALL)
    return normalize_sum20_lookup(headword), re.sub(r"\s+", "", body)


def _inventory(conn: SQLiteConnection, *, staging: bool) -> tuple[int, dict[str, list[tuple[str, str]]]]:
    """Group comparison payloads by normalized article key; retain duplicates.

    Mirror URLs carry no official wordid. The shared identity is the normalized
    lemma (including any homonym suffix), not a row id or a content digest.
    Compare headword and full article text after removing transport wrappers,
    markup, retrieval times and source-specific URLs. No definitions are edited.
    """
    sql = (
        "SELECT lemma, headword, text FROM sum20_slovnyk_articles"
        if staging else "SELECT normalized_lookup_key, headword, article_text FROM sum20_articles"
    )
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    count = 0
    for identity, headword, text in conn.execute(sql):
        key = normalize_sum20_lookup(str(identity or ""))
        if not key:
            raise Sum20StoreError("article_identity_missing")
        grouped[key].append(_comparison_payload(str(headword or ""), str(text or ""), str(identity), staging=staging))
        count += 1
    return count, {key: sorted(payloads) for key, payloads in grouped.items()}


def reconcile_sum20(staging: Path, official: Path | None = None, *, repository_root: Path | None = None) -> dict:
    """Compare both inventories through resolver-validated read-only bindings.

    Missing and extra are relative to official ingest. Duplicate identity groups
    remain visible and their entire payload multisets participate in comparison.
    Quarantined official records remain part of the ingest inventory.
    """
    with closing(open_sources(staging, repository_root=repository_root)) as staged_conn, closing(
        open_sources(official, repository_root=repository_root)
    ) as official_conn:
        staging_rows, staged = _inventory(staged_conn, staging=True)
        official_rows, ingested = _inventory(official_conn, staging=False)
    shared = staged.keys() & ingested.keys()
    differing = sorted(key for key in shared if staged[key] != ingested[key])
    missing = sorted(ingested.keys() - staged.keys())
    extra = sorted(staged.keys() - ingested.keys())
    return {
        "comparison_fields": ["headword", "article_text"],
        "identity": "normalized_article_key",
        "counts": {
            "staging_records": staging_rows,
            "official_records": official_rows,
            "staging_identities": len(staged),
            "official_identities": len(ingested),
            "shared": len(shared),
            "matching": len(shared) - len(differing),
            "missing": len(missing),
            "extra": len(extra),
            "differing_after_normalization": len(differing),
            "staging_duplicate_identities": sum(len(rows) > 1 for rows in staged.values()),
            "official_duplicate_identities": sum(len(rows) > 1 for rows in ingested.values()),
        },
        "missing": missing,
        "extra": extra,
        "differing_examples": differing[:DIFFERENCE_EXAMPLE_LIMIT],
    }


def build_parser() -> argparse.ArgumentParser:
    """Describe the report-only interface and its refusal behavior."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare SUM-20 staging and official article inventories read-only. "
            "Use for reconciliation evidence before a separately authorized data change; never applies changes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.lexicon.reconcile_sum20\n"
            "  .venv/bin/python -m scripts.lexicon.reconcile_sum20 --staging /local/staging.db --official /local/official.db --details\n\n"
            "Outputs: JSON on stdout; no files, database updates or network requests.\n"
            "Exit codes: 0 report produced (differences allowed); 2 refused store or invalid schema/arguments.\n"
            "Related: issue #10655; scripts.lexicon.sum20_lookup; storage-topology.md."
        ),
    )
    parser.add_argument("--staging", type=Path, help="Absolute local staging DB (default: primary data/sum20_slovnyk_staging.db).")
    parser.add_argument("--official", type=Path, help="Absolute local official DB (default: resolve_store('sources')).")
    parser.add_argument("--repository-root", type=Path, help="Inventory repository root (default: current checkout); e.g. /local/repo.")
    parser.add_argument("--details", action="store_true", help="Include article identity lists (default: counts only; no article bodies).")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Emit counts or a path-free typed refusal, without an apply mode."""
    args = build_parser().parse_args(argv)
    root = args.repository_root or Path.cwd()
    staging = args.staging if args.staging is not None else main_checkout_root(root) / "data" / "sum20_slovnyk_staging.db"
    try:
        report = reconcile_sum20(staging, args.official, repository_root=root)
    except Sum20StoreError as exc:
        print(json.dumps({"status": "refused", "reason": exc.reason}))
        return 2
    except sqlite3.Error:
        print(json.dumps({"status": "refused", "reason": "invalid_article_schema"}))
        return 2
    if not args.details:
        report = {key: value for key, value in report.items() if key not in {"missing", "extra", "differing_examples"}}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
