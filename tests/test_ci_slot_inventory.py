from __future__ import annotations

from pathlib import Path

from scripts.ci import slot_inventory


def _write_workflow(directory: Path, name: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding="utf-8")


def test_inventory_expands_static_matrix_and_ignores_non_pr_workflows(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "pr.yml",
        """on: pull_request
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu, macos]
        python: ['3.11', '3.12']
        exclude:
          - os: macos
            python: '3.11'
        include:
          - os: windows
            python: '3.12'
    runs-on: ${{ matrix.os }}
""",
    )
    _write_workflow(
        tmp_path,
        "push.yml",
        """on: push
jobs:
  ignored:
    runs-on: ubuntu-latest
""",
    )

    report = slot_inventory.inventory_report(tmp_path)

    assert report["total"] == 4
    assert report["workflows"] == [{"workflow": str(tmp_path / "pr.yml"), "jobs": {"test": 4}, "total": 4}]


def test_inventory_uses_named_pytest_shard_ceiling_for_runtime_matrix(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        """on: [pull_request, merge_group]
jobs:
  python:
    strategy:
      matrix:
        shard: ${{ fromJSON(inputs.shards) }}
    runs-on: ubuntu-latest
""",
    )

    report = slot_inventory.inventory_report(tmp_path)

    assert report["total"] == slot_inventory.PYTEST_SHARD_CEILING


def test_check_fails_when_dummy_job_expands_past_configured_ceiling(tmp_path: Path, capsys) -> None:
    _write_workflow(
        tmp_path,
        "pr.yml",
        """on: pull_request
jobs:
  baseline:
    strategy:
      matrix:
        lane: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    runs-on: ubuntu-latest
  dummy:
    strategy:
      matrix:
        lane: [1, 2, 3]
    runs-on: ubuntu-latest
""",
    )

    result = slot_inventory.main(["--workflow-dir", str(tmp_path), "--check", "--json"])

    assert result == 1
    assert '"pass": false' in capsys.readouterr().out


def test_static_pytest_shards_cannot_exceed_named_ceiling(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        """on: pull_request
jobs:
  python:
    strategy:
      matrix:
        shard: [1, 2, 3, 4, 5]
    runs-on: ubuntu-latest
""",
    )

    try:
        slot_inventory.inventory_report(tmp_path)
    except ValueError as exc:
        assert "PYTEST_SHARD_CEILING" in str(exc)
    else:
        raise AssertionError("expected an over-ceiling pytest shard matrix to fail")
