"""Focused contract tests for the fail-closed BIO promotion ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.audit import bio_readiness_ledger as ledger


def _gates() -> dict[str, dict[str, str]]:
    return {
        name: {"status": "pass"}
        for name in (
            "inventory",
            "dossier",
            "dossier_xref",
            "dossier_grounding",
            "plan",
            "plan_check",
            "plan_language",
            "reading_packet",
            "reading_rights",
            "reading_or_rights",
            "wiki_pair",
            "wiki_completeness",
            "wiki_subject",
            "wiki_language",
            "wiki_grounding",
            "wiki_quote_verification",
            "image_rights",
            "discovery",
            "discovery_integrity",
            "hold",
            "no_active_hold",
            "cohort_promotion",
            "module_bundle",
            "mdx",
            "deterministic_build",
            "qg_result",
            "qg_pass",
            "corpus_hammer",
            "independent_content_review",
            "merged_publication",
        )
    }


@pytest.mark.parametrize(
    ("gate", "expected"),
    [
        ("dossier", "inventory"),
        ("dossier_grounding", "inventory"),
        ("plan", "source-ready"),
        ("plan_check", "source-ready"),
        ("wiki_pair", "plan-ready"),
        ("wiki_grounding", "plan-ready"),
        ("discovery", "wiki-ready"),
        ("cohort_promotion", "wiki-ready"),
        ("module_bundle", "module-ready"),
        ("deterministic_build", "module-ready"),
        ("qg_result", "module-built"),
        ("corpus_hammer", "qg-current"),
        ("independent_content_review", "qg-current"),
        ("merged_publication", "qg-current"),
    ],
)
def test_each_milestone_transition_stops_at_its_previous_reached_stage(gate: str, expected: str) -> None:
    gates = _gates()
    gates[gate]["status"] = "unknown"
    milestones = ledger.calculate_milestones(gates)

    assert max((name for name, reached in milestones.items() if reached), key=ledger.MILESTONES.index) == expected


def test_manual_unknown_and_structural_wiki_pass_do_not_grant_grounding() -> None:
    gates = _gates()
    gates["wiki_grounding"]["status"] = "unknown"

    milestones = ledger.calculate_milestones(gates)

    assert milestones["plan-ready"] is True
    assert milestones["wiki-ready"] is False
    assert ledger._manual_gate(None, Path("registry.yaml"), "slug", "wiki_grounding")["status"] == "unknown"


def test_reading_packet_presence_is_independent_of_plan_validity() -> None:
    assert ledger._plan_has_reading_packet({"readings": [{"title": "Source"}]}) is True
    assert ledger._plan_has_reading_packet({"readings": []}) is False


def test_active_hold_blocks_module_ready_even_when_other_inputs_pass() -> None:
    gates = _gates()
    gates["no_active_hold"]["status"] = "fail"

    milestones = ledger.calculate_milestones(gates)

    assert milestones["wiki-ready"] is True
    assert milestones["module-ready"] is False


def test_qg_pending_and_parallel_release_gates_are_not_inferred() -> None:
    gates = _gates()
    gates["qg_result"]["status"] = "unknown"
    gates["qg_pass"]["status"] = "unknown"
    milestones = ledger.calculate_milestones(gates)
    assert milestones["module-built"] is True
    assert ledger.release_state(milestones, gates) == "qg-pending"

    gates = _gates()
    gates["corpus_hammer"]["status"] = "unknown"
    gates["independent_content_review"]["status"] = "unknown"
    milestones = ledger.calculate_milestones(gates)
    assert milestones["qg-current"] is True
    assert milestones["shipped"] is False
    assert ledger.release_state(milestones, gates) == "release-review-pending"


def test_legacy_build_is_visible_without_skipping_promotion_gates() -> None:
    gates = _gates()
    gates["dossier_grounding"]["status"] = "unknown"
    gates["qg_result"]["status"] = "unknown"
    gates["qg_pass"]["status"] = "unknown"

    milestones = ledger.calculate_milestones(gates)

    assert milestones["source-ready"] is False
    assert milestones["module-built"] is False
    assert ledger.artifact_state(gates) == "module-built"
    assert ledger.release_state(milestones, gates) == "qg-pending"


def test_qg_store_unavailable_is_unknown_not_a_false_zero(tmp_path: Path) -> None:
    result = ledger._read_current_qg(tmp_path / "missing.db", "bio", "known", tmp_path / "module")

    assert result["store_available"] is False
    assert result["current"] is None
    gates = _gates()
    gates["qg_result"] = ledger._gate(result["current"])
    gates["qg_pass"] = ledger._gate(result["passed"])
    assert "QG_STORE_UNAVAILABLE" in ledger._blockers(gates)


@pytest.mark.parametrize(
    ("terminal_verdict", "expected_pass", "expected_release"),
    [("PASS", True, "release-review-pending"), ("REVISE", False, "qg-failed")],
)
def test_persisted_qg_row_controls_pass_and_release_state(
    tmp_path: Path, terminal_verdict: str, expected_pass: bool, expected_release: str
) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("# Модуль\n", encoding="utf-8")
    db = tmp_path / "qg.db"
    with sqlite3.connect(db) as connection:
        connection.execute(
            """
            CREATE TABLE llm_qg_runs (
                payload_json TEXT NOT NULL,
                run_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                reviewer_family TEXT,
                reviewer_model TEXT,
                gate_version TEXT,
                level TEXT NOT NULL,
                slug TEXT NOT NULL,
                content_sha TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO llm_qg_runs (
                payload_json, run_id, created_at, reviewer_family,
                reviewer_model, gate_version, level, slug, content_sha
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps({"aggregate": {"terminal_verdict": terminal_verdict}}),
                "run-1",
                "2026-07-09T00:00:00Z",
                "claude",
                "claude-opus-4-8",
                "v7.llm_qg.1",
                "bio",
                "known",
                ledger.content_sha_for_module(module_dir),
            ),
        )

    result = ledger._read_current_qg(db, "bio", "known", module_dir)

    assert result["store_available"] is True
    assert result["query_ok"] is True
    assert result["current"] is True
    assert result["passed"] is expected_pass
    gates = _gates()
    gates["qg_result"] = ledger._gate(result["current"])
    gates["qg_pass"] = ledger._gate(result["passed"])
    gates["corpus_hammer"]["status"] = "unknown"
    assert ledger.release_state(ledger.calculate_milestones(gates), gates) == expected_release


@pytest.mark.parametrize(
    "entry",
    [
        {
            "status": "approved",
            "reviewer_family": "claude",
            "date": "2026-07-09",
            "evidence_url": "https://example.test/evidence",
        },
        {
            "status": "pass",
            "reviewer_family": "robot",
            "date": "2026-07-09",
            "evidence_url": "https://example.test/evidence",
        },
        {
            "status": "pass",
            "reviewer_family": "claude",
            "date": "09-07-2026",
            "evidence_url": "https://example.test/evidence",
        },
        {"status": "pass", "reviewer_family": "claude", "date": "2026-07-09", "evidence_url": "file:///proof"},
    ],
)
def test_registry_rejects_malformed_manual_evidence(tmp_path: Path, entry: dict) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump({"version": 1, "entries": {"known": {"dossier_grounding": entry}}}), encoding="utf-8"
    )

    with pytest.raises(ledger.RegistryValidationError):
        ledger.load_manual_evidence(path, {"known"})


def test_registry_rejects_duplicate_and_off_manifest_slugs(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text(
        """version: 1
entries:
  known:
    dossier_grounding: &e {status: pass, reviewer_family: claude, date: 2026-07-09, evidence_url: https://example.test/a}
  known: *e
""",
        encoding="utf-8",
    )
    with pytest.raises(ledger.RegistryValidationError, match="duplicate"):
        ledger.load_manual_evidence(duplicate, {"known"})

    off_manifest = tmp_path / "off-manifest.yaml"
    off_manifest.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "entries": {
                    "missing": {
                        "dossier_grounding": {
                            "status": "pass",
                            "reviewer_family": "claude",
                            "date": "2026-07-09",
                            "evidence_url": "https://example.test/a",
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ledger.RegistryValidationError, match="off-manifest"):
        ledger.load_manual_evidence(off_manifest, {"known"})


def test_registry_requires_closure_metadata_for_an_active_hold(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "entries": {
                    "known": {
                        "hold": {
                            "status": "pass",
                            "reviewer_family": "codex",
                            "date": "2026-07-19",
                            "evidence_url": "https://example.test/reviewed-hold",
                            "active": True,
                            "reason": "An authoritative source conflict remains unresolved.",
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ledger.RegistryValidationError, match="active record needs"):
        ledger.load_manual_evidence(path, {"known"})


@pytest.mark.parametrize(
    ("gate", "status", "disposition"),
    [
        ("reading_rights", "pass", "not-approved"),
        ("reading_rights", "fail", "link-only-approved"),
        ("image_rights", "pass", "not-approved"),
        ("image_rights", "fail", "approved"),
    ],
)
def test_registry_rejects_rights_status_disposition_conflicts(
    tmp_path: Path, gate: str, status: str, disposition: str
) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "entries": {
                    "known": {
                        gate: {
                            "status": status,
                            "disposition": disposition,
                            "reviewer_family": "claude",
                            "date": "2026-07-09",
                            "evidence_url": "https://example.test/evidence",
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ledger.RegistryValidationError, match="conflicts"):
        ledger.load_manual_evidence(path, {"known"})


def test_registry_rejects_unreviewed_hold_status(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "entries": {
                    "known": {
                        "hold": {
                            "status": "fail",
                            "active": True,
                            "reason": "A real blocker",
                            "reviewer_family": "human",
                            "date": "2026-07-09",
                            "evidence_url": "https://example.test/evidence",
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ledger.RegistryValidationError, match="reviewed pass"):
        ledger.load_manual_evidence(path, {"known"})


def test_duplicate_manifest_is_rejected(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    curriculum.mkdir(parents=True)
    (curriculum / "curriculum.yaml").write_text(
        yaml.safe_dump({"levels": {"bio": {"modules": ["known", "known"]}}}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="duplicate slugs"):
        ledger.manifest_inventory(tmp_path, "bio")


def test_off_manifest_artifacts_include_wiki_source_registries(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum / "plans" / "bio").mkdir(parents=True)
    (curriculum / "bio" / "discovery").mkdir(parents=True)
    (curriculum / "bio" / "discovery" / "stray.yaml").write_text("topic: stray\n", encoding="utf-8")
    wiki = tmp_path / "wiki" / "figures"
    wiki.mkdir(parents=True)
    (wiki / "stray.sources.yaml").write_text("sources: []\n", encoding="utf-8")

    off_manifest = ledger._off_manifest_artifacts(tmp_path, "bio", {"known"})

    assert off_manifest["discovery"] == ["stray"]
    assert off_manifest["wiki_sources"] == ["stray"]


def test_cli_json_reports_one_bio_row_and_shared_resolver_handles_another_track(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum / "bio").mkdir(parents=True)
    (curriculum / "curriculum.yaml").write_text(
        yaml.safe_dump({"levels": {"bio": {"modules": ["known"]}}}), encoding="utf-8"
    )
    (curriculum / "bio" / "promotion-evidence.yaml").write_text("version: 1\nentries: {}\n", encoding="utf-8")
    monkeypatch.setattr(ledger, "PROJECT_ROOT", tmp_path)

    assert ledger.main(["--format", "json", "--llm-qg-db", str(tmp_path / "missing.db")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert [row["slug"] for row in output["rows"]] == ["known"]
    assert ledger.resolved_wiki_paths(tmp_path, "bio", "known")[0] == tmp_path / "wiki" / "figures" / "known.md"
    assert ledger.resolved_wiki_paths(tmp_path, "hist", "period")[0] == tmp_path / "wiki" / "periods" / "period.md"
