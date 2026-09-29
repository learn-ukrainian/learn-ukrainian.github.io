"""The #8872 area escape replay counts selections, skips and escapes."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ci.area_replay import main, replay

_ATLAS_TEST = "tests/test_atlas_db.py"


def _write_test(repo: Path, path: str, text: str = "def test_one(): pass\n") -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text, encoding="utf-8")


def test_replay_reports_escape_only_when_failed_area_test_is_skipped(tmp_path: Path) -> None:
    _write_test(tmp_path, _ATLAS_TEST)
    records = [
        {"id": 1, "paths": ["scripts/unmapped_backend.py"], "failed": [_ATLAS_TEST]},
        {"id": 2, "paths": ["scripts/atlas/atlas_db.py"], "failed": [_ATLAS_TEST]},
        {"id": 3, "paths": ["scripts/unmapped_backend.py"], "failed": [_ATLAS_TEST], "labels": ["full-ci"]},
        {"id": 4, "paths": [".github/workflows/ci.yml"], "failed": [_ATLAS_TEST]},
        {"id": 5, "paths": ["scripts/unmapped_backend.py"], "failed": ["tests/test_unrelated.py"]},
    ]
    result = replay(records, repo=tmp_path)
    assert result["runs"] == 5
    assert result["areas"]["atlas"] == {"selected": 3, "skipped": 2}
    assert [(escape["id"], escape["test"]) for escape in result["escapes"]] == [(1, _ATLAS_TEST)]


def test_replay_keeps_repo_wide_failures(tmp_path: Path) -> None:
    _write_test(tmp_path, _ATLAS_TEST, "import pytest\npytestmark = pytest.mark.repo_wide\n")
    result = replay([{"id": 1, "paths": ["scripts/unmapped_backend.py"], "failed": [_ATLAS_TEST]}], repo=tmp_path)
    assert result["escapes"] == []


def test_cli_exits_nonzero_on_escape(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_test(tmp_path, _ATLAS_TEST)
    records = tmp_path / "records.jsonl"
    records.write_text(
        json.dumps({"id": 1, "paths": ["scripts/atlas/atlas_db.py"], "failed": [_ATLAS_TEST]}) + "\n", encoding="utf-8"
    )
    assert main([str(records)]) == 0
    assert json.loads(capsys.readouterr().out)["escapes"] == []
    records.write_text(
        json.dumps({"id": 2, "paths": ["scripts/unmapped_backend.py"], "failed": [_ATLAS_TEST]}) + "\n\n",
        encoding="utf-8",
    )
    assert main([str(records)]) == 1
    assert json.loads(capsys.readouterr().out)["escapes"][0]["id"] == 2
