"""Review commands may use their temp lease without making the checkout writable."""

import os
import sqlite3
import subprocess
import sys
import tomllib

import pytest

from scripts.agent_runtime.adapters import codex as codex_adapter
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.common.github_client import GitHubClient, Response


@pytest.fixture(autouse=True)
def scratch_base(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))


def review_plan(cwd, lease, session_id=None):
    return CodexAdapter().build_invocation(
        prompt="Review the change",
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id="review-test",
        session_id=session_id,
        tool_config={"read_only_tmp_root": str(lease)},
    )


@pytest.mark.parametrize("args", [("issue", "view", "7814"), ("pr", "view", "123")])
def test_review_gh_shim_uses_client_with_review_lease(tmp_path, args, gh_shim_sandbox):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    backend = tmp_path / "fake-gh"
    backend.write_text(
        '#!/bin/sh\nset -eu\ntest -d "$TMPDIR" || { echo "missing scratch lease" >&2; exit 1; }\nprintf "%s\\n" "$@"\n'
    )
    backend.chmod(0o755)
    root, shim, _tooling = gh_shim_sandbox
    env = {**os.environ, "TMPDIR": str(tmp_path / "missing"), "AGENT_REAL_GH": str(backend), "AGENT_NO_MERGE": "1"}
    before = subprocess.run([str(shim), *args], env=env, cwd=root, capture_output=True, text=True, timeout=30)
    assert before.returncode != 0
    assert before.returncode == 1

    plan = review_plan(checkout, lease)
    after = subprocess.run(
        [str(shim), *args], env={**env, **plan.env_overrides}, cwd=root, capture_output=True, text=True, timeout=30
    )
    assert after.returncode == 0, after.stderr
    assert after.stdout.splitlines() == list(args)
    assert not list(lease.glob("agent-gh.*"))


def test_review_gh_shim_refuses_raw_comment_without_calling_backend(tmp_path, gh_shim_sandbox):
    _root, shim, _tooling = gh_shim_sandbox
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    backend = tmp_path / "fake-gh"
    marker = tmp_path / "backend-called"
    backend.write_text(f'#!/bin/sh\ntouch "{marker}"\n')
    backend.chmod(0o755)
    plan = review_plan(checkout, lease)
    env = {**os.environ, **plan.env_overrides, "AGENT_REAL_GH": str(backend), "AGENT_NO_MERGE": "1"}
    result = subprocess.run(
        [str(shim), "pr", "comment", "123", "--body", "verdict"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "raw public write refused" in result.stderr
    assert "scripts.publish pr-comment" in result.stderr
    assert not marker.exists()
    assert not list(lease.glob("agent-gh.*"))


@pytest.mark.parametrize("session_id", [None, "2c8337b6-35da-415d-806d-91d10b5b1381"])
def test_review_permissions_only_write_lease(tmp_path, session_id):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / 'review-"quoted"-📚'
    lease.mkdir(parents=True)
    plan = review_plan(checkout, lease, session_id)
    configs = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd[:-1]) if arg == "-c"]
    config = tomllib.loads("\n".join(value for value in configs if not value.startswith("model_reasoning_effort=")))
    profile = config["permissions"][config["default_permissions"]]
    assert profile["filesystem"] == {":root": "read", str(lease): "write"}
    assert profile["network"]["enabled"] is True
    assert profile["network"]["domains"] == {"github.com": "allow", "api.github.com": "allow"}
    assert config["features"]["network_proxy"] is True
    assert config["approval_policy"] == "never"
    assert config["mcp_servers"]["sources"]["default_tools_approval_mode"] == "prompt"
    assert "-s" not in plan.cmd
    assert "--dangerously-bypass-approvals-and-sandbox" not in plan.cmd
    assert plan.env_overrides["TMPDIR"] == str(lease)
    assert plan.output_file.parent == lease


@pytest.mark.parametrize("invalid", ["relative", "/", "checkout", "parent", "missing", "symlink"])
def test_review_rejects_unsafe_temp_roots(tmp_path, invalid):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    link = tmp_path / "link"
    link.symlink_to(checkout, target_is_directory=True)
    root = {
        "relative": "relative",
        "/": "/",
        "checkout": checkout,
        "parent": tmp_path,
        "missing": tmp_path / "missing",
        "symlink": link,
    }[invalid]
    with pytest.raises(ValueError, match="read_only_tmp_root"):
        review_plan(checkout, root)


def test_sources_prompt_fails_fast_when_read_only_cannot_approve(tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    monkeypatch.setattr(codex_adapter, "_argv_can_call_sources_mcp", lambda _argv: False)
    with pytest.raises(ValueError, match="mcp__sources__"):
        CodexAdapter().build_invocation(
            prompt="Call mcp__sources__verify_words before judging the sentence.",
            mode="read-only",
            cwd=checkout,
            model=None,
            task_id="review-test",
            session_id=None,
            tool_config={"read_only_tmp_root": str(lease)},
        )


def test_review_gh_shim_read_only_with_readonly_cache(tmp_path, gh_shim_sandbox):
    _root, shim, _tooling = gh_shim_sandbox
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    ro_cache = tmp_path / "ro-cache"
    ro_cache.mkdir()
    os.chmod(ro_cache, 0o500)
    backend = tmp_path / "fake-gh"
    backend.write_text(
        '#!/bin/sh\nset -eu\nprintf "HTTP/2.0 200 OK\\r\\nX-RateLimit-Remaining: 100\\r\\nX-RateLimit-Reset: 2000000000\\r\\n\\r\\n{\\"number\\": 10108, \\"state\\": \\"OPEN\\", \\"body\\": \\"text\\", \\"url\\": \\"https://github.com/unit/public/issues/10108\\"}"\n'
    )
    backend.chmod(0o700)
    plan = review_plan(checkout, lease)
    env = {
        **os.environ,
        **plan.env_overrides,
        "AGENT_REAL_GH": str(backend),
        "AGENT_NO_MERGE": "1",
        "LU_GITHUB_CACHE_DIR": str(ro_cache),
    }
    try:
        result = subprocess.run(
            [
                str(shim),
                "issue",
                "view",
                "10108",
                "--repo",
                "unit/public",
                "--json",
                "number,state,body,url",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert '"number": 10108' in result.stdout
        assert "OPSEC: publishing input unresolved" not in result.stderr
    finally:
        os.chmod(ro_cache, 0o700)


def test_raw_entry_read_failure_message_not_publishing_input(tmp_path, monkeypatch, capsys):
    from scripts.opsec import gh_entry

    executable = tmp_path / "real-gh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o700)
    monkeypatch.setattr(
        sys,
        "argv",
        ["entry", str(executable), "unit-shim", "issue", "view", "10108", "--repo", "unit/public", "--json", "number"],
    )

    def broken(*a, **k):
        raise RuntimeError("simulated read failure")

    monkeypatch.setattr(gh_entry, "admit", broken)
    assert gh_entry.main() == 2
    err = capsys.readouterr().err
    assert "OPSEC: read command failed; verify repository and flags." in err
    assert "OPSEC: publishing input unresolved" not in err


def test_review_gh_shim_read_only_with_readonly_sqlite_file(tmp_path, gh_shim_sandbox):
    _root, shim, _tooling = gh_shim_sandbox
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    cache_dir = tmp_path / "writable-cache-dir"
    cache_dir.mkdir()
    database = cache_dir / "cache.sqlite3"
    sqlite3.connect(database).close()
    database.chmod(0o400)

    # 1. Direct GitHubClient test
    calls = []

    def transport(*args):
        calls.append(args[:2])
        return Response(200, {}, b'{"number": 10108}')

    client = GitHubClient(cache_dir=cache_dir, transport=transport)
    resp = client.request("GET", "repos/unit/public/issues/10108")
    assert resp.status == 200
    assert client._memory_db is not None
    assert len(calls) == 1

    # 2. Subprocess shim test
    backend = tmp_path / "fake-gh"
    backend.write_text(
        '#!/bin/sh\nset -eu\nprintf "HTTP/2.0 200 OK\\r\\nX-RateLimit-Remaining: 100\\r\\nX-RateLimit-Reset: 2000000000\\r\\n\\r\\n{\\"number\\": 10108, \\"state\\": \\"OPEN\\", \\"body\\": \\"text\\", \\"url\\": \\"https://github.com/unit/public/issues/10108\\"}"\n'
    )
    backend.chmod(0o700)
    plan = review_plan(checkout, lease)
    env = {
        **os.environ,
        **plan.env_overrides,
        "AGENT_REAL_GH": str(backend),
        "AGENT_NO_MERGE": "1",
        "LU_GITHUB_CACHE_DIR": str(cache_dir),
    }
    try:
        result = subprocess.run(
            [
                str(shim),
                "issue",
                "view",
                "10108",
                "--repo",
                "unit/public",
                "--json",
                "number,state,body,url",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert '"number": 10108' in result.stdout
        assert "OPSEC: publishing input unresolved" not in result.stderr
    finally:
        database.chmod(0o600)


def test_review_gh_shim_read_only_with_connection_error_and_write_only_file(tmp_path, gh_shim_sandbox):
    _root, _shim, _tooling = gh_shim_sandbox
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    database = cache_dir / "cache.sqlite3"
    sqlite3.connect(database).close()
    database.chmod(0o200)

    calls = []

    def transport(*args):
        calls.append(args[:2])
        return Response(200, {}, b'{"number": 10108}')

    client = GitHubClient(cache_dir=cache_dir, transport=transport)
    try:
        resp = client.request("GET", "repos/unit/public/issues/10108")
        assert resp.status == 200
        assert client._memory_db is not None
        assert len(calls) == 1
    finally:
        database.chmod(0o600)


def test_review_gh_shim_read_only_with_readonly_populated_schema_and_directory(tmp_path, gh_shim_sandbox):
    _root, _shim, _tooling = gh_shim_sandbox
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    setup = GitHubClient(cache_dir=cache_dir)
    with setup._db():
        pass
    database = cache_dir / "cache.sqlite3"
    cache_dir.chmod(0o500)

    calls = []

    def transport(*args):
        calls.append(args[:2])
        return Response(200, {}, b'{"number": 10108}')

    client = GitHubClient(cache_dir=cache_dir, transport=transport)
    try:
        resp = client.request("GET", "repos/unit/public/issues/10108")
        assert resp.status == 200
        assert client._memory_db is not None
        assert len(calls) == 1
    finally:
        cache_dir.chmod(0o700)
        database.chmod(0o600)
