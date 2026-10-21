from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.audit import certify_module

pytestmark = pytest.mark.reads_content


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=env,
        text=True, timeout=30,
    )


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


def test_vocabulary_presence_guard_fails_clearly_for_missing_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = certify_module.ModuleTarget(
        lang_pair="l2-uk-en",
        level="a1",
        slug="does-not-exist",
        local_num=999,
    )

    rc = certify_module.run_vocabulary_presence_guard(target)

    captured = capsys.readouterr()
    assert rc == 1
    assert "no vocabulary source found for a1/does-not-exist" in captured.out
    assert "curriculum/l2-uk-en/a1/does-not-exist/vocabulary.yaml" in captured.out


def test_forbidden_diff_reason_flags_generated_artifacts_and_protected_configs() -> None:
    cases = {
        ".python-version": "protected repo config",
        ".yamllint": "protected repo config",
        ".markdownlint.json": "protected repo config",
        "curriculum/l2-uk-en/a2/status/greetings.json": "generated status JSON",
        "curriculum/l2-uk-en/a2/audit/greetings-review.md": "generated audit review",
        "curriculum/l2-uk-en/a2/review/greetings-review.md": "generated review file",
        "curriculum/l2-uk-en/a2/greetings/vocabulary.yaml.errors.txt": "validator sidecar",
        "docs/A2-STATUS.md": "generated level status",
        "data/telemetry/module-builds.sqlite": "local telemetry",
    }

    for rel_path, expected in cases.items():
        assert expected in (certify_module.forbidden_diff_reason(rel_path) or "")

    assert certify_module.forbidden_diff_reason("curriculum/l2-uk-en/a2/greetings/module.md") is None


def test_changed_or_untracked_paths_reports_tracked_and_untracked(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "codex@example.test")
    _git(repo, "config", "user.name", "Codex")
    tracked = repo / "tracked\tfile.txt"
    tracked.write_text("old\n", encoding="utf-8")
    _git(repo, "add", "tracked\tfile.txt")
    _git(repo, "commit", "-m", "init")
    tracked.write_text("new\n", encoding="utf-8")
    (repo / "untracked space.txt").write_text("new\n", encoding="utf-8")

    paths = certify_module.changed_or_untracked_paths(repo)

    assert paths == ("tracked\tfile.txt", "untracked space.txt")
