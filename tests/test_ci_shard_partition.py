"""Regression tests for CI Gate's duration-balanced pytest partition."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

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
            "duration_cache_key": "cache-key",
            "duration_mode": "cache",
            "duration_snapshot_digest": "duration-digest",
            "grouping": "file",
            "markexpr": pytest_shards.REQUIRED_MARKEXPR,
            "partition_mode": "lpt-durations",
            "planner_schema_version": pytest_shards.PLANNER_SCHEMA_VERSION,
            "selection_digest": pytest_shards.SELECTION_DIGEST,
            "serial_nodeids": list(pytest_shards.SERIAL_TESTS) if shard_id == 1 else [],
            "shard_count": len(selected),
            "shard_id": shard_id,
            "source_sha": "source-sha",
        }
        (shard / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (shard / "test-nodeids.txt").write_text(f"{nodeid}\n", encoding="utf-8")
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


def test_assign_shards_is_invariant_to_collection_and_duration_map_order() -> None:
    nodeids = [
        "tests/test_a.py::test_one",
        "tests/test_a.py::test_two",
        "tests/test_b.py::test_one",
        "tests/test_c.py::test_one",
    ]
    durations = {
        "tests/test_a.py::test_one": 8.0,
        "tests/test_a.py::test_two": 2.0,
        "tests/test_b.py::test_one": 6.0,
        "tests/test_c.py::test_one": 4.0,
    }

    forward = pytest_shards.assign_shards(nodeids, 2, durations)
    reversed_order = pytest_shards.assign_shards(list(reversed(nodeids)), 2, dict(reversed(list(durations.items()))))

    assert [set(shard) for shard in forward] == [set(shard) for shard in reversed_order]


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


def test_write_shard_plans_collect_independently_from_one_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(8)]
    durations_path = tmp_path / "durations.json"
    durations_path.write_text(
        json.dumps({"node_durations": {nodeid: float(index + 1) for index, nodeid in enumerate(selected)}}),
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "snapshot.json"
    pytest_shards.write_duration_snapshot(
        durations_path=durations_path,
        output=snapshot_path,
        source_sha="event-sha",
        cache_primary_key="cache-key",
        cache_matched_key="cache-key",
        cache_hit="true",
    )
    collected = 0

    def fake_collect() -> list[str]:
        nonlocal collected
        collected += 1
        return selected

    monkeypatch.setattr(pytest_shards, "collect_nodeids", fake_collect)
    for shard_id in range(1, pytest_shards.SHARD_COUNT + 1):
        pytest_shards.write_shard_plan(
            snapshot_path=snapshot_path,
            output_dir=tmp_path / f"shard-{shard_id}",
            shard_id=shard_id,
            expected_source_sha="event-sha",
        )

    assert collected == pytest_shards.SHARD_COUNT
    plans = [
        json.loads((tmp_path / f"shard-{shard_id}" / "plan.json").read_text(encoding="utf-8"))
        for shard_id in range(1, pytest_shards.SHARD_COUNT + 1)
    ]
    expected = pytest_shards.assign_shards(
        selected,
        pytest_shards.SHARD_COUNT,
        {nodeid: float(index + 1) for index, nodeid in enumerate(selected)},
    )
    assert [plan["assigned_nodeids"] for plan in plans] == expected
    assert len({plan["collected_digest"] for plan in plans}) == 1
    assert len({plan["duration_snapshot_digest"] for plan in plans}) == 1
    assert sorted(nodeid for plan in plans for nodeid in plan["assigned_nodeids"]) == selected


def test_verify_artifacts_accepts_complete_partition(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)

    pytest_shards.verify_artifacts(tmp_path, 4)


def test_verify_artifacts_requires_immutable_metadata_for_ci(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)
    plan_path = tmp_path / "pytest-shard-2" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["duration_snapshot_digest"] = "drifted"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RuntimeError, match="duration_snapshot_digest"):
        pytest_shards.verify_artifacts(tmp_path, 4, require_plan_metadata=True)


def test_verify_artifacts_requires_execution_receipts_for_ci(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)

    with pytest.raises(RuntimeError, match="execution receipt"):
        pytest_shards.verify_artifacts(tmp_path, 4, require_execution_receipt=True)


def test_verify_artifacts_accepts_ci_metadata_and_execution_receipts(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)
    for shard_id, nodeid in enumerate(selected, start=1):
        pytest_shards._write_execution_receipt(
            tmp_path / f"pytest-shard-{shard_id}" / "execution.json",
            planned_nodeids=[nodeid],
            reported_nodeids=[nodeid],
            pytest_exit_code=0,
        )

    pytest_shards.verify_artifacts(
        tmp_path,
        4,
        expected_source_sha="source-sha",
        require_plan_metadata=True,
        require_execution_receipt=True,
    )


def test_verify_artifacts_rejects_mispartitioned_plan(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)
    plan_path = tmp_path / "pytest-shard-4" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["assigned_nodeids"] = []
    plan["assigned_digest"] = pytest_shards._digest([])
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    _write_junit(tmp_path / "pytest-shard-4" / "main-junit.xml", 0)

    with pytest.raises(RuntimeError, match=r"empty shard|complete partition|test-nodeids.txt"):
        pytest_shards.verify_artifacts(tmp_path, 4)


def test_assert_set_integrity_rejects_empty_shard_and_omissions() -> None:
    nodeids = ["tests/a.py::test_a", "tests/b.py::test_b", "tests/c.py::test_c", "tests/d.py::test_d"]
    shards = [["tests/a.py::test_a"], ["tests/b.py::test_b"], ["tests/c.py::test_c"], ["tests/d.py::test_d"]]
    pytest_shards.assert_set_integrity(nodeids, shards)

    with pytest.raises(RuntimeError, match="empty shard"):
        pytest_shards.assert_set_integrity(nodeids, [["tests/a.py::test_a"], ["tests/b.py::test_b"], [], ["tests/d.py::test_d"]])

    with pytest.raises(RuntimeError, match="does not equal fast collection"):
        pytest_shards.assert_set_integrity(
            nodeids,
            [["tests/a.py::test_a"], ["tests/b.py::test_b"], ["tests/c.py::test_c"], ["tests/extra.py::test_x"]],
        )


def test_verify_artifacts_rejects_wrong_markexpr(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    _write_complete_artifacts(tmp_path, selected)
    plan_path = tmp_path / "pytest-shard-1" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["markexpr"] = "not atlas_release"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(RuntimeError, match="plan markexpr"):
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


def test_run_nodeids_records_reported_execution_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nodeids = tmp_path / "nodeids.txt"
    planned = ["tests/test_a.py::test_a", "tests/test_b.py::test_b"]
    nodeids.write_text("\n".join(planned) + "\n", encoding="utf-8")
    receipt = tmp_path / "execution.json"

    import pytest as real_pytest

    def fake_main(args: list[str], *, plugins: list[object]) -> int:
        assert args[-2:] == planned
        for nodeid in planned:
            plugins[0].pytest_runtest_logreport(type("Report", (), {"nodeid": nodeid})())
        return 0

    monkeypatch.setattr(real_pytest, "main", fake_main)

    assert pytest_shards.run_nodeids(nodeids, ["--", "-q"], receipt_path=receipt) == 0
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["planned_nodeids"] == planned
    assert data["reported_nodeids"] == planned
    assert data["reported_count"] == len(planned)
    assert data["pytest_exit_code"] == 0


def test_ci_workflow_uses_shard_local_planner_and_ci_gate_verifier() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    nightly = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "pytest-slow-nightly.yml"
    ).read_text(encoding="utf-8")

    assert "pytest-plan:" in workflow
    assert "pytest-fastlane:" in workflow
    assert "changed_tests.py" in workflow
    assert "timeout-minutes: 10" in workflow
    assert "pytest_shards.py plan-shard" in workflow
    assert "pytest_shards.py plan \\" not in workflow
    assert "pytest-duration-snapshot" in workflow
    assert "pytest-plans" not in workflow
    assert "pytest_shards.py verify-artifacts" in workflow
    assert "gate_required_results.py" in workflow
    assert "--dist=loadfile" in workflow
    assert "-m 'not atlas_release and not slow'" in workflow
    assert workflow.count("-m 'not atlas_release and not slow'") >= 2
    assert "name: CI Gate" in workflow
    assert "name: Ruff" in workflow
    assert "pytest-slow-nightly" not in workflow
    assert "-m 'slow and not atlas_release'" in nightly
    assert "Create or update infra issue on failure" in nightly
    assert "area:infra" in nightly
    assert nightly.splitlines()[0] == "name: Pytest slow nightly"


def test_ci_shard_planner_declares_matrix_shard_env() -> None:
    workflow = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    planner_step = next(
        step
        for step in workflow["jobs"]["python"]["steps"]
        if step.get("name") == "Collect and plan this pytest shard locally"
    )

    assert planner_step["env"]["SHARD"] == "${{ matrix.shard }}"


def test_required_lanes_exclude_live_model_setup_and_fastlane_is_slim() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    planner_steps = jobs["pytest-plan"]["steps"]
    planner_validate = next(step for step in planner_steps if step.get("name") == "Validate planner contract without collection")
    shard_steps = jobs["python"]["steps"]
    shard_install = next(step for step in shard_steps if step.get("name") == "Install dependencies")
    fastlane_steps = jobs["pytest-fastlane"]["steps"]
    fastlane_install = next(step for step in fastlane_steps if step.get("name") == "Install slim fastlane test dependencies")
    fastlane_run = next(step for step in fastlane_steps if step.get("name") == "Run directly changed test modules")

    assert jobs["python"]["needs"] == ["landing-class"]
    assert "validate-snapshot" in planner_validate["run"]
    assert all("Install planner dependencies" not in str(step.get("name")) for step in planner_steps)
    for step in (shard_install,):
        run = step["run"]
        assert "torch==2.13.0" not in run
        assert "download.pytorch.org" not in run
        assert "|stanza)" in run
    assert "stanza_resources" not in "\n".join(str(step) for step in shard_steps)

    assert "requirements-fastlane.txt" in fastlane_install["run"]
    assert "-c requirements-lock.txt" in fastlane_install["run"]
    assert "pip install --no-deps -r" not in fastlane_install["run"]
    assert "No module named" in fastlane_run["run"]
    assert "CPU torch" in fastlane_run["run"]
    names = [step.get("name", "") for step in fastlane_steps]
    assert names.index("Select directly changed test modules") < names.index("Install slim fastlane test dependencies")


def test_codeql_default_setup_scope_excludes_content_generated_and_sparse_paths() -> None:
    config_path = Path(__file__).resolve().parents[1] / ".github" / "codeql" / "codeql-config.yml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert set(config["paths-ignore"]) >= {
        "curriculum/**",
        "site/public/lexicon/**",
        "packages/activity-kit/src/*.generated.ts",
        "scripts/entire/external_agents/entire-agent-kimi/**",
        "scripts/rag/apple_vision_ocr.swift",
    }


def test_required_markexpr_constant_matches_ci_and_addopts_boundary() -> None:
    """addopts stays atlas-only; required gate adds not slow via CLI -m everywhere."""
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert "addopts = \"-v --tb=short -m 'not atlas_release'\"" in pyproject
    assert "not slow" not in pyproject.split("addopts")[1].split("\n")[0]
    assert pytest_shards.REQUIRED_MARKEXPR == "not atlas_release and not slow"
    assert pytest_shards.SLOW_MARKEXPR == "slow and not atlas_release"
    assert "-m" in pytest_shards.COMMON_ARGS
    assert pytest_shards.REQUIRED_MARKEXPR in pytest_shards.COMMON_ARGS
    assert "--strict-markers" in pytest_shards.COMMON_ARGS
