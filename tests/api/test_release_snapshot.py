"""Deterministic tests for immutable API release snapshots."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts.api import release_snapshot
from scripts.common.release_layout import MANIFEST_NAME, is_release_root
from scripts.git_context import sanitized_git_env
from scripts.path_safety import safe_join

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Prefer the repo venv when present; fall back to the running interpreter so
# bare review worktrees (no .venv symlink) stay testable (cf. #4918, #4926).
VENV_PYTHON = (
    PROJECT_ROOT / ".venv" / "bin" / "python"
    if (PROJECT_ROOT / ".venv" / "bin" / "python").exists()
    else Path(sys.executable)
)


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=True,
        env=sanitized_git_env(),
        text=True,
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


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def _read_json(url: str, *, timeout: float = 0.5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _read_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=0.5) as response:
        return response.read().decode("utf-8")


def _provision_missing_live_data_roots(repo_root: Path) -> list[Path]:
    """Create ignored live-data directories absent from a clean worktree."""
    created: list[Path] = []
    for relative_name in release_snapshot.LIVE_DATA_PATHS:
        path = repo_root / relative_name
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    return created


def test_atomic_publish_keeps_previous_current_on_crash(tmp_path: Path) -> None:
    repo_root, old_sha = _create_snapshot_repo(tmp_path)
    old_release, _ = release_snapshot.build_release(repo_root, old_sha)
    new_sha = _next_sha(repo_root)

    class SimulatedCrash(BaseException):
        pass

    def crash_before_publish(_staging: Path) -> None:
        raise SimulatedCrash()

    with pytest.raises(SimulatedCrash):
        release_snapshot.build_release(repo_root, new_sha, before_publish=crash_before_publish)

    release_root = release_snapshot.releases_root(repo_root)
    assert (release_root / "current").resolve() == old_release
    assert (release_root / f".staging-{os.getpid()}").is_dir()
    assert not (release_root / new_sha).exists()


def test_release_reuse_is_idempotent_and_links_live_data(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    first_release, reused = release_snapshot.build_release(repo_root, sha)
    second_release, reused_again = release_snapshot.build_release(repo_root, sha)

    assert not reused
    assert reused_again
    assert second_release == first_release
    assert (first_release / "curriculum").is_symlink()
    assert (first_release / "tests" / "fixtures").is_symlink()
    assert [
        path.name
        for path in release_snapshot.releases_root(repo_root).iterdir()
        if path.is_dir() and not path.is_symlink()
    ] == [sha]


def test_running_release_keeps_serving_archived_code_after_checkout_mutation(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path, api_app=True)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)
    port = _free_port()
    environment = sanitized_git_env() | {
        "LEARN_UK_REPO_ROOT": str(repo_root),
        "GIT_DIR": str(repo_root / ".git"),
        "GIT_WORK_TREE": str(repo_root),
        "PYTHONPATH": str(release_dir),
    }
    process = subprocess.Popen(
        [
            str(VENV_PYTHON),
            "-m",
            "uvicorn",
            "scripts.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=release_dir,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                if _read_json(f"http://127.0.0.1:{port}/value") == {"value": "snapshot"}:
                    break
            except (urllib.error.URLError, TimeoutError):
                pass
            if time.monotonic() >= deadline:
                pytest.fail("release API did not become ready")
            time.sleep(0.05)

        (repo_root / "scripts" / "api" / "marker.py").write_text(
            "def value() -> str:\n    return 'mutated checkout'\n",
            encoding="utf-8",
        )
        assert _read_json(f"http://127.0.0.1:{port}/value") == {"value": "snapshot"}
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_git_service_environment_targets_live_checkout(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)
    (repo_root / "live-only.txt").write_text("dirty\n", encoding="utf-8")
    environment = sanitized_git_env() | {
        "LEARN_UK_REPO_ROOT": str(repo_root),
        "GIT_DIR": str(repo_root / ".git"),
        "GIT_WORK_TREE": str(repo_root),
    }

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=release_dir,
        env=environment,
        capture_output=True,
        check=True,
        text=True,
    )
    assert "?? live-only.txt" in result.stdout


def test_pruning_preserves_a_live_release_outside_the_newest_three(tmp_path: Path) -> None:
    repo_root, _sha = _create_snapshot_repo(tmp_path)
    releases_dir = release_snapshot.releases_root(repo_root)
    releases_dir.mkdir(parents=True)
    shas = [f"{index:040x}" for index in range(5)]
    release_dirs = []
    for index, sha in enumerate(shas):
        path = releases_dir / sha
        path.mkdir()
        os.utime(path, ns=(index + 1, index + 1))
        release_dirs.append(path)
    (releases_dir / "current").symlink_to(shas[-1], target_is_directory=True)

    listener = subprocess.Popen(
        [
            str(VENV_PYTHON),
            "-c",
            "import socket, time; server = socket.socket(); server.bind(('127.0.0.1', 0)); server.listen(); time.sleep(30)",
        ],
        cwd=release_dirs[0],
    )
    try:
        def lsof_for_live_listener(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                args=["lsof"],
                returncode=0,
                stdout=f"p{listener.pid}\nn{release_dirs[0]}\n",
                stderr="",
            )

        result = release_snapshot.prune_releases(repo_root, runner=lsof_for_live_listener)
    finally:
        listener.terminate()
        listener.wait(timeout=5)

    assert release_dirs[0].exists(), "a live process owns this old release"
    assert not release_dirs[1].exists()
    assert release_dirs[2].exists() and release_dirs[3].exists() and release_dirs[4].exists()
    assert shas[0] not in result.removed
    assert shas[1] in result.removed


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


def test_release_root_attestation_requires_release_layout(tmp_path: Path) -> None:
    repo_root, sha = _create_snapshot_repo(tmp_path)
    release_dir, _ = release_snapshot.build_release(repo_root, sha)
    fake_root = tmp_path / sha
    outside = tmp_path / "outside"
    fake_root.mkdir()
    outside.mkdir()
    (fake_root / MANIFEST_NAME).write_text("{}\n", encoding="utf-8")
    (fake_root / "curriculum").symlink_to(outside, target_is_directory=True)

    assert is_release_root(release_dir)
    assert not is_release_root(fake_root)
    with pytest.raises(ValueError, match="escapes"):
        safe_join(fake_root, "curriculum", "secret.txt")


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


def test_pruning_rechecks_current_release_before_each_deletion(tmp_path: Path) -> None:
    repo_root, _sha = _create_snapshot_repo(tmp_path)
    releases_dir = release_snapshot.releases_root(repo_root)
    releases_dir.mkdir(parents=True)
    shas = [f"{index:040x}" for index in range(5)]
    release_dirs = []
    for index, sha in enumerate(shas):
        path = releases_dir / sha
        path.mkdir()
        os.utime(path, ns=(index + 1, index + 1))
        release_dirs.append(path)
    current = releases_dir / "current"
    current.symlink_to(shas[-1], target_is_directory=True)

    calls = 0

    def lsof_that_switches_current(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        # The fourth sorted release is the first old candidate. Changing
        # current here verifies that prune reads it again before deleting.
        if calls == 4:
            current.unlink()
            current.symlink_to(shas[1], target_is_directory=True)
        return subprocess.CompletedProcess(args=["lsof"], returncode=0, stdout="", stderr="")

    result = release_snapshot.prune_releases(repo_root, runner=lsof_that_switches_current)

    assert calls == 5
    assert release_dirs[1].exists(), "the freshly current release must not be deleted"
    assert not release_dirs[0].exists()
    assert shas[0] in result.removed
    assert shas[1] not in result.removed


def test_real_release_serves_live_data_routers_with_logical_paths(tmp_path: Path) -> None:
    """Boot a snapshot of this worktree and exercise each live-data route class."""
    created_live_roots = _provision_missing_live_data_roots(PROJECT_ROOT)
    try:
        sha = _run_git(PROJECT_ROOT, "rev-parse", "HEAD")
        release_dir, _ = release_snapshot.build_release(PROJECT_ROOT, sha)
        port = _free_port()
        log_path = tmp_path / "release-api.log"
        environment = sanitized_git_env() | {
            "LEARN_UK_REPO_ROOT": str(PROJECT_ROOT),
            "GIT_DIR": _run_git(PROJECT_ROOT, "rev-parse", "--absolute-git-dir"),
            "GIT_WORK_TREE": str(PROJECT_ROOT),
            "PYTHONPATH": str(release_dir),
        }

        with log_path.open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                [
                    str(VENV_PYTHON),
                    "-m",
                    "uvicorn",
                    "scripts.api.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=release_dir,
                env=environment,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            agent_url = f"http://127.0.0.1:{port}/api/agent/module/a1/people-around-me"
            try:
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

                curriculum_payload = _read_json(f"http://127.0.0.1:{port}/api/blue/live-status")
                artifact_payload = _read_json(f"http://127.0.0.1:{port}/api/artifacts/html", timeout=10)
                docs_text = _read_text(
                    "http://127.0.0.1:"
                    f"{port}/files/docs/research/2026-06-12-atlas-synonym-sense-fix-report.md"
                )
            finally:
                process.terminate()
                process.wait(timeout=5)

        key_paths = agent_payload["key_paths"]
        assert curriculum_payload["a1"]["module_count"] >= 0
        assert key_paths["orchestration_dir"].startswith("curriculum/l2-uk-en/")
        assert not key_paths["orchestration_dir"].startswith(str(release_dir))
        assert artifact_payload["artifacts"]
        assert all(not item["path"].startswith(str(release_dir)) for item in artifact_payload["artifacts"])
        assert docs_text.startswith("# Word Atlas Synonym Sense Fix Report")
    finally:
        for path in reversed(created_live_roots):
            shutil.rmtree(path)
