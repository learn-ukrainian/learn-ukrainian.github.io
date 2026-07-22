"""Tests for the deterministic required-pytest shard planner (#5657)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ci import pytest_shards


def test_assign_shards_is_complete_disjoint_and_duration_balanced() -> None:
    nodeids = [f"tests/test_{number}.py::test_case" for number in range(8)]
    durations = {nodeid: 8.0 if number < 4 else 1.0 for number, nodeid in enumerate(nodeids)}

    shards = pytest_shards.assign_shards(nodeids, 4, durations)

    assert sorted(nodeid for shard in shards for nodeid in shard) == sorted(nodeids)
    assert sum(len(shard) for shard in shards) == len(set(nodeids))
    totals = [sum(durations[nodeid] for nodeid in shard) for shard in shards]
    assert max(totals) == min(totals)


def test_verify_artifacts_rejects_an_omitted_selected_test(tmp_path: Path) -> None:
    selected = ["tests/test_a.py::test_a", "tests/test_b.py::test_b"]
    digest = pytest_shards._digest(selected)
    for shard_id, assigned in ((1, selected[:1]), (2, [])):
        shard = tmp_path / f"pytest-shard-{shard_id}"
        shard.mkdir()
        (shard / "plan.json").write_text(
            json.dumps(
                {
                    "assigned_nodeids": assigned,
                    "assigned_digest": pytest_shards._digest(assigned),
                    "collected_count": len(selected),
                    "collected_digest": digest,
                    "serial_nodeids": list(pytest_shards.SERIAL_TESTS) if shard_id == 1 else [],
                    "shard_count": 2,
                    "shard_id": shard_id,
                }
            ),
            encoding="utf-8",
        )
        (shard / "main-junit.xml").write_text(f'<testsuite tests="{len(assigned)}" />', encoding="utf-8")
        if shard_id == 1:
            (shard / "cache-junit.xml").write_text('<testsuite tests="2" />', encoding="utf-8")
            (shard / "playground-junit.xml").write_text('<testsuite tests="1" />', encoding="utf-8")

    try:
        pytest_shards.verify_artifacts(tmp_path, 2)
    except RuntimeError as error:
        assert "complete partition" in str(error)
    else:
        raise AssertionError("an omitted selected test must fail artifact verification")


def test_verify_artifacts_accepts_a_complete_disjoint_partition(tmp_path: Path) -> None:
    selected = [f"tests/test_{number}.py::test_case" for number in range(4)]
    digest = pytest_shards._digest(selected)
    for shard_id, nodeid in enumerate(selected, start=1):
        shard = tmp_path / f"pytest-shard-{shard_id}"
        shard.mkdir()
        (shard / "plan.json").write_text(
            json.dumps(
                {
                    "assigned_nodeids": [nodeid],
                    "assigned_digest": pytest_shards._digest([nodeid]),
                    "collected_count": len(selected),
                    "collected_digest": digest,
                    "serial_nodeids": list(pytest_shards.SERIAL_TESTS) if shard_id == 1 else [],
                    "shard_count": 4,
                    "shard_id": shard_id,
                }
            ),
            encoding="utf-8",
        )
        (shard / "main-junit.xml").write_text('<testsuite tests="1" />', encoding="utf-8")
        if shard_id == 1:
            (shard / "cache-junit.xml").write_text('<testsuite tests="2" />', encoding="utf-8")
            (shard / "playground-junit.xml").write_text('<testsuite tests="1" />', encoding="utf-8")

    pytest_shards.verify_artifacts(tmp_path, 4)


def test_parse_durations_accumulates_per_test_timings(tmp_path: Path) -> None:
    log = tmp_path / "pytest.log"
    output = tmp_path / "durations.json"
    log.write_text(
        "  1.25s call     tests/test_a.py::test_a\n  0.75s setup    tests/test_a.py::test_a\n",
        encoding="utf-8",
    )

    pytest_shards.parse_durations([log], output)

    assert json.loads(output.read_text(encoding="utf-8")) == {"tests/test_a.py::test_a": 2.0}
