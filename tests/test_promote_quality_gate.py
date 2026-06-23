from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from scripts.build import promote_quality_gate as gate
from scripts.common.thresholds import seminar_promote_floors_for

SLUG = "koliadky-shchedrivky"


def _write_stub_repo(tmp_path: Path, *, slug: str = SLUG) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    module_dir = repo_root / "curriculum" / "l2-uk-en" / "folk" / slug
    plan_dir = repo_root / "curriculum" / "l2-uk-en" / "plans" / "folk"
    module_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)
    (plan_dir / f"{slug}.yaml").write_text("title: Stub plan\n", encoding="utf-8")
    (module_dir / "module.md").write_text("# Stub module\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("- prompt: Stub\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("- term: Stub\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("- url: https://example.com\n", encoding="utf-8")
    return repo_root, module_dir


def _passing_scores() -> dict[str, float]:
    floors = seminar_promote_floors_for("folk")
    assert floors is not None
    return {dim: floor + 0.1 for dim, floor in floors.items()}


def _record_passing(repo_root: Path, module_dir: Path, *, scores: dict[str, float] | None = None) -> dict:
    result = gate.record(
        "folk",
        SLUG,
        module_dir=module_dir,
        repo_root=repo_root,
        writer_family="anthropic",
        writer_agent="claude",
        writer_model="claude-opus-4.8",
        reviewer_family="openai",
        reviewer_agent="codex",
        reviewer_model="gpt-5.5",
        scores=scores or _passing_scores(),
        evidence={"pedagogical": "stub evidence"},
        scored_at="2026-06-23T00:00:00Z",
    )
    return result["sidecar"]


def _load_sidecar(module_dir: Path) -> dict:
    return json.loads((module_dir / "promote_quality.json").read_text(encoding="utf-8"))


def _write_sidecar(module_dir: Path, sidecar: dict) -> None:
    (module_dir / "promote_quality.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_content_hash_stable_and_changes_for_any_hashed_file(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    baseline = gate.content_hash("folk", SLUG, module_dir=module_dir, repo_root=repo_root)
    assert gate.content_hash("folk", SLUG, module_dir=module_dir, repo_root=repo_root) == baseline

    rel_paths = [
        Path("curriculum/l2-uk-en/plans/folk") / f"{SLUG}.yaml",
        Path("curriculum/l2-uk-en/folk") / SLUG / "module.md",
        Path("curriculum/l2-uk-en/folk") / SLUG / "activities.yaml",
        Path("curriculum/l2-uk-en/folk") / SLUG / "vocabulary.yaml",
        Path("curriculum/l2-uk-en/folk") / SLUG / "resources.yaml",
    ]
    for rel_path in rel_paths:
        path = repo_root / rel_path
        original = path.read_text(encoding="utf-8")
        path.write_text(original + "\nchanged\n", encoding="utf-8")
        changed = gate.content_hash("folk", SLUG, module_dir=module_dir, repo_root=repo_root)
        assert changed["digest"] != baseline["digest"], rel_path
        path.write_text(original, encoding="utf-8")

    assert gate.content_hash("folk", SLUG, module_dir=module_dir, repo_root=repo_root) == baseline


def test_verify_passes_valid_cross_family_sidecar(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    _record_passing(repo_root, module_dir)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["applicable"] is True
    assert report["passed"] is True
    assert {row["dim"] for row in report["per_dim"]} == set(seminar_promote_floors_for("folk") or {})


def test_verify_fails_closed_without_sidecar(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("missing sidecar" in failure for failure in report["failures"])


def test_verify_fails_closed_on_stale_digest_and_reports_path(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    _record_passing(repo_root, module_dir)
    (module_dir / "module.md").write_text("# Stub module\nchanged\n", encoding="utf-8")

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("module.md changed since scoring" in failure for failure in report["failures"])


def test_verify_fails_closed_on_same_family_reviewer(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    sidecar = _record_passing(repo_root, module_dir)
    sidecar["reviewer"]["family"] = "anthropic"
    _write_sidecar(module_dir, sidecar)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("must differ" in failure for failure in report["failures"])


def test_verify_fails_closed_on_deepseek_reviewer_for_folk(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    sidecar = _record_passing(repo_root, module_dir)
    sidecar["reviewer"]["family"] = "deepseek"
    _write_sidecar(module_dir, sidecar)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("deepseek" in failure for failure in report["failures"])


def test_verify_fails_closed_on_score_below_floor(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    scores = _passing_scores()
    scores["beauty"] = 8.4
    _record_passing(repo_root, module_dir, scores=scores)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("beauty" in failure and "below floor" in failure for failure in report["failures"])


def test_verify_fails_closed_on_weaker_recorded_floors(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    sidecar = _record_passing(repo_root, module_dir)
    sidecar["floors"]["beauty"] = 8.0
    _write_sidecar(module_dir, sidecar)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("recorded floor stale: beauty" in failure for failure in report["failures"])


def test_verify_fails_closed_on_missing_score_dim(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    sidecar = _record_passing(repo_root, module_dir)
    del sidecar["scores"]["beauty"]
    _write_sidecar(module_dir, sidecar)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("missing or invalid score: beauty" in failure for failure in report["failures"])


def test_verify_fails_closed_on_unknown_reviewer_family(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    sidecar = _record_passing(repo_root, module_dir)
    sidecar["reviewer"]["family"] = "unknown-family"
    _write_sidecar(module_dir, sidecar)

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("unknown reviewer family" in failure for failure in report["failures"])


@pytest.mark.parametrize("level", ["a1", "bio"])
def test_verify_passes_through_unenrolled_levels(tmp_path: Path, level: str) -> None:
    report = gate.verify(level, SLUG, module_dir=tmp_path / "missing", repo_root=tmp_path)

    assert report == {
        "applicable": False,
        "passed": True,
        "reason": "level not enrolled in pre-promote gate",
        "per_dim": [],
        "failures": [],
    }


def test_record_verify_round_trip_and_computes_digest_locally(tmp_path: Path) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)

    assert "content_hash" not in inspect.signature(gate.record).parameters
    sidecar = _record_passing(repo_root, module_dir)

    assert sidecar["content_hash"] == gate.content_hash(
        "folk",
        SLUG,
        module_dir=module_dir,
        repo_root=repo_root,
    )
    assert gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)["passed"] is True


def test_gate_reads_floors_from_thresholds_ssot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root, module_dir = _write_stub_repo(tmp_path)
    _record_passing(repo_root, module_dir)

    monkeypatch.setattr(gate, "seminar_promote_floors_for", lambda _level: {"pedagogical": 9.9})

    report = gate.verify("folk", SLUG, module_dir=module_dir, repo_root=repo_root)

    assert report["passed"] is False
    assert any("pedagogical" in failure for failure in report["failures"])
