"""Regression coverage for teacher-lesson intake promotion ledgers."""

import json
import re
import sqlite3
from pathlib import Path
from types import MappingProxyType

import pytest
import yaml

from scripts.audit.generate_source_inventory_review_candidates import COMMITTED_SOURCE_INVENTORIES
from scripts.audit.source_inventory_intake import read_source_inventories, read_source_inventory
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
from scripts.verification.vesum import InspectionStatus, inspect_words

DELTA_INVENTORY = (
    PROJECT_ROOT / "registry/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-2026-09-02-delta.yaml"
)
DELTA_DECISIONS = (
    PROJECT_ROOT / "registry/lexicon/source-inventory-review-decisions/2026-09-02-teacher-lesson-delta-approve.yaml"
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


@pytest.fixture(scope="module")
def source_records():
    """Share parsed, frozen source rows while each validation runs afresh."""
    delta = tuple(read_source_inventory(DELTA_INVENTORY, project_root=PROJECT_ROOT))
    committed = read_source_inventories(COMMITTED_SOURCE_INVENTORIES, project_root=PROJECT_ROOT)
    index = MappingProxyType(
        {
            (record.lemma, record.inventory_path, record.source_locator): record
            for record in (*committed, *delta)
        }
    )
    return delta, index


def test_default_full_decisions_is_a_committed_repository_file() -> None:
    relative_path = DEFAULT_FULL_DECISIONS.relative_to(PROJECT_ROOT)

    assert relative_path == (
        Path("registry")
        / "lexicon"
        / "source-inventory-review-decisions"
        / "2026-07-23-alona-full-document-intake.yaml"
    )
    assert DEFAULT_FULL_DECISIONS.is_file()


def test_case_preserved_vesum_proper_names_do_not_resolve_to_common_noun(tmp_path, monkeypatch) -> None:
    db = tmp_path / "vesum.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany(
            "INSERT INTO forms VALUES (?,?,?,?)",
            [
                ("Бандера", "Бандера", "noun", "noun:anim:m:v_naz:prop:lname"),
                ("бандера", "бандера", "noun", "noun:anim:m:v_naz"),
                ("Вифлеєм", "Вифлеєм", "noun", "noun:inanim:m:v_naz:prop:geo"),
            ],
        )
    analyses = promote_module._vesum_analyses(["Бандера", "Вифлеєм", "бандера"], db)
    assert promote_module._canonical_lemma("Бандера", analyses["Бандера"], preserve_case=True) == "Бандера"
    assert promote_module._canonical_lemma("Вифлеєм", analyses["Вифлеєм"], preserve_case=True) == "Вифлеєм"
    assert promote_module._vesum_pos(analyses["Бандера"], reviewed_proper_name=True) == "proper noun"
    assert promote_module._vesum_pos(analyses["Вифлеєм"], reviewed_proper_name=True) == "proper noun"
    assert promote_module._vesum_pos(analyses["бандера"]) == "noun"

    ledger = tmp_path / "reviewed.yaml"
    ledger.write_text(
        yaml.safe_dump(
            {
                "decisions": [
                    {
                        "lemma": lemma,
                        "decision": "approve_for_publish",
                        "approved_pos": "proper noun",
                        "approved_gloss": gloss,
                        "source_inventory": {"locator": f"explicit vocabulary table 1 row {i}"},
                    }
                    for i, (lemma, gloss) in enumerate(
                        [("Бандера", "Bandera (surname)"), ("Вифлеєм", "Bethlehem")], start=1
                    )
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    assert promote_module._read_full_rows(ledger)[0].lemma == "Бандера"
    monkeypatch.setattr(promote_module, "_read_curated_rows", lambda _: [])
    monkeypatch.setattr(promote_module, "_dictionary_glosses", lambda *args: ({}, set()))
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    candidates, decisions, report = promote_module._build_rows(
        ledger, tmp_path / "unused-curated.yaml", manifest, db, None
    )
    assert report["canonical_lemmas"] == 2
    assert {(entry["lemma"], entry["pos"], entry["gloss"]) for entry in candidates} == {
        ("Бандера", "proper noun", "Bandera (surname)"),
        ("Вифлеєм", "proper noun", "Bethlehem"),
    }
    assert {decision["lemma"] for decision in decisions} == {"Бандера", "Вифлеєм"}


def test_unreviewed_all_caps_keep_original_candidates(tmp_path, monkeypatch) -> None:
    db = tmp_path / "vesum.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany(
            "INSERT INTO forms VALUES (?,?,?,?)",
            [
                ("застій", "застій", "noun", "noun:inanim:m:v_naz"),
                ("застій", "застояти", "verb", "verb:imperf"),
                ("штабу", "штаб", "noun", "noun:inanim:m:v_rod"),
                ("штабу", "штаба", "noun", "noun:inanim:m:v_rod"),
                ("ДНК", "ДНК", "abbr", "abbr"),
            ],
        )
    ledger = tmp_path / "reviewed.yaml"
    ledger.write_text(
        yaml.safe_dump(
            {
                "decisions": [
                    {
                        "lemma": lemma,
                        "decision": "approve_for_publish",
                        "approved_gloss": "test term",
                        "source_inventory": {"locator": f"explicit vocabulary table 1 row {i}"},
                    }
                    for i, lemma in enumerate(["ЗАСТІЙ", "застій", "ШТАБУ", "ДНК"], start=1)
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(promote_module, "_read_curated_rows", lambda _: [])
    monkeypatch.setattr(promote_module, "_dictionary_glosses", lambda *args: ({}, set()))
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    candidates, _, _ = promote_module._build_rows(ledger, tmp_path / "unused.yaml", manifest, db, None)
    assert [entry["lemma"] for entry in candidates] == ["застій", "штабу"]


def test_reviewed_name_without_exact_proper_analysis_is_held(tmp_path, monkeypatch) -> None:
    db = tmp_path / "vesum.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.execute("INSERT INTO forms VALUES ('калина','калина','noun','noun:inanim:f:v_naz')")
    ledger = tmp_path / "reviewed.yaml"
    ledger.write_text(
        yaml.safe_dump(
            {
                "decisions": [
                    {
                        "lemma": "Калина",
                        "decision": "approve_for_publish",
                        "approved_pos": "proper noun",
                        "approved_gloss": "Kalyna (name)",
                        "source_inventory": {"locator": "explicit vocabulary table 1 row 1"},
                    }
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(promote_module, "_read_curated_rows", lambda _: [])
    monkeypatch.setattr(promote_module, "_dictionary_glosses", lambda *args: ({}, set()))
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    candidates, decisions, report = promote_module._build_rows(ledger, tmp_path / "unused.yaml", manifest, db, None)
    assert candidates == decisions == []
    assert report["held_without_english_anchor"] == 1


def test_reviewed_common_words_accept_vesum_even_when_marked_invalid(tmp_path, monkeypatch) -> None:
    words = ["папка", "накаркати", "деталька", "кохана", "рідні", "озвучка", "чізкейк"]
    reviewed = json.loads(
        (PROJECT_ROOT / "registry/lexicon/curated-membership-reconciliation-9151.json").read_text(encoding="utf-8")
    )
    table = {row["lemma"]: row for row in reviewed["rows"] if row["lemma"] in words}
    assert set(table) == set(words)
    assert {word for word in words if table[word]["vesum"]["status"] == "KNOWN_INVALID"} == {
        "папка", "накаркати"
    }
    assert all(table[word]["ulif_lexical_attestation"] for word in ("папка", "накаркати"))
    assert all(
        table[word]["decision"] == "ADMIT" and table[word]["vesum"]["status"] == "CLEAN"
        and not table[word]["ulif_lexical_attestation"]
        for word in ("деталька", "кохана", "рідні", "озвучка", "чізкейк")
    )
    db = tmp_path / "vesum.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany(
            "INSERT INTO forms VALUES (?,?,?,?)",
            [(word, word, "noun", "noun:v_naz") for word in words],
        )
        conn.execute(
            "CREATE TABLE forms_all (id INTEGER, entry_id INTEGER, word_form TEXT, lemma TEXT, "
            "pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT)"
        )
        conn.execute(
            "CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT)"
        )
        conn.executemany(
            "INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)",
            [(i, i, word, word, "noun", "noun:v_naz", None, "fixture") for i, word in enumerate(words, start=1)],
        )
        conn.executemany(
            "INSERT INTO form_markers VALUES (?, 'bad', 'fixture', 'lexical')",
            [(words.index(word) + 1,) for word in ("папка", "накаркати")],
        )
    inspection = inspect_words(words, db_path=db)
    assert {word for word in words if inspection[word].status == InspectionStatus.KNOWN_INVALID} == {
        "папка", "накаркати"
    }
    ledger = tmp_path / "reviewed.yaml"
    ledger.write_text(
        yaml.safe_dump(
            {
                "decisions": [
                    {
                        "lemma": word,
                        "decision": "approve_for_publish",
                        "approved_pos": "noun",
                        "approved_gloss": "reviewed gloss",
                        "source_inventory": {"locator": f"explicit vocabulary table 1 row {i}"},
                    }
                    for i, word in enumerate(words, start=1)
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(promote_module, "_read_curated_rows", lambda _: [])
    monkeypatch.setattr(promote_module, "_dictionary_glosses", lambda *args: ({}, set()))
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}', encoding="utf-8")
    candidates, _, _ = promote_module._build_rows(ledger, tmp_path / "unused.yaml", manifest, db, None)
    assert {entry["lemma"] for entry in candidates} == set(words)


def test_private_teacher_lesson_delta_inventory_is_privacy_safe(source_records) -> None:
    records, _ = source_records

    assert len(records) == DELTA_HEADWORD_COUNT
    assert {record.source_family for record in records} == {"teacher_lesson"}
    assert {record.extraction_mode for record in records} == {"curated_headword"}
    assert all(record.source_url is None and record.source_path is None for record in records)
    assert all(_SAFE_LOCATOR.fullmatch(record.source_locator or "") for record in records)

    inventory_text = DELTA_INVENTORY.read_text(encoding="utf-8")
    assert DELTA_SOURCE_SHAPE_SHA256 in inventory_text
    assert ".docx" not in inventory_text.lower()
    assert "alona" not in inventory_text.lower()


def test_private_teacher_lesson_delta_decisions_validate_as_practice_only(source_records) -> None:
    _, source_index = source_records
    summary = validate_decision_file(DELTA_DECISIONS, source_index=source_index)
    # Match the validator's safe C loader for this 8.6 MB ledger. The full
    # validation above still runs independently on every test invocation.
    safe_loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    payload = yaml.load(DELTA_DECISIONS.read_text(encoding="utf-8"), Loader=safe_loader)

    assert summary["rows"] == DELTA_HEADWORD_COUNT
    assert summary["decision_counts"] == {"approve_for_publish": DELTA_HEADWORD_COUNT}
    assert payload["source_queue"]["total_queue_rows"] == DELTA_HEADWORD_COUNT
    assert payload["source_queue"]["approved_in_queue"] == DELTA_HEADWORD_COUNT
    assert all(
        row["surface_admission"] == {"practice": True, "cloze": False, "daily": False} for row in payload["decisions"]
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

    _synthetic_inventory_reads(monkeypatch, candidates)
    report = {
        "source_rows": len(lemmas),
        "canonical_lemmas": len(lemmas),
        "collapsed_source_rows": 0,
        "candidates_with_english_anchor": len(lemmas),
        "held_without_english_anchor": 0,
        "dictionary_or_manifest_gloss_fallbacks": 0,
    }
    monkeypatch.setattr(promote_module, "_build_rows", lambda *a, **kw: (candidates, decisions, report))

    # Route every stateful path under tmp_path; never touch the real journal/lock.
    intake_dir = tmp_path / "intake"
    monkeypatch.setattr(promote_module, "DEFAULT_INTAKE_DIR", intake_dir)
    monkeypatch.setattr(promote_module, "DEFAULT_JOURNAL", intake_dir / "journal.json")
    monkeypatch.setattr(promote_module, "DEFAULT_LOCK", intake_dir / "promotion.lock")
    monkeypatch.setattr(promote_module, "STAGED_MANIFEST", tmp_path / "manifest.staged.json")
    monkeypatch.setattr(promote_module, "STAGED_FINGERPRINT", tmp_path / "manifest.staged.fingerprint.json")

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

    def _fake_enrich_entry(entry, conn, kaikki_lookup, **_kwargs):
        enriched_lemmas.append(entry["lemma"])
        entry["enrichment"] = True
        return True

    monkeypatch.setattr(promote_module.enrich_module, "enrich_entry", _fake_enrich_entry)
    monkeypatch.setattr(promote_module.enrich_module, "_load_kaikki_lookup", lambda: {})

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"entries": [], "stats": {}}, ensure_ascii=False), encoding="utf-8")
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
        plan_out=tmp_path / "plan.json",
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
    _synthetic_inventory_reads(monkeypatch, [entry])
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
        plan_out=tmp_path / "plan.json",
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
        "decisions": [{"lemma": lemma, "decision": "approve_for_publish", "approved_pos": "noun"} for lemma in lemmas],
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


def _synthetic_inventory_reads(monkeypatch, candidates):
    """Keep the real ledger validator; replace only its corpus input."""
    from scripts.audit.source_inventory_intake import SourceInventoryRecord

    records = [
        SourceInventoryRecord(
            lemma=entry["lemma"], source_family="teacher_lesson",
            source_id=promote_module.PUBLIC_SOURCE_ID,
            extraction_mode=promote_module.PUBLIC_EXTRACTION_MODE,
            inventory_path=promote_module.PUBLIC_INVENTORY_PATH,
            inventory_locator=entry["source_provenance"][0]["source_locator"],
            source_locator=entry["source_provenance"][0]["source_locator"],
        )
        for entry in candidates
    ]
    monkeypatch.setattr(promote_module.planner.decisions, "read_source_inventories", lambda *a, **kw: records)


@pytest.fixture
def temp_promotion(tmp_path, monkeypatch):
    candidates, decisions = zip(*[
        _fake_candidate_and_decision(lemma, locator=f"private source unit {i} paragraph 1")
        for i, lemma in enumerate(("fixture-routed", "fixture-unrouted"), 1)
    ], strict=True)
    candidates, decisions = list(candidates), list(decisions)
    _synthetic_inventory_reads(monkeypatch, candidates)
    reviewed = tmp_path / "reviewed.yaml"
    promote_module._write_decisions(decisions, reviewed)
    report = {"canonical_lemmas": 2, "held_without_english_anchor": 0}

    def extract(full, curated, manifest, vesum, sources):
        # Review ledger consumed before the shared candidate artifact is replaced.
        assert yaml.safe_load(full.read_bytes())["decisions"] == decisions
        return candidates, decisions, report

    monkeypatch.setattr(promote_module, "_build_rows", extract)
    for attr, filename in (
        ("DEFAULT_INTAKE_DIR", "journal-dir"), ("DEFAULT_JOURNAL", "journal-dir/journal.json"),
        ("DEFAULT_LOCK", "journal-dir/lock"), ("STAGED_MANIFEST", "staged.json"),
        ("STAGED_FINGERPRINT", "staged-fingerprint.json"),
    ):
        monkeypatch.setattr(promote_module, attr, tmp_path / filename)
    monkeypatch.setattr(promote_module, "_enrich_promoted_entries", lambda *a, **kw: None)
    monkeypatch.setattr(promote_module.verify_manifest, "main", lambda argv: 0)
    monkeypatch.setattr(promote_module, "_conformance_violation_keys", lambda path: set())
    monkeypatch.setattr(promote_module, "write_fingerprint", lambda path, **kw: path.write_text('{"synthetic": true}'))
    manifest = tmp_path / "manifest.json"
    routed = {**candidates[0], "url_slug": "fixture-routed"}
    manifest.write_text(json.dumps({"entries": [routed], "stats": {}}))
    fingerprint = tmp_path / "fingerprint.json"
    fingerprint.write_bytes(b'{"original": true}\n')
    vesum = tmp_path / "unused.db"
    vesum.touch()
    membership = tmp_path / "membership-in.json"
    membership.write_text('{"members": []}')
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    kwargs = dict(
        full_decisions=reviewed, curated_inventory=tmp_path / "unused.yaml", manifest=manifest,
        fingerprint=fingerprint, vesum_db=vesum, sources_db=None,
        candidates_out=tmp_path / promote_module.CANDIDATES_FILENAME,
        decisions_out=tmp_path / promote_module.DECISIONS_FILENAME, write=False,
    )
    return kwargs, candidates, decisions, report, membership


def _read_temp_artifacts(root):
    return (
        json.loads((root / promote_module.CANDIDATES_FILENAME).read_bytes()),
        yaml.safe_load((root / promote_module.DECISIONS_FILENAME).read_bytes()),
        json.loads((root / promote_module.PLAN_FILENAME).read_bytes()),
    )


def test_temp_artifacts_destination_readback_and_lifetime(tmp_path, monkeypatch, temp_promotion):
    kwargs, candidates, decisions, _, _ = temp_promotion
    original = kwargs["manifest"].read_bytes(), kwargs["fingerprint"].read_bytes()
    for label in ("first-root", "second-root"):
        root = tmp_path / label
        root.mkdir()
        monkeypatch.setenv("TMPDIR", str(root))
        argv = ["--apply", "--report", "--full-decisions", str(kwargs["full_decisions"]),
                "--manifest", str(kwargs["manifest"]), "--fingerprint", str(kwargs["fingerprint"]),
                "--vesum-db", str(kwargs["vesum_db"])]
        assert promote_module.main(argv) == 0
        payload, ledger, plan = _read_temp_artifacts(root)
        assert payload["auto_merge"] == candidates and ledger["decisions"] == decisions
        assert plan["counts"]["proposed_additions"] == 1
        assert plan["counts"]["skipped_existing"] == 1
        assert plan["counts"]["missing_candidates"] == 0
        assert plan["source_candidate_payload"] == str(root / promote_module.CANDIDATES_FILENAME)
        assert (kwargs["manifest"].read_bytes(), kwargs["fingerprint"].read_bytes()) == original
        for entry in plan["proposed_manifest_additions"]:
            assert _SAFE_LOCATOR.fullmatch(entry["source_inventory"]["locator"])
    assert _read_temp_artifacts(tmp_path / "first-root")[0] == _read_temp_artifacts(tmp_path / "second-root")[0]


def test_temp_decisions_default_membership_readback(tmp_path, monkeypatch, capsys, temp_promotion):
    kwargs, _, _, _, membership = temp_promotion
    assert promote_module.main([
        "--apply", "--full-decisions", str(kwargs["full_decisions"]),
        "--manifest", str(kwargs["manifest"]), "--vesum-db", str(kwargs["vesum_db"]),
    ]) == 0
    out = tmp_path / "membership-out.json"
    reader_args = ["--emit-membership", str(out), "--membership-in", str(membership),
                   "--manifest", str(kwargs["manifest"]), "--report"]
    assert promote_module.main(reader_args) == 0
    assert json.loads(capsys.readouterr().out)["resolved_atlas_routes"] == 1
    members = json.loads(out.read_bytes())["members"]
    assert members == [{"lemma": "fixture-routed", "slug": "fixture-routed", "sources": ["teacher_inventory"]}]
    changed_root = tmp_path / "changed-root"
    changed_root.mkdir()
    monkeypatch.setenv("TMPDIR", str(changed_root))
    with pytest.raises(FileNotFoundError):
        promote_module.main(reader_args)
    monkeypatch.delenv("TMPDIR")
    assert promote_module.main([*reader_args, "--decisions-in", str(kwargs["decisions_out"])]) == 0
    capsys.readouterr()


def test_temp_plan_override_and_invalid_root(tmp_path, monkeypatch, capsys, temp_promotion):
    kwargs, *_ = temp_promotion
    monkeypatch.delenv("TMPDIR")
    with pytest.raises(SystemExit) as help_exit:
        promote_module.main(["--help"])
    assert help_exit.value.code == 0
    help_text = capsys.readouterr().out
    assert "--plan-out" in help_text and "Caller" in help_text and "Exit codes:" in help_text
    plan_out = tmp_path / "explicit-plan.json"
    assert promote(**kwargs, plan_out=plan_out)["plan"]["proposed_additions"] == 1
    assert json.loads(plan_out.read_bytes())["counts"]["approved_decisions"] == 2
    # CLI explicit destinations also work without TMPDIR.
    assert promote_module.main([
        "--apply", "--full-decisions", str(kwargs["full_decisions"]),
        "--manifest", str(kwargs["manifest"]), "--vesum-db", str(kwargs["vesum_db"]),
        "--candidates-out", str(kwargs["candidates_out"]), "--decisions-out", str(kwargs["decisions_out"]),
        "--plan-out", str(plan_out),
    ]) == 0
    originals = {path: path.read_bytes() for path in (kwargs["candidates_out"], kwargs["decisions_out"], plan_out)}
    file_root = tmp_path / "file-root"
    file_root.touch()
    for invalid in (None, "relative", str(tmp_path / "absent"), str(file_root)):
        if invalid is not None:
            monkeypatch.setenv("TMPDIR", invalid)
        else:
            monkeypatch.delenv("TMPDIR", raising=False)
        with pytest.raises(ValueError, match="TMPDIR"):
            promote(**kwargs)
        with pytest.raises(ValueError, match="TMPDIR"):
            promote_module.main(["--apply", "--vesum-db", str(kwargs["vesum_db"])])
        assert all(path.read_bytes() == data for path, data in originals.items())
    repo_link = tmp_path / "repo-link"
    repo_link.symlink_to(PROJECT_ROOT, target_is_directory=True)
    for root in (PROJECT_ROOT, repo_link):
        monkeypatch.setenv("TMPDIR", str(root))
        with pytest.raises(promote_module.planner.SourceInventoryError):
            promote(**kwargs)
        with pytest.raises(promote_module.planner.SourceInventoryError):
            promote(**kwargs, plan_out=root / "private-plan.json")
        assert all(path.read_bytes() == data for path, data in originals.items())


@pytest.mark.parametrize("gate", ["missing_candidate", "held", "verification", "conformance", "cas"])
def test_temp_artifact_failure_gates_preserve_outputs(tmp_path, monkeypatch, temp_promotion, gate):
    kwargs, candidates, _, report, _ = temp_promotion
    kwargs["write"] = True
    original_manifest = kwargs["manifest"].read_bytes()
    original_fingerprint = kwargs["fingerprint"].read_bytes()
    if gate == "missing_candidate":
        candidates.pop()
        match = "missing candidates"
    elif gate == "held":
        report["held_without_english_anchor"] = 1
        match = "refusing a partial"
    elif gate == "verification":
        monkeypatch.setattr(promote_module.verify_manifest, "main", lambda argv: 7)
        match = "failed verification"
    elif gate == "conformance":
        monkeypatch.setattr(promote_module, "_conformance_violation_keys",
                            lambda path: {("fixture-unrouted", "fixture-violation")} if path == promote_module.STAGED_MANIFEST else set())
        match = "conformance"
    else:
        real_hash = promote_module._sha256_file
        calls = 0

        def changed_hash(path):
            nonlocal calls
            if path == kwargs["manifest"]:
                calls += 1
                if calls == 2:
                    return "concurrent-change"
            return real_hash(path)

        monkeypatch.setattr(promote_module, "_sha256_file", changed_hash)
        match = "CAS"
    with pytest.raises(RuntimeError, match=match):
        promote(**kwargs)
    payload, ledger, plan = _read_temp_artifacts(tmp_path)
    assert payload["generated_from"] == "promote_teacher_lesson_intake.v1"
    assert len(ledger["decisions"]) == 2
    assert plan["counts"]["approved_decisions"] == 2
    assert plan["counts"]["missing_candidates"] == (1 if gate == "missing_candidate" else 0)
    assert kwargs["manifest"].read_bytes() == original_manifest
    assert kwargs["fingerprint"].read_bytes() == original_fingerprint
