"""Isolated origin fetch in a real blob-filtered partial clone.

The primary checkout is a ``--filter=blob:none`` clone, so its origin carries
``remote.origin.promisor`` and ``remote.origin.partialclonefilter``. The
credential-free file import must accept exactly those keys, keep refusing every
other remote/url key, and never lazily fetch a missing promisor object.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.orchestration import execution_safe_git as safe


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        # Fixture probes must not lazily fill the missing objects under test.
        ["git", "--no-lazy-fetch", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _commit(tree: Path, content: str) -> str:
    (tree / "file.txt").write_text(content)
    _git(tree, "add", "file.txt")
    _git(tree, "commit", "-m", content.strip())
    return _git(tree, "rev-parse", "HEAD")


def _blob(tree: Path, commit: str) -> str:
    return _git(tree, "rev-parse", f"{commit}:file.txt")


def _missing(primary: Path) -> set[str]:
    out = _git(primary, "rev-list", "--objects", "--missing=print", "--all")
    return {line[1:] for line in out.splitlines() if line.startswith("?")}


@pytest.fixture
def partial_clone(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Fixture")
    _git(source, "config", "user.email", "fixture@example.invalid")
    old = _commit(source, "old\n")
    _commit(source, "current\n")
    origin = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(source), str(origin))
    _git(origin, "config", "uploadpack.allowFilter", "true")
    primary = tmp_path / "primary"
    _git(tmp_path, "clone", "--no-checkout", "--filter=blob:none", origin.as_uri(), str(primary))
    assert _git(primary, "config", "remote.origin.promisor") == "true"
    assert _git(primary, "config", "remote.origin.partialclonefilter") == "blob:none"
    assert _blob(source, old) in _missing(primary), "fixture is not a real partial clone"
    # A new upstream commit needs an object transfer; a stale tracking ref needs pruning.
    _git(source, "remote", "add", "origin", str(origin))
    new = _commit(source, "new\n")
    _git(source, "push", "origin", "HEAD:main")
    _git(primary, "update-ref", "refs/remotes/origin/gone", old)
    # Any non-empty credential list selects the isolated transfer/import path.
    monkeypatch.setattr(safe, "verification_credentials", lambda remote: ["credential.helper="])
    return source, primary, old, new


def _fetch(primary: Path):
    return safe.run_git(["fetch", "--no-tags", "origin", "--prune"], cwd=primary, profile="remote",
                        capture_output=True, text=True, timeout=30)


def test_partial_clone_origin_fetch_imports_without_lazy_fetch(partial_clone, monkeypatch):
    source, primary, old, new = partial_clone
    real_run = subprocess.run
    imports = []

    def import_hook(argv, **kwargs):
        if "fetch" in argv and any(arg.startswith("file://") for arg in argv):
            imports.append(kwargs["env"])
        return real_run(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", import_hook)
    result = _fetch(primary)
    assert not isinstance(result, safe.GitRefusal), result.code
    assert result.returncode == 0, result.stderr
    assert len(imports) == 1
    assert imports[0]["GIT_ALLOW_PROTOCOL"] == "file" and imports[0]["GIT_NO_LAZY_FETCH"] == "1"
    assert _git(primary, "rev-parse", "refs/remotes/origin/main") == new
    assert _git(primary, "rev-parse", "FETCH_HEAD^{commit}") == new
    assert not _git(primary, "for-each-ref", "refs/remotes/origin/gone")
    # The default origin filter is not applied to the anonymous import, and
    # the previously filtered blob was not lazily fetched.
    missing = _missing(primary)
    assert _blob(source, new) not in missing
    assert _blob(source, old) in missing


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("remote.origin.uploadpack", "git-upload-pack"),
        ("remote.origin.pushurl", "https://example.invalid/push.git"),
        ("remote.upstream.url", "https://example.invalid/upstream.git"),
        ("url.https://example.invalid/.insteadOf", "unused:"),
    ],
)
def test_partial_clone_keeps_other_remote_config_refusals(partial_clone, key, value):
    _source, primary, old, _new = partial_clone
    before = _git(primary, "rev-parse", "refs/remotes/origin/main")
    _git(primary, "config", key, value)
    result = _fetch(primary)
    assert isinstance(result, safe.GitRefusal) and result.code == "remote_import_config_unsupported"
    assert _git(primary, "rev-parse", "refs/remotes/origin/main") == before
    assert _git(primary, "rev-parse", "refs/remotes/origin/gone") == old
