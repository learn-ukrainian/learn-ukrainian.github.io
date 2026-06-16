from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.audit import certify_module


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )


def test_qg_artifacts_match_only_known_direct_files(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    expected = {
        "llm_qg.json": "{}\n",
        "python_qg.json": "{}\n",
        "llm-qg-naturalness-prompt.md": "prompt\n",
        "llm-qg-tone-response.raw.md": "raw\n",
    }
    for name, content in expected.items():
        (module_dir / name).write_text(content, encoding="utf-8")
    (module_dir / "llm-qg-notes.txt").write_text("keep\n", encoding="utf-8")
    nested = module_dir / "nested"
    nested.mkdir()
    (nested / "llm_qg.json").write_text("{}\n", encoding="utf-8")

    artifacts = certify_module.qg_artifacts(module_dir)

    assert {path.name for path in artifacts} == set(expected)


def test_inspect_qg_artifacts_flags_empty_and_malformed_outputs(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    malformed = module_dir / "llm_qg.json"
    malformed.write_text("{not-json", encoding="utf-8")
    empty_response = module_dir / "llm-qg-tone-response.raw.md"
    empty_response.write_text(" \n\t", encoding="utf-8")
    valid_prompt = module_dir / "llm-qg-tone-prompt.md"
    valid_prompt.write_text("prompt\n", encoding="utf-8")

    findings = certify_module.inspect_qg_artifacts(
        (malformed, empty_response, valid_prompt)
    )

    assert {(finding.code, finding.path.name) for finding in findings} == {
        ("malformed-qg-json", "llm_qg.json"),
        ("empty-qg-response", "llm-qg-tone-response.raw.md"),
    }


def test_clean_qg_artifacts_removes_untracked_known_files_only(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    qg_json = module_dir / "llm_qg.json"
    qg_json.write_text("{}\n", encoding="utf-8")
    raw_response = module_dir / "llm-qg-tone-response.raw.md"
    raw_response.write_text("raw\n", encoding="utf-8")
    keep = module_dir / "llm-qg-notes.txt"
    keep.write_text("keep\n", encoding="utf-8")

    result = certify_module.clean_qg_artifacts(module_dir, repo_root=tmp_path)

    assert {path.name for path in result.removed} == {
        "llm_qg.json",
        "llm-qg-tone-response.raw.md",
    }
    assert result.refused_tracked == ()
    assert not qg_json.exists()
    assert not raw_response.exists()
    assert keep.read_text(encoding="utf-8") == "keep\n"


def test_clean_qg_artifacts_refuses_tracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    module_dir = repo / "curriculum" / "l2-uk-en" / "a1" / "demo"
    module_dir.mkdir(parents=True)
    tracked = module_dir / "llm_qg.json"
    tracked.write_text("{}\n", encoding="utf-8")
    untracked = module_dir / "llm-qg-tone-response.raw.md"
    untracked.write_text("raw\n", encoding="utf-8")
    _git(repo, "add", str(tracked.relative_to(repo)))

    result = certify_module.clean_qg_artifacts(module_dir, repo_root=repo)

    assert {path.name for path in result.refused_tracked} == {"llm_qg.json"}
    assert {path.name for path in result.removed} == {"llm-qg-tone-response.raw.md"}
    assert tracked.exists()
    assert not untracked.exists()


def test_build_checks_use_project_venv_python() -> None:
    target = certify_module.ModuleTarget(
        lang_pair="l2-uk-en",
        level="a1",
        slug="my-family",
        local_num=6,
    )

    checks = certify_module.build_checks(target, site_build=False, install_site_deps=False)
    python_commands = [check.command for check in checks if check.command[0].endswith("/python")]

    assert python_commands
    assert all(command[0] == str(certify_module.VENV_PYTHON) for command in python_commands)


def test_parse_target_accepts_slug_and_module_number() -> None:
    modules = [
        SimpleNamespace(slug="hello", local_num=1, numbered_slug="01-hello"),
        SimpleNamespace(slug="my-family", local_num=6, numbered_slug="06-my-family"),
    ]
    with (
        patch("scripts.audit.certify_module.get_modules_for_level", return_value=modules),
        patch("scripts.audit.certify_module.get_module_by_number", return_value=modules[1]),
    ):
        by_slug = certify_module.parse_target(["a1/my-family"])
        by_number = certify_module.parse_target(["l2-uk-en", "a1", "6"])

    assert by_slug.slug == "my-family"
    assert by_slug.local_num == 6
    assert by_number.slug == "my-family"
    assert by_number.local_num == 6
