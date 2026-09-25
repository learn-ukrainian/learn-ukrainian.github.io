"""Gemini review requests require an explicit profile (operator 2026-09-25)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge._agy import gemini_review_profile_error
from scripts.ai_agent_bridge._channels_cli import _gemini_review_request_error
from scripts.ai_agent_bridge._cli import _handle_acp_compat
from scripts.audit import llm_reviewer_dispatch

pytestmark = pytest.mark.reads_content


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

        if command[:2] == ["git", "fetch"]:
            assert command == ["git", "fetch", "origin", _branch_refspec(name)]
            code = 1 if fail == "fetch" else 0
            return subprocess.CompletedProcess(command, code, stderr="fetch failed" if code else "")
        if command[:3] == ["git", "rev-parse", "--verify"]:
            assert command == ["git", "rev-parse", "--verify", f"refs/remotes/origin/{name}"]
            code = 1 if fail == "rev-parse" else 0
            stdout = "" if code else f"{_REMOTE_SHA}\n"
            return subprocess.CompletedProcess(command, code, stdout=stdout, stderr="missing" if code else "")
        assert command == ["git", "diff", "--name-only", "--no-renames", f"origin/main...{_REMOTE_SHA}"]
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

    sha = "a" * 40

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "fetch"]:
            assert command == ["git", "fetch", "origin", sha]
            return subprocess.CompletedProcess(command, 0, stdout="")
        assert command == ["git", "diff", "--name-only", "--no-renames", f"origin/main...{sha}"]
        return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    _handle_acp_compat(_review_args(pr=77), "agy")
    assert seen["target"] == "agy"
    assert seen["kwargs"]["review_profile"] == "ukrainian"
    assert seen["kwargs"]["pr_number"] == 77
    assert seen["kwargs"]["pinned_head"] == sha


def test_mixed_pr_refuses_naming_the_code_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_dispatch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("mixed PR must not reach Gemini dispatch")

    monkeypatch.setattr("scripts.ai_agent_bridge._cli._dispatch_headless_review", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("mixed-branch", "b" * 40),
    )

    sha = "b" * 40

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "fetch"]:
            assert command[-1] == sha
            return subprocess.CompletedProcess(command, 0, stdout="")
        assert command[-1] == f"origin/main...{sha}"
        return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n{_CODE_PATH}\n")

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
    sha = "d" * 40
    names = [f"curriculum/l2-uk-en/a1/page-{index}.md" for index in range(1, 151)]
    names[119] = _CODE_PATH

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "fetch"]:
            assert command == ["git", "fetch", "origin", sha]
            return subprocess.CompletedProcess(command, 0, stdout="")
        assert command == ["git", "diff", "--name-only", "--no-renames", f"origin/main...{sha}"]
        return subprocess.CompletedProcess(command, 0, stdout="\n".join(names) + "\n")

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
    args = delegate.build_parser().parse_args(_dispatch_argv("--require-review-verdict"))
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
        ["git", "fetch", "origin", _branch_refspec("feature")],
        ["git", "rev-parse", "--verify", "refs/remotes/origin/feature"],
        ["git", "diff", "--name-only", "--no-renames", f"origin/main...{_REMOTE_SHA}"],
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


def test_pr_head_move_between_gate_and_dispatch_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """The path gate's SHA is the only commit dispatch may check out."""
    gate_sha = "e" * 40
    moved_sha = "f" * 40

    def fake_dispatch(*_args: object, **kwargs: object) -> None:
        assert kwargs["pinned_head"] == gate_sha
        raise RuntimeError(
            f"refusing dispatch: fetched branch head {moved_sha} differs from the Gemini path-gate SHA {gate_sha}"
        )

    monkeypatch.setattr("scripts.ai_agent_bridge._dispatch_wrappers.run_ask_review_dispatch", fake_dispatch)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._cli._resolve_same_repo_pr_head",
        lambda number: ("content-branch", gate_sha),
    )

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "fetch"]:
            assert command[-1] == gate_sha
            return subprocess.CompletedProcess(command, 0, stdout="")
        return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(SystemExit, match="differs from the Gemini path-gate SHA"):
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
        timeout=30,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise AssertionError(f"git {' '.join(args)} failed: {detail}")


# Names whose pure-Python verdict must match ``git check-ref-format --branch``.
# Deliberate rejects stay off this list: ``@`` (``--branch`` prints it),
# ``@{-N}`` (git expands it), and ``HEAD`` (some git versions accept
# ``refs/heads/HEAD``). Prefix rules ``-`` and ``:`` are also omitted: their
# git verdict depends on the git version.
# Accepting names below were checked with ``git check-ref-format --branch``
# on this host. ``a.lock/y`` was tried and rejected (a component ends in
# ``.lock``), so it is not an accepting case.
_GIT_BRANCH_FORMAT_AGREEMENT = (
    "valid-name",
    "cursor/task",
    "a/b",
    "x.lockx",
    "a@b",
    "é",
    "feat/a-b_c.d",
    "v1.2.3",
    "a..b",
    "x.lock",
    "name with space",
    "trail.",
    "trail/",
    "foo//bar",
    ".hidden",
    "foo/.bar",
    "foo/bar.lock",
    "has~tilde",
    "has^caret",
    "has?question",
    "has*star",
    "has[bracket",
    "has\\backslash",
    "a\nb",
    "lead/",
)


def _git_check_ref_format_branch(repo: str, name: str) -> str | None:
    """Return the name git prints, or None when ``--branch`` rejects it."""
    import subprocess

    from scripts.common.git_context import sanitized_git_env

    completed = subprocess.run(
        ["git", "check-ref-format", "--branch", name],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=sanitized_git_env(),
        timeout=30,
    )
    if completed.returncode != 0:
        return None
    confirmed = (completed.stdout or "").strip()
    if not confirmed or "\n" in confirmed or confirmed != name:
        return None
    return confirmed


def test_validate_plain_branch_name_real_git_refuses_unsafe_names(tmp_path) -> None:
    """Unsafe names are refused, and the pure rules agree with git on a fixed list.

    ``@{-1}`` is a previous checkout in this repo, so ``check-ref-format --branch``
    expands it. The validator must refuse that shorthand instead of returning the
    expanded name. Git runs only in this test, with a timeout.
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

    for name in ("a..b", "x.lock", "name with space", "@{-1}", "@", "HEAD", "a@{b"):
        with pytest.raises(UnsafeBranchNameError):
            validate_plain_branch_name(name, repo_root=root)

    # Prefix rules, not a git-version contract. ``-leading`` is the leading
    # ``-`` reject; ``has:colon`` is the ``:`` reject.
    for name in ("-leading", "has:colon"):
        with pytest.raises(UnsafeBranchNameError):
            validate_plain_branch_name(name, repo_root=root)

    assert validate_plain_branch_name("valid-name", repo_root=root) == "valid-name"
    import subprocess

    from scripts.common.git_context import sanitized_git_env

    expanded = subprocess.run(
        ["git", "check-ref-format", "--branch", "@{-1}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        env=sanitized_git_env(),
        timeout=30,
    )
    assert expanded.returncode == 0
    assert expanded.stdout.strip() == "valid-name"

    for name in _GIT_BRANCH_FORMAT_AGREEMENT:
        git_name = _git_check_ref_format_branch(root, name)
        if git_name is None:
            with pytest.raises(UnsafeBranchNameError):
                validate_plain_branch_name(name, repo_root=root)
        else:
            assert validate_plain_branch_name(name, repo_root=root) == git_name


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
    heads: list[str] = []
    assert list_branch_changed_paths("feature", repo_root=root, head_out=heads) == ["notes.txt"]
    assert len(heads) == 1 and len(heads[0]) == 40


def test_cursor_gemini_model_review_is_refused_including_after_substitution(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A Gemini model on Cursor is a review gate, including the post-substitution model."""
    from scripts import delegate
    from scripts.ai_agent_bridge._agy import gemini_review_verdict_dispatch_error

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "cursor",
            "--model",
            "gemini-3.1-pro",
            "--task-id",
            "cursor-gemini-review",
            "--prompt",
            "Review this change.",
            "--require-review-verdict",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "--review-profile" in err

    substituted = gemini_review_verdict_dispatch_error(
        agent="cursor",
        require_review_verdict=True,
        profile=None,
        pr_number=None,
        branch=None,
        repo_root=".",
        model="grok-4.7",
        resolved_model="google/gemini-3.8-flash-high",
    )
    assert substituted is not None
    assert "--review-profile" in substituted


def test_rename_from_code_onto_content_is_a_code_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--no-renames`` keeps the deleted code path visible on the pinned SHA."""
    from scripts.ai_agent_bridge._agy import list_branch_changed_paths, list_commit_changed_paths

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["git", "diff"]:
            assert "--no-renames" in command
            return subprocess.CompletedProcess(command, 0, stdout=f"scripts/x.py\n{_CONTENT_PATH}\n")
        if command[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(command, 0, stdout="")
        if command[:3] == ["git", "rev-parse", "--verify"]:
            return subprocess.CompletedProcess(command, 0, stdout=f"{_REMOTE_SHA}\n")
        if command[:2] == ["git", "check-ref-format"]:
            return subprocess.CompletedProcess(command, 0, stdout="feature\n")
        raise AssertionError(command)

    monkeypatch.setattr("subprocess.run", fake_run)
    branch_paths = list_branch_changed_paths("feature", repo_root=".")
    assert "scripts/x.py" in branch_paths
    pr_paths = list_commit_changed_paths(_REMOTE_SHA, repo_root=".")
    assert pr_paths == ["scripts/x.py", _CONTENT_PATH]


def test_delegate_pr_gate_diffs_the_resolved_sha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``delegate --pr`` resolves the head once and diffs that SHA, not the API file list."""
    from scripts import delegate

    sha = "a" * 40
    payload = '{"headRefName":"feature","headRefOid":"' + sha + '","isCrossRepository":false}\n'

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["gh", "pr"]:
            return subprocess.CompletedProcess(command, 0, stdout=payload)
        if command[:2] == ["git", "fetch"]:
            assert command == ["git", "fetch", "origin", sha]
            return subprocess.CompletedProcess(command, 0, stdout="")
        if command[:2] == ["git", "diff"]:
            assert command == ["git", "diff", "--name-only", "--no-renames", f"origin/main...{sha}"]
            return subprocess.CompletedProcess(command, 0, stdout=f"{_CONTENT_PATH}\n")
        if command[:2] == ["git", "check-ref-format"]:
            return subprocess.CompletedProcess(command, 0, stdout="feature\n")
        raise AssertionError(command)

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "agy-pr-pin",
            "--prompt",
            "Implement the requested dispatch guard and add regression tests.",
            "--require-review-verdict",
            "--review-profile",
            "ukrainian",
            "--pr",
            "77",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "write-shaped prompt" in err
    assert "gemini_code_review_forbidden" not in err
    assert args.pinned_head == sha
    assert args.branch == "feature"


def test_delegate_pr_pinned_head_must_match_resolved_sha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--pr`` plus an unrelated ``--pinned-head`` is refused, even with the right branch."""
    from scripts import delegate

    sha = "a" * 40
    other = "b" * 40
    payload = '{"headRefName":"feature","headRefOid":"' + sha + '","isCrossRepository":false}\n'

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["gh", "pr"]:
            return subprocess.CompletedProcess(command, 0, stdout=payload)
        if command[:2] == ["git", "check-ref-format"]:
            return subprocess.CompletedProcess(command, 0, stdout="feature\n")
        raise AssertionError(command)

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "agy-pr-pin-mismatch",
            "--prompt",
            "Implement the requested dispatch guard and add regression tests.",
            "--pr",
            "77",
            "--pinned-head",
            other,
            "--branch",
            "feature",
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert f"--pinned-head {other} is not PR #77 head {sha}" in err
    assert args.branch == "feature"


def test_delegate_pr_pinned_head_requires_the_pr_branch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A pin without ``--branch`` must not fall through and start from main."""
    from scripts import delegate

    sha = "a" * 40
    payload = '{"headRefName":"feature","headRefOid":"' + sha + '","isCrossRepository":false}\n'

    def fake_run(command: list[str], **kwargs: object):
        import subprocess

        if command[:2] == ["gh", "pr"]:
            return subprocess.CompletedProcess(command, 0, stdout=payload)
        if command[:2] == ["git", "check-ref-format"]:
            return subprocess.CompletedProcess(command, 0, stdout="feature\n")
        raise AssertionError(command)

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("spawn")))
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "agy-pr-pin-no-branch",
            "--prompt",
            "Implement the requested dispatch guard and add regression tests.",
            "--pr",
            "77",
            "--pinned-head",
            sha,
        ]
    )
    assert delegate.cmd_dispatch(args) == 2
    err = capsys.readouterr().err
    assert "--pr 77 with --pinned-head requires --branch 'feature'" in err
    assert args.branch is None


def test_dispatch_refuses_when_fetched_head_differs_from_gate_sha() -> None:
    from scripts.delegate import _refuse_if_gate_head_moved

    gate = "a" * 40
    _refuse_if_gate_head_moved(gate, gate)
    with pytest.raises(RuntimeError, match="differs from the Gemini path-gate SHA"):
        _refuse_if_gate_head_moved("b" * 40, gate)
