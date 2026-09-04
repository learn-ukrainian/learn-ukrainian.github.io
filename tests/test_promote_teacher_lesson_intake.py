"""Regression coverage for teacher-lesson intake promotion ledgers."""

import json
import re
import sqlite3
from pathlib import Path

import yaml

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import (
    source_inventory_key,
    validate_decision_file,
)
from scripts.lexicon import promote_teacher_lesson_intake as promote_module
from scripts.lexicon.grow_lexicon_from_content import build_skeleton_entry
from scripts.lexicon.promote_teacher_lesson_intake import (
    DEFAULT_FULL_DECISIONS,
    PROJECT_ROOT,
    promote,
)

DELTA_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-2026-09-02-delta.yaml"
)
DELTA_DECISIONS = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/2026-09-02-teacher-lesson-delta-approve.yaml"
)
DELTA_SOURCE_SHAPE_SHA256 = "a3349f88c6a7a97682544d61ae6ddee9545a7103eec73479b8ac9f344d1b4320"
# Full delta: high_frequency_missing (2433) + post_boundary_table_missing (228) +
# needs_review_bulk (9150) = 11811. A prior pass only took the first two buckets
# (2661); the operator flagged that as skipping needs_review_bulk (#7623).
DELTA_HEADWORD_COUNT = 11_811
_SAFE_LOCATOR = re.compile(
    r"^(?:explicit vocabulary table 1 row \d+"
    r"|private source unit \d+ paragraph 1"
    r"|private source table row \d+)$"
)


def test_default_full_decisions_is_a_committed_repository_file() -> None:
    relative_path = DEFAULT_FULL_DECISIONS.relative_to(PROJECT_ROOT)

    assert relative_path == (
        Path("data")
        / "lexicon"
        / "source-inventory-review-decisions"
        / "2026-07-23-alona-full-document-intake.yaml"
    )
    assert DEFAULT_FULL_DECISIONS.is_file()


def test_private_teacher_lesson_delta_inventory_is_privacy_safe() -> None:
    records = read_source_inventory(DELTA_INVENTORY, project_root=PROJECT_ROOT)

    assert len(records) == DELTA_HEADWORD_COUNT
    assert {record.source_family for record in records} == {"teacher_lesson"}
    assert {record.extraction_mode for record in records} == {"curated_headword"}
    assert all(record.source_url is None and record.source_path is None for record in records)
    assert all(_SAFE_LOCATOR.fullmatch(record.source_locator or "") for record in records)

    inventory_text = DELTA_INVENTORY.read_text(encoding="utf-8")
    assert DELTA_SOURCE_SHAPE_SHA256 in inventory_text
    assert ".docx" not in inventory_text.lower()
    assert "alona" not in inventory_text.lower()


def test_private_teacher_lesson_delta_decisions_validate_as_practice_only() -> None:
    summary = validate_decision_file(DELTA_DECISIONS)
    payload = yaml.safe_load(DELTA_DECISIONS.read_text(encoding="utf-8"))

    assert summary["rows"] == DELTA_HEADWORD_COUNT
    assert summary["decision_counts"] == {"approve_for_publish": DELTA_HEADWORD_COUNT}
    assert payload["source_queue"]["total_queue_rows"] == DELTA_HEADWORD_COUNT
    assert payload["source_queue"]["approved_in_queue"] == DELTA_HEADWORD_COUNT
    assert all(
        row["surface_admission"] == {"practice": True, "cloze": False, "daily": False}
        for row in payload["decisions"]
    )


def _fake_candidate_and_decision(lemma: str, *, locator: str) -> tuple[dict, dict]:
    """Build one manifest-ready candidate + matching decision, as ``_build_rows`` would."""
    entry = build_skeleton_entry(lemma)
    entry.update(
        {
            "pos": "noun",
            "gloss": "test gloss",
            "primary_source": "source_inventory_grow",
            "source_provenance": [
                {
                    "source_family": "teacher_lesson",
                    "extraction_mode": promote_module.PUBLIC_EXTRACTION_MODE,
                    "inventory_path": promote_module.PUBLIC_INVENTORY_PATH,
                    "inventory_locator": locator,
                    "source_id": promote_module.PUBLIC_SOURCE_ID,
                    "source_title": promote_module.PUBLIC_SOURCE_TITLE,
                    "source_locator": locator,
                }
            ],
            "surface_admission": {"practice": True},
            "heritage_status": {
                "classification": "unknown",
                "attestations": [],
                "is_russianism": False,
                "russian_shadow": False,
                "vesum_attested": True,
                "calque_warning": None,
                "warning_severity": "none",
            },
        }
    )
    key = source_inventory_key(
        lemma=lemma,
        inventory_path=promote_module.PUBLIC_INVENTORY_PATH,
        locator=locator,
    )
    decision = {
        "lemma": lemma,
        "decision": "approve_for_publish",
        "approved_pos": "noun",
        "approved_gloss": "test gloss",
        "sense_note": "test fixture",
        "source_inventory": {
            "key": key,
            "path": promote_module.PUBLIC_INVENTORY_PATH,
            "locator": locator,
            "source_id": promote_module.PUBLIC_SOURCE_ID,
            "source_family": "teacher_lesson",
        },
        "evidence_refs": ["test fixture"],
        "surface_admission": {"practice": True},
    }
    return entry, decision


def test_promote_never_runs_full_manifest_enrich(tmp_path, monkeypatch) -> None:
    """A 9-head promote must enrich only the new heads, never sweep the manifest (#7623)."""
    lemmas = [f"тестлема{i}" for i in range(9)]
    candidates, decisions = [], []
    for i, lemma in enumerate(lemmas):
        entry, decision = _fake_candidate_and_decision(lemma, locator=f"private source unit {i} paragraph 1")
        candidates.append(entry)
        decisions.append(decision)

    report = {
        "source_rows": len(lemmas),
        "canonical_lemmas": len(lemmas),
        "collapsed_source_rows": 0,
        "candidates_with_english_anchor": len(lemmas),
        "held_without_english_anchor": 0,
        "dictionary_or_manifest_gloss_fallbacks": 0,
        "sum11_attested_canonical_lemmas": 0,
    }
    monkeypatch.setattr(
        promote_module, "_build_rows", lambda *a, **kw: (candidates, decisions, report)
    )

    # Route every stateful path under tmp_path; never touch the real journal/lock.
    intake_dir = tmp_path / "intake"
    monkeypatch.setattr(promote_module, "DEFAULT_INTAKE_DIR", intake_dir)
    monkeypatch.setattr(promote_module, "DEFAULT_JOURNAL", intake_dir / "journal.json")
    monkeypatch.setattr(promote_module, "DEFAULT_LOCK", intake_dir / "promotion.lock")
    monkeypatch.setattr(promote_module, "STAGED_MANIFEST", tmp_path / "manifest.staged.json")
    monkeypatch.setattr(promote_module, "STAGED_FINGERPRINT", tmp_path / "manifest.staged.fingerprint.json")
    monkeypatch.setattr(promote_module, "DEFAULT_PLAN", tmp_path / "plan.json")

    # Verification is exercised elsewhere; this test only guards the enrich fan-out.
    monkeypatch.setattr(promote_module.verify_manifest, "main", lambda argv: 0)
    monkeypatch.setattr(
        promote_module,
        "_assert_no_new_conformance_violations",
        lambda *, staged, baseline: {
            "baseline_violations": 0,
            "staged_violations": 0,
            "new_violations": 0,
            "new_samples": [],
        },
    )

    def _forbidden_full_enrich(*args, **kwargs):
        raise AssertionError("promote must never call the full-manifest enrich()")

    monkeypatch.setattr(promote_module.enrich_module, "enrich", _forbidden_full_enrich)

    enriched_lemmas: list[str] = []

    def _fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags, **_kwargs):
        enriched_lemmas.append(entry["lemma"])
        entry["enrichment"] = True
        return True

    monkeypatch.setattr(promote_module.enrich_module, "enrich_entry", _fake_enrich_entry)
    monkeypatch.setattr(promote_module.enrich_module, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(promote_module.enrich_module, "_sum11_has_flag_columns", lambda conn: False)

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [], "stats": {}}, ensure_ascii=False), encoding="utf-8"
    )
    fingerprint_path = tmp_path / "manifest.fingerprint.json"
    sources_db_path = tmp_path / "sources.db"
    sqlite3.connect(sources_db_path).close()

    result = promote(
        full_decisions=tmp_path / "unused-full-decisions.yaml",
        curated_inventory=tmp_path / "unused-curated-inventory.yaml",
        manifest=manifest_path,
        fingerprint=fingerprint_path,
        vesum_db=tmp_path / "unused-vesum.db",
        sources_db=sources_db_path,
        candidates_out=tmp_path / "candidates.json",
        decisions_out=tmp_path / "decisions.yaml",
        write=True,
        allow_held=True,
    )

    assert result["applied"]["promoted"] == 9
    assert result["journal"]["phase"] == "PUBLISHED"
    assert sorted(enriched_lemmas) == sorted(lemmas)

    published = json.loads(manifest_path.read_text(encoding="utf-8"))
    published_lemmas = {entry["lemma"] for entry in published["entries"]}
    assert published_lemmas == set(lemmas)
    assert all(entry.get("enrichment") for entry in published["entries"])


def test_promote_resume_staged_skips_replan_and_reenrich(tmp_path, monkeypatch) -> None:
    """``--resume-staged`` must reuse an already-staged manifest, not re-plan/re-enrich."""
    lemma = "тестлема-resume"
    entry, decision = _fake_candidate_and_decision(lemma, locator="private source unit 0 paragraph 1")
    entry["enrichment"] = True  # simulate a prior interrupted run that already enriched it

    monkeypatch.setattr(
        promote_module,
        "_build_rows",
        lambda *a, **kw: (
            [entry],
            [decision],
            {
                "source_rows": 1,
                "canonical_lemmas": 1,
                "collapsed_source_rows": 0,
                "candidates_with_english_anchor": 1,
                "held_without_english_anchor": 0,
                "dictionary_or_manifest_gloss_fallbacks": 0,
                "sum11_attested_canonical_lemmas": 0,
            },
        ),
    )

    intake_dir = tmp_path / "intake"
    journal_path = intake_dir / "journal.json"
    staged_manifest_path = tmp_path / "manifest.staged.json"
    monkeypatch.setattr(promote_module, "DEFAULT_INTAKE_DIR", intake_dir)
    monkeypatch.setattr(promote_module, "DEFAULT_JOURNAL", journal_path)
    monkeypatch.setattr(promote_module, "DEFAULT_LOCK", intake_dir / "promotion.lock")
    monkeypatch.setattr(promote_module, "STAGED_MANIFEST", staged_manifest_path)
    monkeypatch.setattr(promote_module, "STAGED_FINGERPRINT", tmp_path / "manifest.staged.fingerprint.json")
    monkeypatch.setattr(promote_module, "DEFAULT_PLAN", tmp_path / "plan.json")
    monkeypatch.setattr(promote_module.verify_manifest, "main", lambda argv: 0)
    monkeypatch.setattr(
        promote_module,
        "_assert_no_new_conformance_violations",
        lambda *, staged, baseline: {
            "baseline_violations": 0,
            "staged_violations": 0,
            "new_violations": 0,
            "new_samples": [],
        },
    )
    monkeypatch.setattr(
        promote_module.enrich_module,
        "enrich",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must never full-enrich")),
    )

    def _forbidden_enrich_entry(*args, **kwargs):
        raise AssertionError("resume of an already-ENRICHED stage must not re-run enrich_entry")

    monkeypatch.setattr(promote_module.enrich_module, "enrich_entry", _forbidden_enrich_entry)

    manifest_path = tmp_path / "manifest.json"
    base_manifest = {"entries": [], "stats": {}}
    manifest_path.write_text(json.dumps(base_manifest, ensure_ascii=False), encoding="utf-8")

    intake_dir.mkdir(parents=True, exist_ok=True)
    staged_manifest = {"entries": [entry], "stats": {}}
    staged_manifest_path.write_text(json.dumps(staged_manifest, ensure_ascii=False), encoding="utf-8")
    journal_path.write_text(
        json.dumps(
            {
                "schema_version": "promotion-journal.v1",
                "tx_id": "fixture-tx",
                "base_sha256": promote_module._sha256_file(manifest_path),
                "phase": "ENRICHED",
                "promoted": 1,
            }
        ),
        encoding="utf-8",
    )

    result = promote(
        full_decisions=tmp_path / "unused-full-decisions.yaml",
        curated_inventory=tmp_path / "unused-curated-inventory.yaml",
        manifest=manifest_path,
        fingerprint=tmp_path / "manifest.fingerprint.json",
        vesum_db=tmp_path / "unused-vesum.db",
        sources_db=tmp_path / "unused-sources.db",
        candidates_out=tmp_path / "candidates.json",
        decisions_out=tmp_path / "decisions.yaml",
        write=True,
        allow_held=True,
        resume_staged=True,
    )

    assert result["resumed"] is True
    assert result["journal"]["phase"] == "PUBLISHED"
    published = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {e["lemma"] for e in published["entries"]} == {lemma}


def _write_decisions_ledger(path: Path, lemmas: list[str]) -> None:
    payload = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "decisions": [
            {"lemma": lemma, "decision": "approve_for_publish", "approved_pos": "noun"}
            for lemma in lemmas
        ],
    }
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")


def test_build_teacher_lesson_membership_unions_existing_atlas_routes(tmp_path) -> None:
    """Every approved lemma with an Atlas route joins membership, regardless of gloss cache state.

    A lemma that is already ``skipped_existing`` at promotion time (i.e. some
    other pipeline already put it in the Atlas) still deserves curated
    recognition-practice membership; this must not require re-deriving a
    gloss for it (#7623 follow-up).
    """
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "абзац", "url_slug": "абзац"},
                    # A stress-marked manifest lemma must still resolve via _lemma_key.
                    {"lemma": "а́бо", "url_slug": "або"},
                    {"lemma": "не в атласі", "url_slug": "не-в-атласі-placeholder"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    decisions_path = tmp_path / "decisions.yaml"
    _write_decisions_ledger(decisions_path, ["абзац", "або", "лемма без маршруту"])

    membership_in = tmp_path / "membership-in.json"
    membership_in.write_text(
        json.dumps(
            {
                "schema": promote_module.MEMBERSHIP_SCHEMA,
                "schemaVersion": 1,
                "members": [{"lemma": "абзац", "slug": "абзац", "sources": ["homework"]}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload, report = promote_module.build_teacher_lesson_membership(
        decisions_path=decisions_path,
        manifest_path=manifest_path,
        membership_in=membership_in,
    )

    assert report == {
        "decision_lemmas": 3,
        "resolved_atlas_routes": 2,
        "unresolved_atlas_routes": 1,
        "newly_tagged_members": 2,
        "total_members": 2,
    }
    by_slug = {member["slug"]: member for member in payload["members"]}
    assert by_slug["абзац"]["sources"] == ["homework", "teacher_inventory"]
    assert by_slug["або"]["sources"] == ["teacher_inventory"]
    assert "не-в-атласі-placeholder" not in by_slug
