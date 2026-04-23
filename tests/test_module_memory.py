from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build import module_memory
from build.alignment_manifest import manifest_hash


def _manifest(label: str) -> dict[str, object]:
    return {
        "plan_hash": f"plan-{label}",
        "sources_hash": f"sources-{label}",
        "template_hashes": {"writer": f"template-{label}"},
        "canonical_anchor_hash": f"anchors-{label}",
        "tokenizer_version": f"tokenizer-{label}",
        "threshold_snapshot": {"level_config": {"words": label}, "review_target_score": 8.0},
        "decisions_subset": [("dec-001", label)],
    }


def test_schema_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "module-memory.yaml"
    current_manifest = _manifest("current")
    payload = {
        "plan_version": 3,
        "constraints": [{"id": "c_001", "status": "active"}],
        "history": [{"attempt": 1, "strategy": "write"}],
        "events": [{"type": "seed"}],
    }

    module_memory.save_module_memory(path, payload, current_manifest=current_manifest)
    loaded, invalidated = module_memory.load_module_memory(
        path,
        current_manifest=current_manifest,
        expected_plan_version=3,
    )
    saved = yaml.safe_load(path.read_text("utf-8"))

    assert invalidated is False
    assert loaded["alignment_manifest_hash"] == manifest_hash(current_manifest)
    assert loaded["constraints"] == payload["constraints"]
    assert loaded["history"] == payload["history"]
    assert "plan_hash" not in saved
    assert "sources_hash" not in saved
    assert saved["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)


def test_alignment_manifest_invalidation_clears_constraints_keeps_history(tmp_path: Path) -> None:
    path = tmp_path / "module-memory.yaml"
    original_manifest = _manifest("before")
    module_memory.save_module_memory(
        path,
        {
            "plan_version": 1,
            "constraints": [{"id": "c_001", "status": "active"}],
            "history": [{"attempt": 1, "strategy": "write"}],
        },
        current_manifest=original_manifest,
    )

    updated_manifest = _manifest("after")
    loaded, invalidated = module_memory.load_module_memory(
        path,
        current_manifest=updated_manifest,
        expected_plan_version=2,
    )

    assert invalidated is True
    assert loaded["constraints"] == []
    assert loaded["history"] == [{"attempt": 1, "strategy": "write"}]
    assert loaded["alignment_manifest_hash"] == manifest_hash(updated_manifest)
    assert loaded["events"][-1]["type"] == "alignment_manifest_invalidation"
    assert loaded["events"][-1]["previous_hash"] == manifest_hash(original_manifest)
    assert loaded["events"][-1]["current_hash"] == manifest_hash(updated_manifest)


def test_legacy_plan_hash_file_migrates_and_invalidates_on_first_read(
    tmp_path: Path,
    caplog,
) -> None:
    path = tmp_path / "module-memory.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "plan_hash": "legacy-plan",
                "plan_version": 4,
                "sources_hash": "legacy-sources",
                "constraints": [{"id": "c_001", "status": "active"}],
                "history": [{"attempt": 1, "strategy": "write"}],
                "events": [{"type": "seed"}],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    current_manifest = _manifest("legacy-current")
    with caplog.at_level("INFO"):
        loaded, invalidated = module_memory.load_module_memory(
            path,
            current_manifest=current_manifest,
            expected_plan_version=4,
        )
    saved = yaml.safe_load(path.read_text("utf-8"))

    assert invalidated is True
    assert loaded["constraints"] == []
    assert loaded["history"] == [{"attempt": 1, "strategy": "write"}]
    assert loaded["events"][-1]["type"] == "alignment_manifest_migration_invalidation"
    assert loaded["alignment_manifest_hash"] == manifest_hash(current_manifest)
    assert "alignment_manifest_hash" in saved
    assert "plan_hash" not in saved
    assert "sources_hash" not in saved
    assert saved["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)
    assert "Migrating legacy module memory without alignment_manifest_hash" in caplog.text


def test_reset_memory_wipes_file(tmp_path: Path) -> None:
    path = tmp_path / "module-memory.yaml"
    module_memory.save_module_memory(path, {"history": [{"attempt": 1}]})

    assert path.exists()
    assert module_memory.reset_module_memory(path) is True
    assert not path.exists()
    assert module_memory.reset_module_memory(path) is False


def test_conflict_detector_quarantines_same_scope_opposites() -> None:
    memory = {
        "constraints": [
            {
                "id": "c_001",
                "normalized_id": "nf_001",
                "status": "active",
                "scope": {"speaker": "teacher", "section_title": "Greetings", "target_lexeme": "ви"},
                "directive": "Teacher uses formal register (ви) in direct address",
            }
        ]
    }
    candidate = {
        "id": "c_002",
        "normalized_id": "nf_002",
        "status": "active",
        "scope": {"speaker": "teacher", "section_title": "Greetings", "target_lexeme": "ви"},
        "directive": "Teacher uses informal register (ти) in direct address",
        "source_finding_ids": ["nf_002"],
        "recur_count": 2,
    }

    updated = module_memory.upsert_constraint(memory, candidate)

    assert updated["constraints"][0]["status"] == "quarantined"
    assert updated["constraints"][1]["status"] == "quarantined"


def test_conflict_detector_ignores_different_scope_false_positive() -> None:
    memory = {
        "constraints": [
            {
                "id": "c_001",
                "normalized_id": "nf_001",
                "status": "active",
                "scope": {"speaker": "teacher", "section_title": "Greetings", "target_lexeme": "ви"},
                "directive": "Teacher uses formal register (ви) in direct address",
            }
        ]
    }
    candidate = {
        "id": "c_002",
        "normalized_id": "nf_002",
        "status": "active",
        "scope": {"speaker": "classmate", "section_title": "Hallway", "target_lexeme": "ти"},
        "directive": "Classmate uses informal register (ти) in direct address",
        "source_finding_ids": ["nf_002"],
        "recur_count": 2,
    }

    updated = module_memory.upsert_constraint(memory, candidate)

    assert [item["status"] for item in updated["constraints"]] == ["active", "active"]


def test_sources_manifest_hashes_target_tables_and_external_template(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    curriculum_root = project_root / "curriculum" / "l2-uk-en"
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True)
    (curriculum_root / "wiki" / "a1" / "demo").mkdir(parents=True)
    (curriculum_root / "wiki" / "a1" / "demo" / "packet.md").write_text("wiki", "utf-8")

    vesum_db = data_dir / "vesum.db"
    with sqlite3.connect(vesum_db) as connection:
        connection.execute("CREATE TABLE forms (lemma TEXT, form TEXT)")
        connection.execute("INSERT INTO forms VALUES ('мати', 'маю')")
        connection.commit()

    sources_db = data_dir / "sources.db"
    with sqlite3.connect(sources_db) as connection:
        connection.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, body)")
        connection.execute("CREATE VIRTUAL TABLE literary_fts USING fts5(title, body)")
        connection.execute("CREATE TABLE wiktionary (lemma TEXT, gloss TEXT)")
        connection.execute(
            "INSERT INTO textbooks_fts (title, body) VALUES ('t1', 'body 1')"
        )
        connection.execute(
            "INSERT INTO literary_fts (title, body) VALUES ('l1', 'body 2')"
        )
        connection.execute("INSERT INTO wiktionary VALUES ('мати', 'to have')")
        connection.commit()

    external_dir = tmp_path / "shared"
    external_dir.mkdir()
    writer_template = external_dir / "v6-write.md"
    writer_template.write_text("template", "utf-8")

    manifest = module_memory.compute_sources_manifest(
        project_root=project_root,
        curriculum_root=curriculum_root,
        level="a1",
        slug="demo",
        writer_template_path=writer_template,
    )

    assert "sqlite://data/vesum.db#forms" in manifest
    assert "sqlite://data/sources.db#textbooks_fts" in manifest
    assert "sqlite://data/sources.db#literary_fts" in manifest
    assert "sqlite://data/sources.db#dictionary_indexes" in manifest
    assert any(key.endswith("/v6-write.md") for key in manifest)
