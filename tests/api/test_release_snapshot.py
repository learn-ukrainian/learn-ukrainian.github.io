"""Deterministic tests for immutable API release snapshots."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from lu_machinery.api import release_snapshot
from lu_machinery.api import release_snapshot as installed_release_snapshot
from lu_machinery.common.git_context import sanitized_git_env
from lu_machinery.common.release_layout import MANIFEST_NAME
from lu_machinery.path_safety import safe_join

from tests.helpers.python import project_python
from tests.wait_helpers import wait_until

pytestmark = pytest.mark.reads_content

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = project_python()


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=True,
        env=sanitized_git_env(),
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def _release_test_sha(repo_root: Path) -> str:
    """Return HEAD, or an immutable commit for staged release-code changes."""
    head = _run_git(repo_root, "rev-parse", "HEAD")
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "HEAD", "--", "scripts", "schemas"],
        cwd=repo_root,
        check=False,
        env=sanitized_git_env(),
        timeout=30,
    )
    if staged.returncode == 0:
        return head
    if staged.returncode != 1:
        pytest.fail("could not inspect staged release-code changes")

    tree = _run_git(repo_root, "write-tree")
    environment = sanitized_git_env() | {
        "GIT_AUTHOR_NAME": "Release Snapshot Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
        "GIT_COMMITTER_NAME": "Release Snapshot Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
    }
    result = subprocess.run(
        ["git", "commit-tree", tree, "-p", head],
        cwd=repo_root,
        capture_output=True,
        check=True,
        env=environment,
        input="release snapshot staged test\n",
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def _create_snapshot_repo(tmp_path: Path, *, api_app: bool = False) -> tuple[Path, str]:
    repo_root = tmp_path / "live"
    (repo_root / "scripts" / "api").mkdir(parents=True)
    (repo_root / "schemas").mkdir()
    (repo_root / "scripts" / "__init__.py").write_text("", encoding="utf-8")
    (repo_root / "scripts" / "api" / "__init__.py").write_text("", encoding="utf-8")
    (repo_root / "schemas" / "example.json").write_text("{}\n", encoding="utf-8")
    if api_app:
        (repo_root / "scripts" / "api" / "marker.py").write_text(
            "def value() -> str:\n    return 'snapshot'\n",
            encoding="utf-8",
        )
        (repo_root / "scripts" / "api" / "main.py").write_text(
            "from fastapi import FastAPI\n"
            "from .marker import value\n"
            "app = FastAPI()\n"
            "@app.get('/value')\n"
            "def get_value():\n"
            "    return {'value': value()}\n",
            encoding="utf-8",
        )
    else:
        (repo_root / "scripts" / "api" / "marker.py").write_text("VALUE = 'one'\n", encoding="utf-8")

    for relative_name in release_snapshot.LIVE_DATA_PATHS:
        (repo_root / relative_name).mkdir(parents=True, exist_ok=True)

    _run_git(repo_root.parent, "init", repo_root.name)
    _run_git(repo_root, "config", "user.email", "test@example.invalid")
    _run_git(repo_root, "config", "user.name", "Release Snapshot Test")
    _run_git(repo_root, "add", "scripts", "schemas")
    _run_git(repo_root, "commit", "-m", "initial snapshot")
    return repo_root, _run_git(repo_root, "rev-parse", "HEAD")


def _next_sha(repo_root: Path) -> str:
    marker = repo_root / "scripts" / "api" / "marker.py"
    marker.write_text("VALUE = 'two'\n", encoding="utf-8")
    _run_git(repo_root, "add", str(marker.relative_to(repo_root)))
    _run_git(repo_root, "commit", "-m", "next snapshot")
    return _run_git(repo_root, "rev-parse", "HEAD")


@pytest.fixture
def release_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        yield listener


def _read_json(url: str, *, timeout: float = 0.5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _read_text(url: str, *, timeout: float = 0.5) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


@pytest.fixture()
def real_release_live_checkout(tmp_path: Path) -> tuple[Path, str]:
    """Real code and manifest, with a bounded live-data corpus (#10315).

    A shared no-checkout clone reuses local Git objects without copying the
    entire documentation corpus. Only runtime imports and the route inputs
    are materialized; the release still archives this worktree's actual code.
    """
    sha = _release_test_sha(PROJECT_ROOT)
    repo_root = tmp_path / "live"
    _run_git(tmp_path, "clone", "--shared", "--no-checkout", str(PROJECT_ROOT), str(repo_root))
    _run_git(
        repo_root,
        "checkout",
        sha,
        "--",
        "agents_extensions",
        "curriculum/l2-uk-en/curriculum.yaml",
        "site/src/content/docs/a1-v1/sounds-letters-and-hello.mdx",
    )
    for relative_name in release_snapshot.LIVE_DATA_PATHS:
        (repo_root / relative_name).mkdir(parents=True, exist_ok=True)
    return repo_root, sha


def test_safe_join_rejects_a_symlink_escape(tmp_path: Path) -> None:
    base = tmp_path / "base"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    (base / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="escapes"):
        safe_join(base, "escape", "secret.txt")


def test_safe_join_allows_declared_live_data_and_preserves_logical_path(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)

    path = safe_join(release_dir, "curriculum", "l2-uk-en", "a1")

    assert path == release_dir / "curriculum" / "l2-uk-en" / "a1"
    assert path.resolve() == repo_root / "curriculum" / "l2-uk-en" / "a1"


def test_safe_join_rejects_nested_undeclared_symlink_from_live_data(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo_root / "curriculum" / "escape").symlink_to(outside, target_is_directory=True)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)

    with pytest.raises(ValueError, match="escapes"):
        safe_join(release_dir, "curriculum", "escape", "secret.txt")


def test_safe_join_rejects_planted_manifest_live_data_escape(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    planted = repo_root / "curriculum" / "planted"
    planted.mkdir()
    (planted / MANIFEST_NAME).write_text("{}\n", encoding="utf-8")
    (planted / "curriculum").symlink_to(outside, target_is_directory=True)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)

    with pytest.raises(ValueError, match="escapes"):
        safe_join(release_dir, "curriculum", "planted", "curriculum", "secret.txt")


def test_safe_join_rejects_declared_live_data_parent_traversal(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)

    with pytest.raises(ValueError, match="Invalid path component"):
        safe_join(release_dir, "curriculum", "..", "secret.txt")


def test_real_release_serves_live_data_routers_with_logical_paths(
    tmp_path: Path, real_release_live_checkout: tuple[Path, str], release_listener
) -> None:
    """Boot a snapshot of this worktree and exercise each live-data route class."""
    repo_root, sha = real_release_live_checkout
    release_dir, _ = installed_release_snapshot.build_release(repo_root, sha)
    # Write after snapshot publication to prove these routes read live data,
    # while keeping discovery independent of the growing repository corpus.
    doc_path = "docs/research/release-live-data.md"
    html_path = "docs/research/release-live-data.html"
    (repo_root / "docs" / "research").mkdir()
    (repo_root / doc_path).write_text("# Live release data\n", encoding="utf-8")
    (repo_root / html_path).write_text("<title>Live release data</title>\n", encoding="utf-8")
    listener = release_listener
    port = listener.getsockname()[1]
    log_path = tmp_path / "release-api.log"
    # As lu_machinery.api.launchd_supervisor starts it: the snapshot is the product, the installed
    # release serves the app, and the shared-state primary is the live checkout the snapshot was
    # built from. This test process's own roots name neither.
    environment = {
        key: value
        for key, value in sanitized_git_env().items()
        if key not in ("LU_PRODUCT_ROOT", "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT")
    } | {
        "LU_PRODUCT_ROOT": str(release_dir),
        "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT": str(repo_root),
        "LEARN_UK_REPO_ROOT": str(repo_root),
        "GIT_DIR": _run_git(repo_root, "rev-parse", "--absolute-git-dir"),
        "GIT_WORK_TREE": str(repo_root),
        "PYTHONPATH": str(release_dir),
    }

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                str(VENV_PYTHON),
                "-m",
                "uvicorn",
                "lu_machinery.api.main:app",
                "--host",
                "127.0.0.1",
                "--fd",
                str(listener.fileno()),
            ],
            pass_fds=(listener.fileno(),),
            cwd=release_dir,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        listener.close()
        agent_url = f"http://127.0.0.1:{port}/api/agent/module/a1/people-around-me"
        try:
            def application_started() -> bool:
                lines = log_path.read_text(encoding="utf-8").splitlines(keepends=True)
                assert process.poll() is None, "release API exited during startup"
                return "INFO:     Application startup complete.\n" in lines

            try:
                wait_until(application_started, message="release API completing ASGI startup")
            except AssertionError as exc:
                pytest.fail(f"{exc}:\n{log_path.read_text(encoding='utf-8')}")

            deadline = time.monotonic() + 15
            while True:
                try:
                    agent_payload = _read_json(agent_url)
                    if agent_payload.get("key_paths"):
                        break
                except (urllib.error.URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    pytest.fail(f"release API did not become ready:\n{log_path.read_text(encoding='utf-8')}")
                time.sleep(0.05)

            curriculum_payload = _read_json(f"http://127.0.0.1:{port}/api/state/build-status", timeout=10)
            preparation_payload = _read_json(
                f"http://127.0.0.1:{port}/api/state/preparation/a1/sounds-letters-and-hello",
                timeout=10,
            )
            # The bounded live-data corpus is the proof this cold read is the
            # small discovery walk: the payload below lists only the two files
            # written above. The socket timeout is a hang guard.
            artifact_payload = _read_json(f"http://127.0.0.1:{port}/api/artifacts/html", timeout=10)
            docs_text = _read_text(f"http://127.0.0.1:{port}/files/{doc_path}", timeout=10)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    key_paths = agent_payload["key_paths"]
    assert curriculum_payload["tracks"]["a1-v1"]["total"] > 0
    assert preparation_payload["track"] == "a1-v1"
    assert preparation_payload["publication"]["source"]["path"].startswith("site/src/content/docs/a1-v1/")
    assert "data_checkout" not in preparation_payload["authority"]
    assert preparation_payload["authority"]["primary_checkout"]["role"] == "live_primary"
    assert len(preparation_payload["authority"]["primary_checkout"]["head_sha"]) == 40
    assert preparation_payload["authority"]["cwd_role"] == "other"
    assert preparation_payload["authority"]["service_code"]["mode"] == "release"
    assert key_paths["orchestration_dir"].startswith("curriculum/l2-uk-en/")
    assert not key_paths["orchestration_dir"].startswith(str(release_dir))
    assert {item["path"] for item in artifact_payload["artifacts"]} == {doc_path, html_path}
    assert all(not item["path"].startswith(str(release_dir)) for item in artifact_payload["artifacts"])
    assert docs_text == "# Live release data\n"


def test_trusted_join_validates_components_lexically(tmp_path: Path) -> None:
    """trusted_join keeps the lexical guards: no .., no absolute, no separators."""
    from lu_machinery.path_safety import trusted_join

    base = tmp_path / "root"
    base.mkdir()
    assert trusted_join(base, "a", "b.json") == Path(os.path.abspath(base / "a" / "b.json"))
    for bad in ("..", "a/../..", "/abs", "a\x00b", ""):
        with pytest.raises(ValueError):
            trusted_join(base, bad)


def _fake_git(
    monkeypatch: pytest.MonkeyPatch,
    script: str,
    popen_cls: type[subprocess.Popen[bytes]] = subprocess.Popen,
) -> list[subprocess.Popen[bytes]]:
    """Run ``script`` in a real child process in place of ``git archive``."""
    spawned: list[subprocess.Popen[bytes]] = []

    def popen(command: list[str], **kwargs: object) -> subprocess.Popen[bytes]:
        process = popen_cls([sys.executable, "-c", script], **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(release_snapshot.subprocess, "Popen", popen)
    return spawned


class _ExitsAfterTimedWait(subprocess.Popen):
    """The timed wait expires, and git exits on its own right after it."""

    kills = 0
    timed_out = False

    def wait(self, timeout: float | None = None) -> int:
        if not self.timed_out:
            self.timed_out = True
            os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOWAIT)  # exited, not yet reaped
            raise subprocess.TimeoutExpired(self.args, timeout or 0.0)
        return super().wait(timeout)

    def kill(self) -> None:
        type(self).kills += 1
        super().kill()


class _IgnoresKill(subprocess.Popen):
    """kill() is sent but git never goes away."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wait_timeouts: list[float | None] = []

    def kill(self) -> None:
        pass

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        return super().wait(timeout=timeout)


class _ExitsZeroOnKill(subprocess.Popen):
    """Deliver a handled signal so a real child exits zero after the deadline."""

    def kill(self) -> None:
        self.send_signal(signal.SIGTERM)
