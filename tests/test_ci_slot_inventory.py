from __future__ import annotations

from pathlib import Path

import pytest

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


def test_inventory_counts_the_static_pytest_shard_list(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        """on: [pull_request, merge_group]
jobs:
  pytest:
    strategy:
      matrix:
        shard: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    runs-on: ubuntu-latest
  ci-gate:
    runs-on: ubuntu-latest
""",
    )

    report = slot_inventory.inventory_report(tmp_path)

    assert report["total"] == 11


def test_check_fails_when_total_exceeds_ceiling(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setattr(slot_inventory, "CI_SLOT_CEILING", 31)
    _write_workflow(
        tmp_path,
        "ci.yml",
        """on: pull_request
jobs:
  pytest:
    strategy:
      matrix:
        shard: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    runs-on: ubuntu-latest
  baseline:
    strategy:
      matrix:
        lane: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    runs-on: ubuntu-latest
""",
    )

    result = slot_inventory.main(["--workflow-dir", str(tmp_path), "--check", "--json"])

    assert result == 1
    assert '"pass": false' in capsys.readouterr().out


def test_runtime_matrix_fails_closed(tmp_path: Path) -> None:
    """A matrix computed at run time cannot be counted, so the inventory refuses it."""
    _write_workflow(
        tmp_path,
        "ci.yml",
        """on: pull_request
jobs:
  pytest:
    strategy:
      matrix:
        shard: ${{ fromJSON(needs.plan.outputs.shards) }}
    runs-on: ubuntu-latest
""",
    )

    with pytest.raises(ValueError, match="static YAML list"):
        slot_inventory.inventory_report(tmp_path)


def test_repository_workflows_fit_the_ceiling() -> None:
    report = slot_inventory.inventory_report(Path(__file__).resolve().parents[1] / ".github/workflows")

    assert report["pass"], report
