"""Product SQLite boundary and declared source-ingest writers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from lu_machinery.hygiene import lint_source_db_writable_connects as lint

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.repo_wide
def test_repo_has_no_unallowlisted_writable_source_db_connect(monkeypatch):
    monkeypatch.setenv("LU_PRODUCT_ROOT", str(REPO_ROOT))
    violations, unreadable = lint.find_violations(REPO_ROOT)
    assert violations == [], "\n".join(violations)
    skipped = subprocess.run(
        ["git", "ls-files", "-t", "--", "scripts"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    assert set(unreadable) <= {line[2:] for line in skipped if line.startswith("S ")}, unreadable


SOURCE_INGEST_BUILD_WRITERS = {
    "scripts/audit/sum11_sovietization_scan.py",
    "scripts/etymology/extract_cognate_forms.py",
    "scripts/etymology/recover_latin_cognates.py",
    "scripts/ingest/antonenko_full_book_ingest.py",
    "scripts/ingest/apply_zno_annotations.py",
    "scripts/ingest/backfill_lesson_sections.py",
    "scripts/ingest/backfill_school_textbook_orphans.py",
    "scripts/ingest/dictionary_ingest.py",
    "scripts/ingest/esum_load.py",
    "scripts/ingest/goroh_etymology_ingest.py",
    "scripts/ingest/incremental_dmklinger_ingest.py",
    "scripts/ingest/incremental_historical_source_ingest.py",
    "scripts/ingest/incremental_textbook_ingest.py",
    "scripts/ingest/ohoiko_books_ingest.py",
    "scripts/ingest/ohoiko_to_jsonl.py",
    "scripts/ingest/ohoiko_verbs_ingest.py",
    "scripts/ingest/owned_books_ingest.py",
    "scripts/ingest/pohribnyi_pronunciation_ingest.py",
    "scripts/ingest/pravopys_2019_ingest.py",
    "scripts/ingest/private_teacher_lessons_ingest.py",
    "scripts/ingest/resource_catalogue_ingest.py",
    "scripts/ingest/slovnyk_me_ingest.py",
    "scripts/ingest/sum20_official_ingest.py",
    "scripts/ingest/sum20_quarantine_unverified.py",
    "scripts/ingest/ua_gec_ingest.py",
    "scripts/ingest/ulp_lesson_notes_ingest.py",
    "scripts/ingest/ulp_to_jsonl.py",
    "scripts/ingest/wiktionary_etymology_ingest.py",
    "scripts/ingest/zno_ingest.py",
    "scripts/lexicon/load_relation_candidates.py",
    "scripts/lexicon/migrate_sum11_sovietization.py",
    "scripts/lexicon/runner/ulif_forms.py",
    "scripts/lexicon/teacher_deck.py",
    "scripts/lexicon/tools/migrate_ulif_raw.py",
    "scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py",
    "scripts/migrations/2026-07-06-add-subject-to-textbooks.py",
    "scripts/projects/open_model_data/phase3_saint_sophia_db_reconciliation.py",
    "scripts/projects/open_model_data/phase3_vspu_db_cutover.py",
    "scripts/rag/migrate_add_literary_source_url.py",
    "scripts/rag/scrape_wikisource.py",
    "scripts/wiki/build_sources_db.py",
    "scripts/wiki/extract_sections.py",
    "scripts/wiki/fetch_wikipedia.py",
    "scripts/wiki/migrate_external_chunks.py",
    "scripts/wiki/restore_literary_metadata.py",
    "scripts/wiki/rollback_sections.py",
    "scripts/wiki/sources_db.py",
    "scripts/wiki/ukrainian_wiki_corpus.py",
}


def test_only_listed_source_ingest_build_writers_declare_protected_databases():
    actual = {
        entry.path
        for entry in lint.load_scan_allowlist(REPO_ROOT)
        if entry.kind == "writer" and any(name in entry.target_db for name in ("sources.db", "vesum.db"))
    }
    assert actual == SOURCE_INGEST_BUILD_WRITERS
