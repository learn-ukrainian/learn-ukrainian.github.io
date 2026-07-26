"""The CI node planner must make a complete, deterministic test partition.

This guards the exact failure mode that motivated the CI rebuild: every shard
can report success while a test simply is not assigned anywhere.  The planner
is deliberately independent of git, diff state, and the pull-request base.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci import pytest_evidence, pytest_shard, verify_pytest_evidence


def _synthetic_nodes() -> list[str]:
    ordinary = [
        f"tests/test_regular_{index}.py::test_case[{case}]"
        for index in range(24)
        for case in range(3)
    ]
    thread_sensitive = [
        "tests/orchestration/test_thread_handoff.py::test_handoff",
        "tests/orchestration/test_thread_restart_e2e.py::test_restart",
        "tests/test_pytest_worker_rlimit_isolation.py::test_worker_limit",
        "tests/wiki/test_ukrainian_wiki_corpus.py::test_encode",
    ]
    inventory = [
        "tests/test_source_inventory_intake.py::test_intake",
        "tests/test_source_inventory_review_decisions.py::test_review",
    ]
    bounded_network = ["tests/test_video_discovery.py::TestSearchChannel::test_returns_empty_on_timeout"]
    return sorted([*ordinary, *thread_sensitive, *inventory, *bounded_network])


def _owner(plans: list[list[str]], nodeid: str) -> int:
    return next(index for index, plan in enumerate(plans) if nodeid in plan)


def test_plans_cover_each_non_quarantined_node_once() -> None:
    nodes = _synthetic_nodes()
    quarantined = {"tests/test_regular_0.py::test_case[0]"}

    plans, emitted_quarantine = pytest_shard.build_plans(nodes, quarantined)

    assigned = [nodeid for plan in plans for nodeid in plan]
    assert sorted(assigned) == sorted(set(nodes) - quarantined)
    assert len(assigned) == len(set(assigned))
    assert emitted_quarantine == sorted(quarantined)
    assert all(plan for plan in plans)


def test_thread_and_inventory_nodes_each_stay_in_one_external_shard() -> None:
    nodes = _synthetic_nodes()
    plans, _ = pytest_shard.build_plans(nodes, ())

    thread_nodes = [nodeid for nodeid in nodes if pytest_shard._group_for(nodeid) == "thread-sensitive"]
    inventory_nodes = [nodeid for nodeid in nodes if pytest_shard._group_for(nodeid) == "source-inventory"]
    bounded_network_nodes = [nodeid for nodeid in nodes if pytest_shard._group_for(nodeid) == "bounded-network"]

    assert len({_owner(plans, nodeid) for nodeid in thread_nodes}) == 1
    assert len({_owner(plans, nodeid) for nodeid in inventory_nodes}) == 1
    assert len({_owner(plans, nodeid) for nodeid in bounded_network_nodes}) == 1


def test_plans_are_balanced_within_one_node() -> None:
    plans, _ = pytest_shard.build_plans(_synthetic_nodes(), ())

    sizes = [len(plan) for plan in plans]
    assert max(sizes) - min(sizes) <= 1


def test_plans_are_deterministic() -> None:
    nodes = _synthetic_nodes()

    assert pytest_shard.build_plans(nodes, ()) == pytest_shard.build_plans(nodes, ())


def test_wiki_mlx_safe_mode_excludes_the_mlx_override_contract() -> None:
    assert pytest_evidence._is_wiki_node("tests/wiki/test_ukrainian_wiki_corpus.py::test_encode")
    assert pytest_evidence._is_wiki_node("tests/test_wiki_source_attribution.py::test_source")
    assert not pytest_evidence._is_wiki_node("tests/test_mlx_bridge_gate.py::test_force_mlx_override")


def test_stale_quarantine_fails_closed() -> None:
    with pytest.raises(pytest_shard.ShardPlanError):
        pytest_shard.build_plans(_synthetic_nodes(), {"tests/not-real.py::test_missing"})


def test_main_coverage_is_an_explicit_evidence_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI_PYTEST_COVERAGE", raising=False)
    assert pytest_shard._coverage_enabled() is False

    monkeypatch.setenv("CI_PYTEST_COVERAGE", "1")
    assert pytest_shard._coverage_enabled() is True


def test_main_coverage_evidence_is_fail_closed(tmp_path: Path) -> None:
    quarantine = tmp_path / "quarantine.json"
    quarantine.write_text(json.dumps({"version": 1, "entries": []}), encoding="utf-8")
    evidence_root = tmp_path / "evidence"
    for shard in range(1, pytest_shard.DEFAULT_SHARD_COUNT + 1):
        artifact = evidence_root / f"pytest-evidence-{shard}"
        artifact.mkdir(parents=True)
        nodeid = f"tests/test_shard_{shard}.py::test_complete"
        (artifact / "plan.txt").write_text(f"{nodeid}\n", encoding="utf-8")
        (artifact / "executed.txt").write_text(f"{nodeid}\n", encoding="utf-8")
        (artifact / "quarantine.txt").write_text("", encoding="utf-8")
        (artifact / "run.json").write_text(
            json.dumps({"returncode": 0, "timed_out": False, "coverage_enabled": True}),
            encoding="utf-8",
        )
        (artifact / "coverage").write_bytes(b"coverage-data")

    summary = verify_pytest_evidence.verify(
        evidence_root,
        quarantine,
        pytest_shard.DEFAULT_SHARD_COUNT,
        require_coverage=True,
    )
    assert "pytest union: 5 planned/executed nodes" in summary

    (evidence_root / "pytest-evidence-3" / "coverage").unlink()
    with pytest.raises(pytest_shard.ShardPlanError, match="coverage evidence"):
        verify_pytest_evidence.verify(
            evidence_root,
            quarantine,
            pytest_shard.DEFAULT_SHARD_COUNT,
            require_coverage=True,
        )


def test_workflow_uses_the_node_planner_and_fail_closed_gate() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "scripts/ci/pytest_shard.py --repo-root . prepare" in workflow
    assert "--timeout-seconds 1800" in workflow
    assert pytest_shard.DEFAULT_SHARD_COUNT == 5
    assert "shard: [1, 2, 3, 4, 5]" in workflow
    assert "--shard-count 5" in workflow
    assert "-m scripts.ci.verify_pytest_evidence" in workflow
    assert "skipped and cancelled are failures" in workflow
    assert "CI_PYTEST_WIKI_NO_MLX" in workflow
    assert "./node_modules/.bin/playwright test" in workflow
    assert "npm --prefix site exec -- playwright test" not in workflow
    assert "needs: [pytest, web_quality, integrity]" in workflow
    assert "uv venv --python 3.12 .venv" in workflow
    assert "trufflesecurity/trufflehog@47e7b7cd74f578e1e3145d48f669f22fd1330ca6" in workflow
    assert "Validate BIO preparation capsules and active holds" in workflow
    assert "CI_PYTEST_COVERAGE" in workflow
    assert "--require-coverage" in workflow
    assert "coverage report --fail-under=35" in workflow
    for forbidden in ("GITHUB_BASE_REF", "changed-files", "paths-filter", "git diff"):
        assert forbidden not in workflow
