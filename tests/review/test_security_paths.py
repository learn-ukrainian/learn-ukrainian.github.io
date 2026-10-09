"""#9125: literal changed paths and an additive, tracked security inventory."""

from __future__ import annotations

import json
import subprocess
from fnmatch import fnmatchcase
from pathlib import Path

import pytest

from scripts.common.git_context import sanitized_git_env
from scripts.review.closeout_cli import main
from scripts.review.security_paths import (
    SECURITY_SENSITIVE_PATHS,
    effective_review_risk,
    git_changed_paths,
    is_security_sensitive_change,
)
from scripts.review.target_resolution import TargetResolutionError

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def isolated_live_snapshot(monkeypatch):
    monkeypatch.setattr("scripts.fleet.credit_lane.read_routing_budget", lambda **_: None)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, env=sanitized_git_env(), timeout=30)


@pytest.mark.parametrize("pattern", SECURITY_SENSITIVE_PATHS)
def test_every_security_glob_matches_a_tracked_file(pattern):
    tracked = _git(REPO_ROOT, "ls-files", "-z").split("\0")
    witnesses = [path for path in tracked if fnmatchcase(path, pattern)]
    assert witnesses, f"security coverage lost: {pattern} matches no tracked file"
    assert is_security_sensitive_change((witnesses[0],))


@pytest.mark.parametrize(
    "paths,owned,expected",
    [
        ((), (), False),
        (("docs/readme.md", "site/src/app.ts"), (), False),
        (("docs/readme.md", "scripts/ocr/_credentials.py"), ("site/src/app.ts",), True),
        (("site/src/app.ts",), ("scripts/ocr/_credentials.py",), True),
        (("scripts/ocr/_credentials.py",), ("!scripts/ocr/_credentials.py",), True),
        (("./scripts/delegate.py",), (), True),
        ((), ("./scripts/delegate.py",), True),
        ((), ("scripts/agent_runtime",), True),
        ((), ("scripts/agent_runtime/",), True),
        ((), ("scripts/hooks",), True),
        ((), ("scripts",), True),
        ((), ("scripts/",), True),
        ((), ("././scripts/",), True),
        ((), ("agents_extensions/shared",), True),
        ((), ("scripts/lib/nested",), True),
        ((), ("scripts/launchers-other",), False),
        ((), ("scripts/reviewer",), False),
        ((), ("docs/",), False),
    ],
)
def test_classifier_and_risk_are_additive(paths, owned, expected):
    assert is_security_sensitive_change(paths, owned) is expected
    for risk in ("low", "medium", "high", "critical"):
        assert effective_review_risk(risk, paths, owned) == ("critical" if expected else risk)


@pytest.mark.parametrize("profile", ["code", "infra", "ukrainian"])
def test_security_floor_is_scoped_to_code_and_infra(profile):
    assert effective_review_risk("low", ("scripts/delegate.py",), profile=profile) == (
        "low" if profile == "ukrainian" else "critical"
    )
    assert effective_review_risk("medium", (), ("scripts/agent_runtime",), profile=profile) == (
        "medium" if profile == "ukrainian" else "critical"
    )


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "git-probe"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    return repo


@pytest.mark.parametrize("operation", ["rename-out", "rename-in", "delete", "newline-rename"])
@pytest.mark.parametrize("mode", ["commit", "local"])
def test_git_and_cli_classify_both_rename_names_and_deletions(repo, capsys, operation, mode):
    sensitive = "scripts/ocr/_credentials.py"
    ordinary = "ordinary/file.py" if operation != "newline-rename" else "ordinary/file\nname.py"
    old, new = (ordinary, sensitive) if operation == "rename-in" else (sensitive, ordinary)
    old_path = repo / old
    old_path.parent.mkdir(parents=True)
    old_path.write_text("value = 1\n" * 5, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    if operation == "delete":
        _git(repo, "rm", old)
        expected = {old}
    else:
        (repo / new).parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "mv", old, new)
        expected = {old, new}
    if mode == "commit":
        # A committed target is attributed by its X-Agent trailer (#9739), here the --author-model below.
        _git(repo, "commit", "-qm", "change\n\nX-Agent: codex/gpt-6.1-sol")
        head = _git(repo, "rev-parse", "HEAD").strip()
    else:
        head = None
    assert set(git_changed_paths(repo, base, head)) == expected
    assert is_security_sensitive_change(git_changed_paths(repo, base, head))

    state = repo.parent / "review.json"
    target_args = ["target", "--mode", mode, "--repo-root", str(repo)]
    if mode == "commit":
        target_args += ["--commit", head]
    assert main(["--state-file", str(state), *target_args]) == 0
    capsys.readouterr()
    # The probe repository has no GitHub origin, so name the repository its task records would carry.
    resolve_args = ["resolve-reviewer", "--author-model", "gpt-6.1-sol", "--risk", "low"]
    resolve_args += ["--repository", "learn-ukrainian/learn-ukrainian.github.io"]
    assert main(["--state-file", str(state), *resolve_args]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["resolved_risk"] == "critical"
    assert payload["selected"]["concrete_model"] == "claude-opus-5-5"


def test_git_collection_failure_is_a_refusal(repo):
    with pytest.raises(TargetResolutionError, match="changed-path collection failed"):
        git_changed_paths(repo, "f" * 40, "e" * 40)


@pytest.mark.parametrize("base,head", [("HEAD", None), ("f" * 39, "e" * 40), ("f" * 40, "--option"), (None, "e" * 40)])
def test_invalid_sha_refuses_before_git(repo, monkeypatch, base, head):
    def unexpected(*_args):
        pytest.fail("invalid state-file endpoints must never reach git")

    monkeypatch.setattr("scripts.review.security_paths._run_git", unexpected)
    with pytest.raises(TargetResolutionError, match="target_sha_invalid"):
        git_changed_paths(repo, base, head)


@pytest.mark.parametrize("error", [OSError("unavailable"), subprocess.TimeoutExpired("git", 30)])
def test_git_collection_launch_or_timeout_is_a_refusal(repo, monkeypatch, error):
    from scripts.review import security_paths

    def fail(*_args):
        raise error

    monkeypatch.setattr(security_paths, "_run_git", fail)
    with pytest.raises(TargetResolutionError, match="changed-path collection failed"):
        git_changed_paths(repo, "f" * 40, "e" * 40)


def test_cli_untracked_security_path_is_preserved(repo, capsys):
    (repo / "ordinary.py").write_text("value = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    path = repo / "scripts/ocr/_credentials.py"
    path.parent.mkdir(parents=True)
    path.write_text("value = 2\n", encoding="utf-8")
    state = repo.parent / "review.json"
    assert main(["--state-file", str(state), "target", "--mode", "local", "--repo-root", str(repo)]) == 0
    capsys.readouterr()
    assert main(["--state-file", str(state), "resolve-reviewer", "--author-model", "gpt-6.1-sol", "--risk", "low"]) == 0
    assert json.loads(capsys.readouterr().out)["resolved_risk"] == "critical"


def test_cli_refuses_unreadable_frozen_target(repo, capsys):
    state = repo.parent / "review.json"
    state.write_text(
        json.dumps(
            {
                "target": {
                    "mode": "commit",
                    "base_sha": "f" * 40,
                    "head_sha": "e" * 40,
                    "changed_paths": ["ordinary.py"],
                    "non_test_loc": 1,
                    "clean_tree": False,
                    "description": "missing endpoints",
                },
                "target_args": {"repo_root": str(repo)},
            }
        ),
        encoding="utf-8",
    )
    assert main(["--state-file", str(state), "resolve-reviewer", "--author-model", "gpt-6.1-sol"]) == 1
    assert "changed-path collection failed" in capsys.readouterr().err
