"""Freshness contract for site/src/data/curriculum-stats.json (#9754).

The committed stats must equal what the producer derives from curriculum.yaml,
and the producer's `--check` boundary must catch stale, missing and malformed
files, including a self-consistent old file that still has a valid `_total`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts import generate_curriculum_stats as gcs

pytestmark = pytest.mark.reads_content

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_curriculum_stats.py"


def _manifest(**levels: list[str]) -> dict:
    return {"levels": {level: {"modules": modules} for level, modules in levels.items()}}


@pytest.fixture
def paths(tmp_path, monkeypatch):
    """Point the producer at a throwaway manifest and output file."""
    curriculum = tmp_path / "curriculum.yaml"
    output = tmp_path / "data" / "curriculum-stats.json"
    monkeypatch.setattr(gcs, "CURRICULUM", curriculum)
    monkeypatch.setattr(gcs, "OUTPUT", output)
    return curriculum, output


def _write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(yaml.safe_dump(manifest), encoding="utf-8")


def test_build_stats_counts_modules_and_total() -> None:
    manifest = _manifest(a2=["x", "y"], bio=["p"], empty=[])
    manifest["levels"]["no_modules_key"] = {}
    manifest["levels"]["null_level"] = None

    assert gcs.build_stats(manifest) == {
        "a2": {"modules": 2},
        "bio": {"modules": 1},
        "empty": {"modules": 0},
        "no_modules_key": {"modules": 0},
        "null_level": {"modules": 0},
        "_total": 3,
    }


def test_render_stats_is_stable_two_space_json_with_trailing_newline() -> None:
    text = gcs.render_stats({"a2": {"modules": 2}, "_total": 2})

    assert text.endswith("}\n")
    assert text == '{\n  "a2": {\n    "modules": 2\n  },\n  "_total": 2\n}\n'


def test_load_stats_reads_manifest_from_disk(paths) -> None:
    curriculum, _ = paths
    _write_manifest(curriculum, _manifest(a2=["x"], b1=["y", "z"]))

    assert gcs.load_stats() == {"a2": {"modules": 1}, "b1": {"modules": 2}, "_total": 3}


def test_check_passes_for_fresh_output(paths) -> None:
    curriculum, _ = paths
    _write_manifest(curriculum, _manifest(a2=["x"], b1=["y", "z"]))
    gcs.main([])

    assert gcs.stats_drift(gcs.load_stats()) == []
    assert gcs.main(["--check"]) == 0


def test_check_detects_missing_file(paths, capsys) -> None:
    curriculum, output = paths
    _write_manifest(curriculum, _manifest(a2=["x"]))

    assert gcs.main(["--check"]) == 1
    assert "missing" in capsys.readouterr().out
    assert not output.exists(), "--check must never write"


@pytest.mark.parametrize(
    ("content", "needle"),
    [
        ("{not json", "unparseable"),
        ("[1, 2]", "unexpected shape"),
        (json.dumps({"_total": 1}), "missing key 'a2'"),
        (json.dumps({"a2": {"modules": 5}, "_total": 1}), "stale key 'a2'"),
        (json.dumps({"a2": {"modules": 1}, "_total": 9}), "stale key '_total'"),
        (json.dumps({"a2": {"modules": 1}, "old": {"modules": 1}, "_total": 1}), "unexpected key 'old'"),
        ('{"a2": {"modules": 1}, "_total": 1}', "formatting differs"),
    ],
)
def test_check_detects_bad_output(paths, capsys, content, needle) -> None:
    curriculum, output = paths
    _write_manifest(curriculum, _manifest(a2=["x"]))
    output.parent.mkdir(parents=True)
    output.write_text(content, encoding="utf-8")

    assert gcs.main(["--check"]) == 1
    printed = capsys.readouterr().out
    assert needle in printed
    assert "scripts/generate_curriculum_stats.py" in printed
    assert output.read_text(encoding="utf-8") == content, "--check must never rewrite"


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (["a", "b"], ["a", "b", "c"]),  # module added to the manifest
        (["a", "b"], ["a"]),  # module removed from the manifest
    ],
)
def test_check_detects_source_change_behind_self_consistent_output(paths, before, after) -> None:
    """An old file with an internally valid `_total` must not mask a manifest change."""
    curriculum, output = paths
    _write_manifest(curriculum, _manifest(a2=before, b1=["q"]))
    gcs.main([])
    old = json.loads(output.read_text(encoding="utf-8"))
    assert old["_total"] == sum(v["modules"] for k, v in old.items() if k != "_total")

    _write_manifest(curriculum, _manifest(a2=after, b1=["q"]))

    assert gcs.main(["--check"]) == 1
    assert gcs.main([]) == 0
    assert gcs.main(["--check"]) == 0


def test_write_creates_missing_output_directory(paths) -> None:
    curriculum, output = paths
    _write_manifest(curriculum, _manifest(a2=["x"]))

    assert gcs.main([]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == {"a2": {"modules": 1}, "_total": 1}


def test_committed_stats_match_current_manifest_for_every_key() -> None:
    """All level keys and `_total` equal the manifest-derived producer output."""
    manifest = yaml.safe_load(gcs.CURRICULUM.read_text(encoding="utf-8"))
    expected = gcs.build_stats(manifest)
    actual = json.loads(gcs.OUTPUT.read_text(encoding="utf-8"))

    assert len(expected) == len(manifest["levels"]) + 1 == 22
    assert actual == expected
    assert actual["_total"] == sum(actual[level]["modules"] for level in manifest["levels"])
    assert gcs.stats_drift(expected) == []


def test_check_cli_passes_on_committed_stats() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("OK ")


def test_help_documents_check_flag_and_exit_codes() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0
    assert "--check" in result.stdout
    assert "Exit codes:" in result.stdout
