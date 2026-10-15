"""The dispatch fixture clone is built once per process and copied per test (#9065)."""

import subprocess
from pathlib import Path

from scripts import delegate
from tests.helpers import dispatch_checkout

_GIT_IDENTITY = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *_GIT_IDENTITY, "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        env=delegate._sanitized_git_env(),
    ).stdout.strip()


def _isolated(monkeypatch, tmp_path: Path, name: str) -> Path:
    with monkeypatch.context() as scoped:
        return dispatch_checkout.isolate_dispatch_repo(scoped, tmp_path / name, delegate)


def test_template_is_built_once_and_each_copy_is_isolated(monkeypatch, tmp_path):
    builds: list[Path] = []
    original_build = dispatch_checkout._build_template

    def counting_build(real_run, env, source, destination):
        builds.append(destination)
        return original_build(real_run, env, source, destination)

    monkeypatch.setattr(dispatch_checkout, "_build_template", counting_build)
    monkeypatch.setattr(dispatch_checkout, "_TEMPLATES", {})

    first = _isolated(monkeypatch, tmp_path, "one")
    second = _isolated(monkeypatch, tmp_path, "two")

    assert len(builds) == 1, "the sparse clone must be built once, not once per test"
    assert first != second
    assert first.parent != second.parent

    template = next(iter(dispatch_checkout._TEMPLATES.values()))[0]
    template_head = _git(template, "rev-parse", "HEAD")
    assert _git(first, "rev-parse", "HEAD") == _git(second, "rev-parse", "HEAD") == template_head
    assert _git(first, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert _git(first, "remote", "get-url", "origin").endswith("learn-ukrainian.github.io.git")
    assert _git(first, "sparse-checkout", "list").splitlines() == list(dispatch_checkout._SPARSE_PATTERNS)

    # Mutate the first copy: new file, commit, branch, tag, config, worktree.
    marker = Path("scripts/config/fixture-marker.txt")  # inside the sparse patterns
    (first / marker).write_text("only in the first copy\n", encoding="utf-8")
    _git(first, "add", str(marker))
    _git(first, "commit", "--quiet", "-m", "mutate first copy")
    _git(first, "branch", "first-only")
    _git(first, "tag", "first-tag")
    _git(first, "config", "fixture.marker", "first")
    _git(first, "worktree", "add", "--no-checkout", "--quiet", str(tmp_path / "wt"), "-b", "wt-branch")
    mutated_head = _git(first, "rev-parse", "HEAD")
    assert mutated_head != template_head

    for untouched in (second, template):
        assert not (untouched / marker).exists()
        assert _git(untouched, "rev-parse", "HEAD") == template_head
        assert _git(untouched, "branch", "--list", "first-only", "wt-branch") == ""
        assert _git(untouched, "tag", "--list", "first-tag") == ""
        assert (
            subprocess.run(
                ["git", "-C", str(untouched), "config", "--get", "fixture.marker"],
                capture_output=True,
                text=True,
                timeout=30,
                env=delegate._sanitized_git_env(),
            ).stdout
            == ""
        )
        assert _git(untouched, "worktree", "list", "--porcelain").count("worktree ") == 1

    # A later copy is cut from the pristine template, not from the mutated one.
    third = _isolated(monkeypatch, tmp_path, "three")
    assert len(builds) == 1
    assert _git(third, "rev-parse", "HEAD") == template_head
    assert not (third / marker).exists()


def test_copy_wires_delegate_to_its_own_checkout(monkeypatch, tmp_path):
    primary = dispatch_checkout.isolate_dispatch_repo(monkeypatch, tmp_path, delegate)

    assert primary == tmp_path / "dispatch-source"
    assert primary == delegate._REPO_ROOT
    assert Path.cwd() == primary
    assert (primary / "docs").is_dir()
    assert (primary / "site/src").is_dir()
    assert (primary / "scripts/delegate.py").is_file()
    assert not (primary / "curriculum").exists()
    assert delegate._resolve_worktree_base_sha() == _git(primary, "rev-parse", "HEAD")
