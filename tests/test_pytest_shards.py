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


def test_run_nodeids_rejects_empty_file(tmp_path: Path) -> None:
    empty = tmp_path / "nodeids.txt"
    empty.write_text("", encoding="utf-8")
    try:
        pytest_shards.run_nodeids(empty, ["-q"])
    except RuntimeError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("empty node-id file must fail closed")


def test_run_nodeids_passes_nodeids_to_pytest_main(tmp_path: Path, monkeypatch) -> None:
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text("tests/test_a.py::test_a\ntests/test_b.py::test_b\n", encoding="utf-8")
    captured: list[list[str]] = []

    def fake_main(args):
        captured.append(list(args))
        return 7

    import pytest as real_pytest

    monkeypatch.setattr(real_pytest, "main", fake_main)
    rc = pytest_shards.run_nodeids(nodeids, ["--", "-q", "-n", "auto"])
    assert rc == 7
    assert captured == [["-q", "-n", "auto", "tests/test_a.py::test_a", "tests/test_b.py::test_b"]]


def test_write_plan_rejects_empty_shard(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(pytest_shards, "collect_nodeids", lambda args=(): ["only-one"])
    monkeypatch.setattr(
        pytest_shards,
        "assign_shards",
        lambda nodeids, shard_count, durations: [[], ["only-one"], [], []],
    )
    try:
        pytest_shards.write_plan(
            shard_id=1,
            shard_count=4,
            durations_path=None,
            output=tmp_path / "plan.json",
            args_output=tmp_path / "nodeids.txt",
        )
    except RuntimeError as error:
        assert "zero assigned" in str(error)
    else:
        raise AssertionError("empty shard must fail at plan time")


def test_write_plan_default_ignores_divergent_duration_caches(
    tmp_path: Path, monkeypatch
) -> None:
    """Equal-weight default: two workers with different duration files still match."""
    nodeids = [f"tests/test_{n}.py::t" for n in range(12)]
    monkeypatch.setattr(pytest_shards, "collect_nodeids", lambda args=(): list(nodeids))

    hot = tmp_path / "hot.json"
    cold = tmp_path / "cold.json"
    hot.write_text(
        json.dumps({nodeids[0]: 99.0, nodeids[1]: 0.1}), encoding="utf-8"
    )
    cold.write_text(json.dumps({nodeids[5]: 50.0}), encoding="utf-8")

    plans = []
    for idx, dur_path in enumerate((hot, cold), start=1):
        out = tmp_path / f"plan-{idx}.json"
        args_out = tmp_path / f"ids-{idx}.txt"
        pytest_shards.write_plan(
            shard_id=1,
            shard_count=4,
            durations_path=dur_path,
            output=out,
            args_output=args_out,
            use_lpt_durations=False,
        )
        plans.append(json.loads(out.read_text(encoding="utf-8")))

    assert plans[0]["partition_mode"] == "equal-weight"
    assert plans[0]["assigned_digest"] == plans[1]["assigned_digest"]
    assert plans[0]["assigned_nodeids"] == plans[1]["assigned_nodeids"]


def test_write_plan_lpt_opt_in_uses_durations(tmp_path: Path, monkeypatch) -> None:
    nodeids = [f"tests/test_{n}.py::t" for n in range(8)]
    monkeypatch.setattr(pytest_shards, "collect_nodeids", lambda args=(): list(nodeids))
    dur = tmp_path / "d.json"
    # One very heavy test changes LPT packing vs equal-weight across shards.
    dur.write_text(
        json.dumps({nid: (100.0 if i == 0 else 1.0) for i, nid in enumerate(nodeids)}),
        encoding="utf-8",
    )
    equal_sets: list[set[str]] = []
    lpt_sets: list[set[str]] = []
    for shard_id in range(1, 5):
        eq_out = tmp_path / f"eq-{shard_id}.json"
        lpt_out = tmp_path / f"lpt-{shard_id}.json"
        pytest_shards.write_plan(
            shard_id=shard_id,
            shard_count=4,
            durations_path=dur,
            output=eq_out,
            args_output=tmp_path / f"eq-{shard_id}.txt",
            use_lpt_durations=False,
        )
        pytest_shards.write_plan(
            shard_id=shard_id,
            shard_count=4,
            durations_path=dur,
            output=lpt_out,
            args_output=tmp_path / f"lpt-{shard_id}.txt",
            use_lpt_durations=True,
        )
        eq = json.loads(eq_out.read_text(encoding="utf-8"))
        lpt = json.loads(lpt_out.read_text(encoding="utf-8"))
        assert eq["partition_mode"] == "equal-weight"
        assert lpt["partition_mode"] == "lpt-durations"
        equal_sets.append(set(eq["assigned_nodeids"]))
        lpt_sets.append(set(lpt["assigned_nodeids"]))
    assert equal_sets != lpt_sets
