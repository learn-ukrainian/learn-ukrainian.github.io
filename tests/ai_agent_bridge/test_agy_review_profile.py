"""Gemini review requests require an explicit profile (operator 2026-09-25)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge._agy import gemini_review_profile_error
from scripts.ai_agent_bridge._channels_cli import _gemini_review_request_error
from scripts.ai_agent_bridge._cli import _handle_acp_compat
from scripts.audit import llm_reviewer_dispatch


def test_missing_profile_names_the_flag() -> None:
    message = gemini_review_profile_error(None)
    assert message is not None
    assert "--review-profile" in message
    assert "ukrainian" in message


def test_code_profile_cites_the_operator_rule() -> None:
    message = gemini_review_profile_error("code")
    assert message is not None
    assert "gemini_code_review_forbidden" in message
    assert "Gemini reviews Ukrainian only, never code" in message


def test_ukrainian_profile_is_allowed() -> None:
    assert gemini_review_profile_error("ukrainian") is None


def test_ask_agy_review_without_profile_is_refused() -> None:
    args = SimpleNamespace(
        content="review this diff",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile=None,
        background=False,
    )
    with pytest.raises(SystemExit, match="--review-profile"):
        _handle_acp_compat(args, "agy")


def test_ask_agy_code_profile_is_refused() -> None:
    args = SimpleNamespace(
        content="review this diff",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile="code",
        background=False,
    )
    with pytest.raises(SystemExit, match="Gemini reviews Ukrainian only, never code"):
        _handle_acp_compat(args, "agy")


def test_ask_agy_ukrainian_profile_reaches_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_dispatch(target: str, content: str, **kwargs: object) -> None:
        seen["target"] = target
        seen["content"] = content
        seen["kwargs"] = kwargs

    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._dispatch_headless_review",
        fake_dispatch,
    )
    args = SimpleNamespace(
        content="перевір наголос",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy-uk",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile="ukrainian",
        background=False,
        effort=None,
        output_path=None,
        stdout_only=False,
        no_timeout=False,
    )
    _handle_acp_compat(args, "agy")
    assert seen["target"] == "agy"
    assert seen["content"] == "перевір наголос"


def test_post_reviews_to_agy_requires_a_profile() -> None:
    missing = _gemini_review_request_error(
        channel="reviews",
        agents=["agy"],
        review=False,
        profile=None,
    )
    assert missing is not None
    assert "--review-profile" in missing

    refused = _gemini_review_request_error(
        channel="reviews",
        agents=["agy"],
        review=False,
        profile="code",
    )
    assert refused is not None
    assert "gemini_code_review_forbidden" in refused

    assert (
        _gemini_review_request_error(
            channel="reviews",
            agents=["agy"],
            review=False,
            profile="ukrainian",
        )
        is None
    )


def test_discuss_with_agy_requires_a_profile() -> None:
    missing = _gemini_review_request_error(
        channel="architecture",
        agents=["claude", "agy"],
        review=False,
        profile=None,
        force=True,
    )
    assert missing is not None
    assert "--review-profile" in missing

    assert (
        _gemini_review_request_error(
            channel="architecture",
            agents=["claude", "agy"],
            review=False,
            profile="ukrainian",
            force=True,
        )
        is None
    )


def test_ukrainian_content_caller_passes_the_profile() -> None:
    command = llm_reviewer_dispatch.FRONTIER_FACTUAL_ROUTE.bridge_command
    assert command[:1] == ("ask-agy",)
    assert "--review" in command
    assert command[command.index("--review-profile") + 1] == "ukrainian"


_CONTENT_PATH = "curriculum/l2-uk-en/a1/hello.md"
_CODE_PATH = "scripts/delegate.py"
_REMOTE_SHA = "a" * 40


def _branch_refspec(name: str) -> str:
    return f"+refs/heads/{name}:refs/remotes/origin/{name}"


def _fake_branch_diff(name: str, diff_stdout: str, *, fail: str | None = None):
    """Script the check-ref, exact fetch, rev-parse, and diff the gate runs."""

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "check-ref-format"]:
            assert command == ["git", "check-ref-format", "--branch", name]
            code = 1 if fail == "check-ref-format" else 0
            return subprocess.CompletedProcess(
                command,
                code,
                stdout="" if code else f"{name}\n",
                stderr="invalid ref" if code else "",
            )
        if command[:2] == ["git", "fetch"]:
            assert command == ["git", "fetch", "origin", _branch_refspec(name)]
            code = 1 if fail == "fetch" else 0
            return subprocess.CompletedProcess(command, code, stderr="fetch failed" if code else "")
        if command[:3] == ["git", "rev-parse", "--verify"]:
            assert command == ["git", "rev-parse", "--verify", f"refs/remotes/origin/{name}"]
            code = 1 if fail == "rev-parse" else 0
            stdout = "" if code else f"{_REMOTE_SHA}\n"
            return subprocess.CompletedProcess(command, code, stdout=stdout, stderr="missing" if code else "")
        assert command == ["git", "diff", "--name-only", f"origin/main...{_REMOTE_SHA}"]
        code = 1 if fail == "diff" else 0
        return subprocess.CompletedProcess(
            command, code, stdout="" if code else diff_stdout, stderr="diff failed" if code else ""
        )

    return fake_run


def _review_args(**overrides: object) -> SimpleNamespace:
    base = dict(
        content="перевір текст",
        data=None,
        to_model=None,
        model=None,
        task_id="review-agy-diff",
        review=True,
        type="query",
        pr=None,
        branch=None,
        review_profile="ukrainian",
        background=False,
        effort=None,
        output_path=None,
        stdout_only=False,
        no_timeout=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_content_only_pr_reaches_gemini_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_dispatch(target: str, content: str, **kwargs: object) -> None:
        seen["target"] = target
        seen["kwargs"] = kwargs

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("content-branch", "a" * 40),
    )

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:3] == ["gh", "api", "--paginate"]:
            assert command[3:] == [
                "repos/{owner}/{repo}/pulls/77/files",
                "--jq",
                ".[].filename",
            ]
            return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n")
        assert command == [
            "gh",
            "api",
            "repos/{owner}/{repo}/pulls/77",
            "--jq",
            ".changed_files",
        ]
        return subprocess.CompletedProcess(command, 0, stdout="1\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    _handle_acp_compat(_review_args(pr=77), "agy")
    assert seen["target"] == "agy"
    assert seen["kwargs"]["review_profile"] == "ukrainian"
    assert seen["kwargs"]["pr_number"] == 77


def test_mixed_pr_refuses_naming_the_code_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("mixed PR must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("mixed-branch", "b" * 40),
    )

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if "--paginate" in command:
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{_CONTENT_PATH}\n{_CODE_PATH}\n"
            )
        return subprocess.CompletedProcess(command, 0, stdout="2\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match=rf"gemini_code_review_forbidden.*{_CODE_PATH}"):
        _handle_acp_compat(_review_args(pr=88), "agy")


def test_pr_file_listing_failure_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file-listing failure must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("broken-branch", "c" * 40),
    )

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        return subprocess.CompletedProcess(command, 1, stderr="gh unavailable")

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match="could not list changed files"):
        _handle_acp_compat(_review_args(pr=99), "agy")


def test_pr_file_past_the_hundredth_still_refuses_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """A code file at position 120 must refuse. The old 100-file page would hide it."""

    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a code file past page 1 must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("wide-branch", "d" * 40),
    )
    names = [f"curriculum/l2-uk-en/a1/page-{index}.md" for index in range(1, 151)]
    names[119] = _CODE_PATH

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if "--paginate" in command:
            assert command == [
                "gh",
                "api",
                "--paginate",
                "repos/{owner}/{repo}/pulls/120/files",
                "--jq",
                ".[].filename",
            ]
            return subprocess.CompletedProcess(command, 0, stdout="\n".join(names) + "\n")
        assert command == [
            "gh",
            "api",
            "repos/{owner}/{repo}/pulls/120",
            "--jq",
            ".changed_files",
        ]
        return subprocess.CompletedProcess(command, 0, stdout="150\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match=rf"gemini_code_review_forbidden.*{_CODE_PATH}"):
        _handle_acp_compat(_review_args(pr=120), "agy")


def test_content_only_branch_reaches_gemini_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_dispatch(target: str, content: str, **kwargs: object) -> None:
        seen["branch"] = kwargs.get("branch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr("subprocess.run", _fake_branch_diff("content-branch", f"{_CONTENT_PATH}\n"))
    _handle_acp_compat(_review_args(branch="content-branch"), "agy")
    assert seen["branch"] == "content-branch"


def test_prefixed_branch_names_are_refused_before_git(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object):
        raise AssertionError(f"prefixed branch must not reach git: {command}")

    monkeypatch.setattr("subprocess.run", fake_run)
    for name in ("origin/feature", "refs/heads/feature", "github/feature", "+feature", "-feature", "feat:ure"):
        with pytest.raises(SystemExit, match="could not list changed files"):
            _handle_acp_compat(_review_args(branch=name), "agy")


def test_stale_local_content_branch_is_refused_when_remote_has_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A local content-only ref must not hide code on origin/<branch>."""

    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("remote code must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "subprocess.run",
        _fake_branch_diff("feature", f"{_CONTENT_PATH}\n{_CODE_PATH}\n"),
    )
    with pytest.raises(SystemExit, match=rf"gemini_code_review_forbidden.*{_CODE_PATH}"):
        _handle_acp_compat(_review_args(branch="feature"), "agy")


def _dispatch_argv(*extra: str) -> list[str]:
    return [
        "dispatch",
        "--agent",
        "agy",
        "--task-id",
        "agy-review-gate",
        "--prompt",
        "перевір український текст",
        *extra,
    ]


def test_delegate_review_verdict_without_profile_is_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import delegate

    def _unexpected_spawn(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("review-verdict without a profile must not spawn")

    monkeypatch.setattr(delegate.subprocess, "Popen", _unexpected_spawn)
    args = delegate.build_parser().parse_args(
        _dispatch_argv("--require-review-verdict")
    )
    assert delegate.cmd_dispatch(args) == 2
    assert "--review-profile" in capsys.readouterr().err
    assert delegate._read_state(delegate._state_path("agy-review-gate")) is None


def test_delegate_review_verdict_mixed_branch_names_the_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import delegate

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    monkeypatch.setattr(
        "subprocess.run",
        _fake_branch_diff("feature", f"{_CONTENT_PATH}\n{_CODE_PATH}\n"),
    )
    args = delegate.build_parser().parse_args(
        _dispatch_argv("--require-review-verdict", "--review-profile", "ukrainian", "--branch", "feature")
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "gemini_code_review_forbidden" in err
    assert _CODE_PATH in err


def test_delegate_review_verdict_file_listing_failure_is_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import delegate

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    monkeypatch.setattr("subprocess.run", _fake_branch_diff("feature", "", fail="fetch"))
    args = delegate.build_parser().parse_args(
        _dispatch_argv("--require-review-verdict", "--review-profile", "ukrainian", "--branch", "feature")
    )
    assert delegate.cmd_dispatch(args) == 2
    assert "could not list changed files" in capsys.readouterr().err


def test_delegate_review_verdict_content_branch_passes_the_gate(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import delegate

    listed: list[list[str]] = []
    scripted = _fake_branch_diff("feature", f"{_CONTENT_PATH}\n")

    def fake_run(command: list[str], **kwargs: object):
        listed.append(command)
        return scripted(command, **kwargs)

    monkeypatch.setattr("subprocess.run", fake_run)
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "agy-content-ok",
            "--prompt",
            "Implement the requested dispatch guard and add regression tests.",
            "--require-review-verdict",
            "--review-profile",
            "ukrainian",
            "--branch",
            "feature",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "write-shaped prompt" in err
    assert "gemini_code_review_forbidden" not in err
    assert listed == [
        ["git", "check-ref-format", "--branch", "feature"],
        ["git", "fetch", "origin", _branch_refspec("feature")],
        ["git", "rev-parse", "--verify", "refs/remotes/origin/feature"],
        ["git", "diff", "--name-only", f"origin/main...{_REMOTE_SHA}"],
    ]


def test_agy_implementation_dispatch_is_not_review_gated(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import delegate

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "check-ref-format"]:
            return subprocess.CompletedProcess(command, 0, stdout="feature\n")
        raise AssertionError(f"implementation dispatch must not list a review diff: {command}")

    monkeypatch.setattr("subprocess.run", fake_run)
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "agy-impl",
            "--prompt",
            "Implement the requested dispatch guard and add regression tests.",
            "--branch",
            "feature",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "write-shaped prompt" in err
    assert "gemini_code_review_forbidden" not in err
    assert "--review-profile" not in err


def test_branch_fetch_failure_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a failed fetch must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr("subprocess.run", _fake_branch_diff("feature", "", fail="fetch"))
    with pytest.raises(SystemExit, match="could not list changed files"):
        _handle_acp_compat(_review_args(branch="feature"), "agy")


def test_branch_diff_failure_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a failed diff must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr("subprocess.run", _fake_branch_diff("feature", "", fail="diff"))
    with pytest.raises(SystemExit, match="could not list changed files"):
        _handle_acp_compat(_review_args(branch="feature"), "agy")


def test_pr_changed_files_mismatch_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a short PR file list must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("content-branch", "e" * 40),
    )

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n")
        return subprocess.CompletedProcess(command, 0, stdout="2\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match="does not match changed_files"):
        _handle_acp_compat(_review_args(pr=41), "agy")


def test_pr_number_below_one_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("PR number below 1 must not reach Gemini dispatch")

    def fake_run(command: list[str], **kwargs: object):
        raise AssertionError(f"PR number below 1 must not reach gh: {command}")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("content-branch", "e" * 40),
    )
    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match="could not list changed files"):
        _handle_acp_compat(_review_args(pr=0), "agy")


def _git(repo: str, *args: str) -> None:
    import subprocess

    from scripts.common.git_context import sanitized_git_env

    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=sanitized_git_env(),
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise AssertionError(f"git {' '.join(args)} failed: {detail}")


def test_validate_plain_branch_name_real_git_refuses_unsafe_names(tmp_path) -> None:
    """``a..b``, ``x.lock``, a space, and ``@{-1}`` are refused; one plain name is kept.

    ``@{-1}`` is a previous checkout in this repo, so ``check-ref-format --branch``
    would expand it. The validator must refuse that shorthand instead of returning
    the expanded name.
    """
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    repo = tmp_path / "repo"
    repo.mkdir()
    root = str(repo)
    _git(root, "init", "-b", "valid-name")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (repo / "f").write_text("hi\n", encoding="utf-8")
    _git(root, "add", "f")
    _git(root, "commit", "-m", "init")
    _git(root, "checkout", "-b", "other")

    for name in ("a..b", "x.lock", "name with space", "@{-1}"):
        with pytest.raises(UnsafeBranchNameError):
            validate_plain_branch_name(name, repo_root=root)

    assert validate_plain_branch_name("valid-name", repo_root=root) == "valid-name"


def test_branch_changed_paths_ignore_hostile_git_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Fetch, rev-parse, and diff must follow ``repo_root``, not the caller's ``GIT_DIR``."""
    from scripts.ai_agent_bridge._agy import list_branch_changed_paths

    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    hostile = tmp_path / "hostile"
    _git(str(tmp_path), "init", "--bare", str(remote))
    repo.mkdir()
    root = str(repo)
    _git(root, "init", "-b", "trunk")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "remote", "add", "origin", str(remote))
    (repo / "base").write_text("base\n", encoding="utf-8")
    _git(root, "add", "base")
    _git(root, "commit", "-m", "base")
    _git(root, "branch", "main")
    _git(root, "checkout", "-b", "feature")
    (repo / "notes.txt").write_text("feature\n", encoding="utf-8")
    _git(root, "add", "notes.txt")
    _git(root, "commit", "-m", "feature")
    _git(str(remote), "fetch", root, "main:main", "feature:feature")
    _git(root, "fetch", "origin", "+refs/heads/main:refs/remotes/origin/main")
    _git(str(tmp_path), "init", "-b", "main", str(hostile))

    monkeypatch.setenv("GIT_DIR", str(hostile / ".git"))
    assert list_branch_changed_paths("feature", repo_root=root) == ["notes.txt"]
