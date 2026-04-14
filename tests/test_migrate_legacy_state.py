import json
from pathlib import Path

import pytest

from scripts.tools import migrate_legacy_state_to_v6 as migrate


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), "utf-8")


def test_v5_to_v6_mapping_correctness(tmp_path: Path) -> None:
    orch = tmp_path / "bio" / "orchestration" / "knyahynia-olha"
    _write_json(
        orch / "state.json",
        {
            "track": "bio",
            "slug": "knyahynia-olha",
            "mode": "v5",
            "phases": {
                "research": {
                    "status": "complete",
                    "ts": "2026-03-12T19:10:34Z",
                    "executor": {"type": "llm", "agent": "gemini", "model": "unknown"},
                },
                "discover": {
                    "status": "complete",
                    "ts": "2026-03-12T19:10:34Z",
                    "note": "merged-into-research",
                    "executor": {"type": "script", "name": "discover_passthrough"},
                },
            },
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None
    assert candidate.detected_mode == "v5"

    report = migrate.build_v6_state(candidate, migrated_at="2026-04-14T09:00:00Z")

    assert report.v6_state["mode"] == "v6"
    assert report.v6_state["track"] == "bio"
    assert report.v6_state["slug"] == "knyahynia-olha"
    assert report.v6_state["migrated_from"] == "v5"
    assert report.v6_state["migrated_at"] == "2026-04-14T09:00:00Z"
    assert list(report.v6_state["phases"]) == ["research"]
    assert report.v6_state["phases"]["research"]["status"] == "complete"
    assert report.v6_state["phases"]["research"]["ts"] == "2026-03-12T19:10:34Z"
    assert report.v6_state["phases"]["research"]["executor"]["agent"] == "gemini"
    assert report.v6_state["legacy_state"]["mode"] == "v5"
    assert report.mapped_pairs == [("research", "research"), ("discover", "research")]
    assert report.warnings == []


def test_v3_to_v6_mapping_correctness(tmp_path: Path) -> None:
    orch = tmp_path / "lit-fantastika" / "orchestration" / "kvitka-dead-mans-easter"
    _write_json(
        orch / "state-v3.json",
        {
            "track": "lit-fantastika",
            "slug": "kvitka-dead-mans-easter",
            "mode": "v3",
            "phases": {
                "v3-A": {
                    "status": "complete",
                    "ts": "2026-02-20T22:42:18Z",
                    "task_id": "v3-kvitka-dead-mans-easter-pA",
                    "mode": "full",
                }
            },
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None
    assert candidate.detected_mode == "v3"

    report = migrate.build_v6_state(candidate, migrated_at="2026-04-14T09:05:00Z")

    assert report.v6_state["migrated_from"] == "v3"
    assert list(report.v6_state["phases"]) == ["research"]
    assert report.v6_state["phases"]["research"]["status"] == "complete"
    assert report.v6_state["phases"]["research"]["task_id"] == "v3-kvitka-dead-mans-easter-pA"
    assert report.v6_state["legacy_state"]["phases"]["v3-A"]["mode"] == "full"
    assert report.mapped_pairs == [("v3-A", "research")]


def test_idempotent_on_v6_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    orch = tmp_path / "a2" / "orchestration" / "dative-pronouns"
    _write_json(
        orch / "state.json",
        {
            "mode": "v6",
            "track": "a2",
            "slug": "dative-pronouns",
            "phases": {"check": {"status": "complete", "ts": "2026-04-13T03:02:38Z"}},
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None
    assert candidate.detected_mode == "v6"

    monkey_target = str(tmp_path)
    original_root = migrate.CURRICULUM_ROOT
    migrate.CURRICULUM_ROOT = Path(monkey_target)
    try:
        rc = migrate.main(["--track", "a2", "--dry-run", "--limit", "1"])
    finally:
        migrate.CURRICULUM_ROOT = original_root

    assert rc == 0
    captured = capsys.readouterr().out
    assert "already mode=v6; skipping" in captured
    assert json.loads((orch / "state.json").read_text("utf-8"))["mode"] == "v6"


def test_legacy_state_preserved_in_full_for_both(tmp_path: Path) -> None:
    orch = tmp_path / "oes" / "orchestration" / "dual-number-intro"
    _write_json(
        orch / "state.json",
        {
            "track": "oes",
            "slug": "dual-number-intro",
            "mode": "v5",
            "phases": {
                "discover": {
                    "status": "complete",
                    "ts": "2026-03-14T00:27:34Z",
                    "note": "merged-into-research",
                },
                "research": {
                    "status": "complete",
                    "ts": "2026-03-14T00:27:34Z",
                    "task_id": "v5-dual-number-intro-pA",
                },
            },
        },
    )
    _write_json(
        orch / "state-v3.json",
        {
            "track": "oes",
            "slug": "dual-number-intro",
            "mode": "v3",
            "phases": {"v3-A": {"status": "failed", "ts": "2026-02-20T03:04:00Z"}},
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None
    assert candidate.detected_mode == "both"

    report = migrate.build_v6_state(candidate)

    assert report.v6_state["migrated_from"] == "v5"
    assert report.v6_state["legacy_state"]["v5"]["mode"] == "v5"
    assert report.v6_state["legacy_state"]["v3"]["mode"] == "v3"
    assert report.v6_state["phases"]["research"]["task_id"] == "v5-dual-number-intro-pA"


def test_unknown_phase_warns_but_migrates_known_phases(tmp_path: Path) -> None:
    orch = tmp_path / "bio" / "orchestration" / "mystery-module"
    _write_json(
        orch / "state.json",
        {
            "track": "bio",
            "slug": "mystery-module",
            "mode": "v5",
            "phases": {
                "research": {"status": "complete", "ts": "2026-03-12T19:10:34Z"},
                "weird-phase": {"status": "complete", "ts": "2026-03-12T19:10:35Z"},
            },
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None

    report = migrate.build_v6_state(candidate)

    assert list(report.v6_state["phases"]) == ["research"]
    assert report.v6_state["phases"]["research"]["status"] == "complete"
    assert len(report.warnings) == 1
    assert "weird-phase" in report.warnings[0]
    assert "__preserved_as_legacy__" in report.warnings[0]


def test_apply_renames_v3_and_verifies_round_trip(tmp_path: Path) -> None:
    orch = tmp_path / "lit-fantastika" / "orchestration" / "kvitka-dead-mans-easter"
    _write_json(
        orch / "state-v3.json",
        {
            "track": "lit-fantastika",
            "slug": "kvitka-dead-mans-easter",
            "mode": "v3",
            "phases": {"v3-A": {"status": "complete", "ts": "2026-02-20T22:42:18Z"}},
        },
    )

    candidate = migrate.detect_candidate(orch)
    assert candidate is not None
    report = migrate.build_v6_state(candidate, migrated_at="2026-04-14T09:05:00Z")

    applied = migrate.apply_migration(report)
    backup_path = orch / "state-v3.json.pre-migration.bak"

    assert backup_path.exists()
    assert not (orch / "state-v3.json").exists()
    assert (orch / "state.json").exists()
    migrate.verify_v6_state("lit-fantastika", "kvitka-dead-mans-easter", orch, applied.v6_state)
    assert applied.backups == [(orch / "state-v3.json", backup_path)]
