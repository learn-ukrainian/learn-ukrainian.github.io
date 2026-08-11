"""Regression tests for CI Gate's duration-balanced pytest partition."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci import pytest_shards


def _write_junit(path: Path, count: int) -> None:
    path.write_text(f'<testsuite tests="{count}" />', encoding="utf-8")


def _write_complete_artifacts(root: Path, selected: list[str]) -> None:
    digest = pytest_shards._digest(selected)
    for shard_id, nodeid in enumerate(selected, start=1):
        shard = root / f"pytest-shard-{shard_id}"
        shard.mkdir()
        plan = {
            "assigned_digest": pytest_shards._digest([nodeid]),
            "assigned_nodeids": [nodeid],
            "collected_count": len(selected),
            "collected_digest": digest,
            "grouping": "file",
            "partition_mode": "lpt-durations",
            "serial_nodeids": list(pytest_shards.SERIAL_TESTS) if shard_id == 1 else [],
            "shard_count": len(selected),
            "shard_id": shard_id,
        }
        (shard / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        _write_junit(shard / "main-junit.xml", 1)
        if shard_id == 1:
            _write_junit(shard / "playground-junit.xml", len(pytest_shards.SERIAL_TESTS))


def test_assign_shards_is_complete_disjoint_balanced_and_file_grouped() -> None:
    nodeids = [
        "tests/test_heavy.py::test_a",
        "tests/test_heavy.py::test_b",
        "tests/test_medium.py::test_a",
        "tests/test_small_a.py::test_a",
        "tests/test_small_b.py::test_a",
        "tests/test_small_c.py::test_a",
    ]
    durations = {
        "tests/test_heavy.py::test_a": 6.0,
        "tests/test_heavy.py::test_b": 6.0,
        "tests/test_medium.py::test_a": 8.0,
        "tests/test_small_a.py::test_a": 4.0,
        "tests/test_small_b.py::test_a": 4.0,
        "tests/test_small_c.py::test_a": 4.0,
    }

    shards = pytest_shards.assign_shards(nodeids, 3, durations)

    assert sorted(nodeid for shard in shards for nodeid in shard) == sorted(nodeids)
    assert len({nodeid for shard in shards for nodeid in shard}) == len(nodeids)
    assert any({"tests/test_heavy.py::test_a", "tests/test_heavy.py::test_b"}.issubset(shard) for shard in shards)
    totals = [sum(durations[nodeid] for nodeid in shard) for shard in shards]
    assert max(totals) - min(totals) == 4.0


def test_unknown_file_uses_median_known_file_weight() -> None:
    nodeids = [
        "tests/test_fast.py::test_a",
        "tests/test_medium.py::test_a",
        "tests/test_slow.py::test_a",
        "tests/test_unknown.py::test_a",
    ]
    weights = pytest_shards._file_weights(
        nodeids,
        {
            "tests/test_fast.py::test_a": 1.0,
            "tests/test_medium.py::test_a": 3.0,
            "tests/test_slow.py::test_a": 9.0,
        },
    )

    assert weights["tests/test_unknown.py"] == 3.0


def test_write_plans_collects_once_and_marks_duration_lpt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(8)]
    collected = 0

    def fake_collect() -> list[str]:
        nonlocal collected
        collected += 1
        return selected

    monkeypatch.setattr(pytest_shards, "collect_nodeids", fake_collect)
    durations = tmp_path / "durations.json"
    durations.write_text(json.dumps({"node_durations": {selected[0]: 100.0}}), encoding="utf-8")

    pytest_shards.write_plans(durations_path=durations, output_dir=tmp_path / "plans")

    assert collected == 1
    plans = [json.loads((tmp_path / "plans" / f"pytest-shard-{index}" / "plan.json").read_text()) for index in range(1, 5)]
    assert {plan["partition_mode"] for plan in plans} == {"lpt-durations"}
    assert {plan["grouping"] for plan in plans} == {"file"}
    assert sorted(nodeid for plan in plans for nodeid in plan["assigned_nodeids"]) == selected


def test_verify_artifacts_accepts_complete_partition(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)

    pytest_shards.verify_artifacts(tmp_path, 4)


def test_verify_artifacts_rejects_mispartitioned_plan(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)
    plan_path = tmp_path / "pytest-shard-4" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["assigned_nodeids"] = []
    plan["assigned_digest"] = pytest_shards._digest([])
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    _write_junit(tmp_path / "pytest-shard-4" / "main-junit.xml", 0)

    with pytest.raises(RuntimeError, match="complete partition"):
        pytest_shards.verify_artifacts(tmp_path, 4)


def test_publish_durations_writes_main_dataset_and_rolling_p95(tmp_path: Path) -> None:
    logs = []
    for shard_id, seconds in enumerate((1.0, 2.0, 3.0, 4.0), start=1):
        path = tmp_path / f"shard-{shard_id}.log"
        path.write_text(f"  {seconds:.2f}s call     tests/test_{shard_id}.py::test_case\n", encoding="utf-8")
        logs.append(path)
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"slowest_shard_seconds": [2.0, 8.0]}), encoding="utf-8")
    output = tmp_path / "dataset.json"
    summary = tmp_path / "summary.md"

    pytest_shards.publish_durations(log_paths=logs, previous=previous, output=output, summary=summary)

    dataset = json.loads(output.read_text(encoding="utf-8"))
    assert dataset["node_durations"]["tests/test_4.py::test_case"] == 4.0
    assert dataset["slowest_shard_seconds"] == [2.0, 8.0, 4.0]
    assert "Slowest-shard p95: **8.00s** across 3 successful main run(s)." in summary.read_text(encoding="utf-8")


def test_run_nodeids_passes_exact_planner_output_to_pytest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text("tests/test_a.py::test_a\ntests/test_b.py::test_b\n", encoding="utf-8")
    captured: list[list[str]] = []

    import pytest as real_pytest

    monkeypatch.setattr(real_pytest, "main", lambda args: captured.append(list(args)) or 0)

    assert pytest_shards.run_nodeids(nodeids, ["--", "-q", "--dist=loadfile"]) == 0
    assert captured == [["-q", "--dist=loadfile", "tests/test_a.py::test_a", "tests/test_b.py::test_b"]]


def test_ci_workflow_uses_single_planner_and_ci_gate_verifier() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pytest-plan:" in workflow
    assert "pytest-fastlane:" in workflow
    assert "changed_tests.py" in workflow
    assert "timeout-minutes: 10" in workflow
    assert "pytest_shards.py plan" in workflow
    assert workflow.count("pytest_shards.py plan") == 1
    assert "pytest_shards.py verify-artifacts" in workflow
    assert "--dist=loadfile" in workflow
