"""#7155: ask-* review intent must reach a reviewer with tools, never ACP.

ACP is intercommunication only (`--deny-all --no-fs --no-terminal`); a
reviewer must be able to run `gh`/pytest/fs. Live proof: #7155
`ask-codex --review --pr 7155` ABSTAINed via ACP (`gh auth` unavailable),
while the same review via headless dispatch with tools approved. `ask-*
--review` / `--type review` / `--pr` / `--branch` now route to the headless
`scripts/delegate.py dispatch` path, never to the tool-less ACP shim
(`run_compat_ask`). Ordinary asks without review intent are unaffected.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys

import pytest

from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

_HEAD_SHA = "a" * 40
_MOVED_SHA = "b" * 40
_HEAD_BRANCH = "cursor/impl-8706"


def _install_fake_gh(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdout: str = "",
    stderr: str = "",
    code: int = 0,
) -> None:
    """Put a no-network ``gh`` first on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gh"
    script.write_text(
        f"#!/bin/sh\nprintf '%s' {json.dumps(stdout)}\nprintf '%s' {json.dumps(stderr)} >&2\nexit {int(code)}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    def respond(args, **kwargs):
        return __import__('subprocess').CompletedProcess(args, code, stdout, stderr)
    monkeypatch.setattr(_cli.github_client, "run", respond)


def _same_repo_payload(*, head_sha: str = _HEAD_SHA, branch: str = _HEAD_BRANCH) -> str:
    return json.dumps(
        {
            "headRefName": branch,
            "headRefOid": head_sha,
            "isCrossRepository": False,
        }
    )


@pytest.fixture()
def same_repo_pr_gh(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Positive forge metadata must name a real isolated canonical Git ref."""
    from tests.test_review_target_resolution import _git, _init_repo, _publish_pr_branch

    repo = _init_repo(tmp_path)
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    _git(repo, "remote", "add", "origin", "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _publish_pr_branch(repo, _HEAD_BRANCH, head)
    monkeypatch.setattr(_cli, "REPO_ROOT", repo)
    monkeypatch.setattr(sys.modules[__name__], "_HEAD_SHA", head)
    _install_fake_gh(tmp_path, monkeypatch, stdout=_same_repo_payload(head_sha=head))
    real_run, real_popen = subprocess.run, subprocess.Popen

    def git_run(command, *args, **kwargs):
        assert command[0] == "git", "provider or other external process reached"
        assert kwargs["env"]["GIT_ALLOW_PROTOCOL"] == "file"
        return real_run(command, *args, **kwargs)

    def git_popen(command, *args, **kwargs):
        assert command[0] == "git", "provider or other external process reached"
        assert kwargs["env"]["GIT_ALLOW_PROTOCOL"] == "file"
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", git_run)
    monkeypatch.setattr(subprocess, "Popen", git_popen)


@pytest.fixture()
def acp_guard(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Fail the test the instant review intent reaches the tool-less ACP shim."""
    calls = {"count": 0}

    def fail_if_called(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("run_compat_ask must not be called for review intent (#7155)")

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fail_if_called)
    return calls


@pytest.fixture()
def captured_dispatch(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_dispatch(agent, content, **kwargs):
        captured["agent"] = agent
        captured["content"] = content
        captured.update(kwargs)
        return {
            "ok": True,
            "status": "done",
            "response": "VERDICT: APPROVED\nEvidence: reviewed the diff at scripts/foo.py:1.",
            "worktree_base_sha": _HEAD_SHA,
        }

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", fake_dispatch)
    return captured


def test_ask_pr_routes_to_headless_dispatch_not_acp(
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    same_repo_pr_gh: None,
) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-7010", "--pr", "7010", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert acp_guard["count"] == 0
    assert captured_dispatch["agent"] == "claude"
    assert captured_dispatch["task_id"] == "review-7010"
    # Target folded into the prompt.
    assert "PR #7010" in captured_dispatch["content"]
    assert "gh pr diff 7010" in captured_dispatch["content"]
    assert f"exact head {_HEAD_SHA}" in captured_dispatch["content"]
    assert "git rev-parse HEAD" in captured_dispatch["content"]
    assert f"If it differs from {_HEAD_SHA}" in captured_dispatch["content"]
    assert "stop without a verdict" in captured_dispatch["content"]
    assert captured_dispatch["branch"] == _HEAD_BRANCH


def test_ask_branch_routes_to_headless_dispatch_not_acp(
    acp_guard: dict[str, int], captured_dispatch: dict[str, object]
) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-codex", "review this change", "--task-id", "review-branch", "--branch", "feat-x", "--from", "test"]
    )

    _cli._handle_ask_codex(args)

    assert acp_guard["count"] == 0
    assert "origin/feat-x" in captured_dispatch["content"]


def test_ordinary_ask_without_review_intent_still_uses_acp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-review asks are unaffected: ACP intercom stays the transport."""
    from types import SimpleNamespace

    captured: dict[str, object] = {}

    def fake_compat(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fake_compat)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "just a question", "--task-id", "plain-ask", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert captured["args"][0] == "claude"
    assert captured["review"] is False


def test_ask_pr_refuses_cross_repository(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gh(
        tmp_path,
        monkeypatch,
        stdout=json.dumps(
            {
                "headRefName": "fork/feature",
                "headRefOid": _HEAD_SHA,
                "isCrossRepository": True,
            }
        ),
    )
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-cross", "--pr", "12", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="cross-repository"):
        _cli._handle_ask_claude(args)


def test_ask_pr_refuses_when_gh_fails(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gh(tmp_path, monkeypatch, stderr="no such pull request", code=1)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-missing", "--pr", "99", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="refusing to review main"):
        _cli._handle_ask_claude(args)


def test_ask_pr_refuses_when_dispatch_base_sha_moved(
    same_repo_pr_gh: None,
    captured_dispatch: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def moved_dispatch(agent, content, **kwargs):
        captured_dispatch["agent"] = agent
        captured_dispatch["content"] = content
        captured_dispatch.update(kwargs)
        return {
            "ok": True,
            "status": "done",
            "response": "VERDICT: APPROVED\nEvidence: reviewed the diff at scripts/foo.py:1.",
            "worktree_base_sha": _MOVED_SHA,
        }

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", moved_dispatch)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-moved", "--pr", "8706", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="refusing dispatch") as exc_info:
        _cli._handle_ask_claude(args)

    message = str(exc_info.value)
    assert captured_dispatch["pinned_head"] == _HEAD_SHA
    assert f"resolved {_HEAD_SHA}" in message
    assert f"dispatch record base {_MOVED_SHA}" in message


@pytest.mark.parametrize("target,model", [("claude", "claude-fable-5-1"), ("cursor", "claude-fable-5-1-thinking-high")])
def test_ask_review_refuses_a_fable_pin_before_any_dispatch(monkeypatch, target, model):
    """#9583: an ask-* review reads the catalog roles and exits with the refusal, before a prompt is written."""
    monkeypatch.setattr(
        _dispatch_wrappers, "build_ask_review_dispatch_command", lambda *_a, **_k: pytest.fail("refused review dispatched")
    )
    with pytest.raises(SystemExit, match=r"REVIEW_ROUTE_REFUSED: .*holds no review, critique or approval role"):
        _cli._dispatch_headless_review(
            target,
            "Review the branch.",
            data=None,
            task_id="review-9583",
            model=model,
            effort=None,
            output_path=None,
            stdout_only=False,
            hard_timeout=None,
        )


@pytest.fixture()
def registered_histories(tmp_path, monkeypatch):
    from scripts.dispatcher import git as dispatch_git
    from scripts.orchestration import fleet_repos
    from tests.test_review_target_resolution import _git, _init_repo, _publish_pr_branch

    roots, heads = {}, {}
    for key, slug in (("public", "example/public"), ("infra-private", "example/sibling")):
        seed = tmp_path / (key + "-seed")
        seed.mkdir()
        root = _init_repo(seed).rename(tmp_path / key)
        _git(root, "config", "core.hooksPath", os.devnull)
        (root / "app.py").write_text(f"print({key!r})\n", encoding="utf-8")
        _git(root, "add", "app.py")
        _git(root, "commit", "-qm", "distinct target")
        _git(root, "remote", "add", "origin", f"https://github.com/{slug}.git")
        heads[key] = _git(root, "rev-parse", "HEAD").stdout.strip()
        _publish_pr_branch(root, "review-shared", heads[key])
        roots[key] = root
    assert heads["public"] != heads["infra-private"]
    config = tmp_path / "repos.yaml"
    config.write_text(
        "repos:\n"
        "  public: {github: example/public, local_name: public, default: true}\n"
        "  infra-private: {github: example/sibling, local_name: infra-private}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fleet_repos, "_CONFIG_PATH", config)
    monkeypatch.setattr(dispatch_git, "CONFIG", config)
    monkeypatch.setattr(dispatch_git, "ROOT", roots["public"])
    monkeypatch.setattr(_cli, "REPO_ROOT", roots["public"])
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    return roots, heads


@pytest.mark.parametrize("selector", [None, "public", "infra-private", " INFRA-PRIVATE "])
@pytest.mark.parametrize("target_flag", ["--pr", "--branch"])
def test_registered_review_targets_use_selected_history(
    registered_histories, tmp_path, monkeypatch, selector, target_flag, acp_guard,
):
    from pathlib import Path

    from scripts.dispatcher import git as dispatch_git
    from scripts.dispatcher.cli import build_parser

    roots, heads = registered_histories
    key = selector.strip().lower() if selector else "public"
    calls = []
    result = tmp_path / "review-result"
    result.write_text("VERDICT: APPROVE\n", encoding="utf-8")
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(tmp_path))
    real_run = subprocess.run

    def boundary(command, **kwargs):
        if command[0] == "gh":
            assert kwargs["cwd"] == roots[key]
            assert command[command.index("--repo") + 1] == f"example/{'public' if key == 'public' else 'sibling'}"
            return subprocess.CompletedProcess(command, 0, _same_repo_payload(head_sha=heads[key], branch="review-shared"))
        if len(command) > 2 and command[1] == "scripts/dispatch.py":
            calls.append(command)
            if command[2] == "wait":
                return subprocess.CompletedProcess(command, 0, json.dumps({
                    "status": "done", "result_file": str(result), "worktree_base_sha": heads[key],
                }))
            parsed = build_parser().parse_args(command[2:])
            assert parsed.repo == (key if selector is not None else None)
            root, _ = dispatch_git.resolve_repo(parsed.repo)
            assert root == roots[key]
            _, _, sha = dispatch_git.worktree_plan(
                root, parsed.agent, parsed.task_id, parsed.pinned_head or parsed.branch,
            )
            assert sha == heads[key]
            prompt = Path(parsed.prompt_file).read_text()
            if target_flag == "--pr":
                assert parsed.pinned_head == heads[key]
                assert heads[key] in prompt
                assert heads["infra-private" if key == "public" else "public"] not in prompt
            return subprocess.CompletedProcess(command, 0)
        return real_run(command, **kwargs)

    monkeypatch.setattr(_cli.github_client, "run", boundary)
    monkeypatch.setattr(subprocess, "run", boundary)
    argv = ["ask-claude", "Review this.", "--task-id", "selected-review", target_flag]
    argv.append("12" if target_flag == "--pr" else "review-shared")
    if selector is not None:
        argv.extend(["--repo", selector])
    _cli._handle_ask_claude(_cli._build_parser().parse_args(argv))
    assert len(calls) == 2
    assert acp_guard["count"] == 0


@pytest.mark.parametrize("selector", ["unknown", "infra-private"])
def test_invalid_repository_refuses_before_provider(registered_histories, monkeypatch, selector, capsys):
    from scripts.orchestration import fleet_repos

    if selector == "infra-private":
        original = fleet_repos.load_fleet_repos
        from dataclasses import replace

        monkeypatch.setattr(fleet_repos, "load_fleet_repos", lambda: {
            key: replace(repo, local_name="absent-private-checkout") if key == selector else repo
            for key, repo in original().items()
        })
        # The resolver imports this function, so use the same test catalog there.
        monkeypatch.setattr("scripts.review.target_resolution.load_fleet_repos", fleet_repos.load_fleet_repos)
    monkeypatch.setattr(_cli.github_client, "run", lambda *_a, **_k: pytest.fail("forge/provider reached"))
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", lambda *_a, **_k: pytest.fail("provider reached"))
    args = _cli._build_parser().parse_args([
        "ask-claude", "Review.", "--task-id", "invalid-review", "--branch", "review-shared", "--repo", selector,
    ])
    with pytest.raises(SystemExit) as exc:
        _cli._handle_ask_claude(args)
    output = str(exc.value) + capsys.readouterr().err
    assert "absent-private-checkout" not in output
    assert "example/sibling" not in output
    assert ("unknown --repo" if selector == "unknown" else "PRIVATE_REVIEW_TARGET_UNRESOLVED") in output


def test_repository_selector_requires_review_intent(monkeypatch):
    monkeypatch.setattr(_acp_compat, "run_compat_ask", lambda *_a, **_k: pytest.fail("ACP reached"))
    args = _cli._build_parser().parse_args([
        "ask-claude", "Question.", "--task-id", "ordinary", "--repo", "public",
    ])
    with pytest.raises(SystemExit, match="--repo requires review intent"):
        _cli._handle_ask_claude(args)


@pytest.mark.parametrize("failure", ["wrong-origin", "missing-branch", "forge-error", "cross-repository"])
def test_selected_repository_refusals_preserve_private_boundary(registered_histories, monkeypatch, failure, capsys):
    from tests.test_review_target_resolution import _git

    roots, heads = registered_histories
    if failure == "wrong-origin":
        _git(roots["infra-private"], "remote", "set-url", "origin", "https://github.com/example/wrong.git")
    elif failure == "missing-branch":
        _git(roots["infra-private"], "--git-dir", str(roots["infra-private"].parent / "infra-private-canonical.git"),
             "update-ref", "-d", "refs/heads/review-shared")
    payload = json.loads(_same_repo_payload(head_sha=heads["infra-private"], branch="review-shared"))
    payload["isCrossRepository"] = failure == "cross-repository"

    def forge(command, **kwargs):
        assert failure != "wrong-origin", "invalid identity reached forge"
        return subprocess.CompletedProcess(
            command, int(failure == "forge-error"), json.dumps(payload), "private-diagnostic-sentinel",
        )

    monkeypatch.setattr(_cli.github_client, "run", forge)
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", lambda *_a, **_k: pytest.fail("provider reached"))
    args = _cli._build_parser().parse_args([
        "ask-claude", "Review.", "--task-id", "refused-review", "--pr", "12", "--repo", "infra-private",
    ])
    with pytest.raises(SystemExit) as exc:
        _cli._handle_ask_claude(args)
    assert "private-diagnostic-sentinel" not in str(exc.value) + capsys.readouterr().err
