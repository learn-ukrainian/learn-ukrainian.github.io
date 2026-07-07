from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import freeze_benchmark, llm_reviewer, qg_bakeoff, qg_workflow

MANIFEST_PATH = freeze_benchmark.DEFAULT_MANIFEST_PATH


def _manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        pytest.skip("benchmark v1 MANIFEST.json is absent; freeze guard is inactive")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _tree_path(relative_path: str) -> Path:
    return freeze_benchmark.PROJECT_ROOT / relative_path


def test_heldout_hashes_include_only_non_hidden_json_files(tmp_path: Path) -> None:
    public_hash_input = tmp_path / "heldout-a.json"
    public_hash_input.write_text('{"slug": "private-a"}\n', encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not a fixture\n", encoding="utf-8")
    (tmp_path / ".DS_Store").write_text("mac metadata\n", encoding="utf-8")
    (tmp_path / ".hidden.json").write_text('{"slug": "hidden"}\n', encoding="utf-8")

    heldout = freeze_benchmark._heldout_fixtures(tmp_path)

    assert heldout == {
        "count": 1,
        "sha256": [freeze_benchmark._sha256_file(public_hash_input)],
    }


def test_external_paths_are_rendered_posix(tmp_path: Path) -> None:
    external = tmp_path / "outside" / "SCORECARD.md"
    external.parent.mkdir()
    external.write_text("# scorecard\n", encoding="utf-8")

    reference = freeze_benchmark._reference_result(external)

    assert reference is not None
    assert "\\" not in reference["path"]
    assert reference["path"].endswith("/outside/SCORECARD.md")


def test_public_fixture_hashes_match_frozen_manifest() -> None:
    manifest = _manifest()
    files = manifest["fixtures"]["public"]["files"]
    assert isinstance(files, list)
    for row in files:
        path = _tree_path(row["path"])
        assert path.exists(), f"{row['path']}: bump benchmark version, never edit v1"
        assert (
            freeze_benchmark._sha256_file(path) == row["sha256"]
        ), f"{row['path']}: drift detected; bump benchmark version, never edit v1"


def test_reference_scorecard_hash_matches_frozen_manifest() -> None:
    manifest = _manifest()
    reference = manifest.get("reference_result")
    assert isinstance(reference, dict), "reference_result must be frozen in benchmark v1"
    path = _tree_path(str(reference["path"]))
    assert path.exists(), f"{reference['path']}: frozen reference scorecard missing"
    assert freeze_benchmark._sha256_file(path) == reference["sha256"], (
        f"{reference['path']}: frozen reference scorecard drift; bump benchmark version, never edit v1"
    )


def test_frozen_diagnostic_values_match_current_code() -> None:
    manifest = _manifest()
    assert manifest["DOMAIN_BY_SLUG"] == dict(qg_bakeoff.DOMAIN_BY_SLUG)
    assert manifest["scorer"]["constants"] == freeze_benchmark._constants_snapshot()

    for relative_path, expected_sha in manifest["scorer"]["files"].items():
        assert freeze_benchmark._sha256_file(_tree_path(relative_path)) == expected_sha

    prompt_template = llm_reviewer.load_reviewer_prompt_template()
    gates = manifest["gates"]
    assert gates["gate_version"] == qg_workflow.DEFAULT_GATE_VERSION
    assert gates["reviewer_prompt_sha256"] == freeze_benchmark._sha256_text(prompt_template)
    assert gates["taxonomy_slice_sha256"] == freeze_benchmark._sha256_text(
        qg_bakeoff._reviewer_verdict_taxonomy()
    )
