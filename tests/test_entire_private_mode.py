from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from scripts.entire.private_mode_preflight import preflight
from scripts.entire.validate_checkpoint_routing import EXPECTED_PRIVATE_RECALL


def _write_config(root: Path) -> None:
    entire = root / ".entire"
    entire.mkdir()
    (entire / "settings.json").write_text(
        json.dumps(
            {
                "strategy_options": {
                    "checkpoint_remote": {
                        "provider": "github",
                        "repo": "learn-ukrainian/entire-checkpoints-private",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (entire / "phase05-allowlist.json").write_text(
        json.dumps({"checkpoint_endpoints": [{"github_repo": "learn-ukrainian/entire-checkpoints-private"}]}),
        encoding="utf-8",
    )
    (entire / "private-recall.json").write_text(
        json.dumps(EXPECTED_PRIVATE_RECALL),
        encoding="utf-8",
    )


def _completed(command: Sequence[str], stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(list(command), returncode, stdout, "")


def _healthy_runner(command: Sequence[str], _cwd: Path):
    key = tuple(command)
    if key == ("entire", "version"):
        return _completed(command, "Entire CLI 0.8.42\n")
    if key[:4] == ("gh", "repo", "view", "learn-ukrainian/entire-checkpoints-private"):
        return _completed(command, '{"isPrivate":true,"visibility":"PRIVATE"}\n')
    if key == ("git", "ls-remote", "--heads", "origin", "entire/*"):
        return _completed(command)
    if key[:4] == ("git", "ls-remote", "--heads", "https://github.com/learn-ukrainian/entire-checkpoints-private.git"):
        return _completed(command, "abc\trefs/heads/entire/checkpoints/v1\n")
    if key == ("entire", "auth", "status"):
        return _completed(command, "logged in\n")
    if key[:5] == ("entire", "repo", "mirror", "list", "--name"):
        return _completed(
            command,
            json.dumps(
                [
                    {
                        "clusterHost": "aws-eu-central-1.entire.io",
                        "owner": "learn-ukrainian",
                        "repo": "entire-checkpoints-private",
                        "isPrivate": True,
                        "status": "ready",
                    },
                    {
                        "clusterHost": "aws-eu-central-1.entire.io",
                        "owner": "learn-ukrainian",
                        "repo": "learn-ukrainian.github.io",
                        "status": "ready",
                    },
                ]
            ),
        )
    if key[:6] == (
        "entire",
        "repo",
        "mirror",
        "collaborators",
        "list",
        "github.com/learn-ukrainian/entire-checkpoints-private",
    ):
        return _completed(
            command,
            '[{"handle":"github:krisztiankoos","role":"writer"}]',
        )
    if key[:6] == (
        "entire",
        "repo",
        "mirror",
        "collaborators",
        "list",
        "github.com/learn-ukrainian/learn-ukrainian.github.io",
    ):
        return _completed(
            command,
            '[{"handle":"github:krisztiankoos","role":"writer"}]',
        )
    raise AssertionError(f"unexpected command: {key}")


def test_private_mode_preflight_accepts_the_full_private_boundary(tmp_path: Path) -> None:
    _write_config(tmp_path)

    receipt = preflight(tmp_path, runner=_healthy_runner)

    assert receipt["ready"] is True
    assert receipt["issues"] == []
    assert all(receipt["checks"].values())
    assert "output" not in json.dumps(receipt)


def test_private_mode_preflight_fails_closed_without_private_visibility(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def public_runner(command: Sequence[str], cwd: Path):
        if tuple(command[:4]) == (
            "gh",
            "repo",
            "view",
            "learn-ukrainian/entire-checkpoints-private",
        ):
            return _completed(command, '{"isPrivate":false,"visibility":"PUBLIC"}\n')
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=public_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["checkpoint_repository_private"] is False
    assert receipt["issues"] == ["checkpoint_repository_private_failed"]


def test_private_mode_preflight_fails_closed_when_public_refs_exist(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def leaked_ref_runner(command: Sequence[str], cwd: Path):
        if tuple(command) == (
            "git",
            "ls-remote",
            "--heads",
            "origin",
            "entire/*",
        ):
            return _completed(command, "abc\trefs/heads/entire/checkpoints/v1\n")
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=leaked_ref_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["public_origin_clean"] is False
    assert receipt["issues"] == ["public_origin_clean_failed"]


def test_private_mode_preflight_fails_closed_on_version_drift(tmp_path: Path) -> None:
    _write_config(tmp_path)

    def drifted_runner(command: Sequence[str], cwd: Path):
        if tuple(command) == ("entire", "version"):
            return _completed(command, "Entire CLI 0.9.0\n")
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=drifted_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["pinned_cli"] is False
    assert receipt["issues"] == ["pinned_cli_failed"]


def test_private_mode_preflight_returns_body_free_failure_on_command_timeout(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def timeout_runner(command: Sequence[str], cwd: Path):
        if tuple(command) == ("entire", "version"):
            raise subprocess.TimeoutExpired(command, timeout=30)
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=timeout_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["pinned_cli"] is False
    assert receipt["issues"] == ["pinned_cli_failed"]
    assert "output" not in json.dumps(receipt)


def test_private_mode_preflight_fails_closed_without_checkpoint_ref(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def missing_ref_runner(command: Sequence[str], cwd: Path):
        if tuple(command[:4]) == (
            "git",
            "ls-remote",
            "--heads",
            "https://github.com/learn-ukrainian/entire-checkpoints-private.git",
        ):
            return _completed(command)
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=missing_ref_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["private_checkpoint_ref"] is False
    assert receipt["issues"] == ["private_checkpoint_ref_failed"]


def test_private_mode_preflight_fails_closed_without_entire_auth(tmp_path: Path) -> None:
    _write_config(tmp_path)

    def unauthenticated_runner(command: Sequence[str], cwd: Path):
        if tuple(command) == ("entire", "auth", "status"):
            return _completed(command, returncode=1)
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=unauthenticated_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["entire_authenticated"] is False
    assert receipt["issues"] == ["entire_authenticated_failed"]


def test_private_mode_preflight_fails_closed_without_ready_mirror(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def syncing_mirror_runner(command: Sequence[str], cwd: Path):
        if tuple(command[:5]) == ("entire", "repo", "mirror", "list", "--name"):
            return _completed(
                command,
                json.dumps(
                    [
                        {
                            "clusterHost": "aws-eu-central-1.entire.io",
                            "owner": "learn-ukrainian",
                            "repo": "entire-checkpoints-private",
                            "isPrivate": True,
                            "status": "syncing",
                        },
                        {
                            "clusterHost": "aws-eu-central-1.entire.io",
                            "owner": "learn-ukrainian",
                            "repo": "learn-ukrainian.github.io",
                            "status": "ready",
                        },
                    ]
                ),
            )
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=syncing_mirror_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["private_mirror_ready"] is False
    assert receipt["issues"] == ["private_mirror_ready_failed"]


def test_private_mode_preflight_rejects_extra_source_mirror_access(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)

    def extra_collaborator_runner(command: Sequence[str], cwd: Path):
        if tuple(command[:6]) == (
            "entire",
            "repo",
            "mirror",
            "collaborators",
            "list",
            "github.com/learn-ukrainian/learn-ukrainian.github.io",
        ):
            return _completed(
                command,
                json.dumps(
                    [
                        {"handle": "github:krisztiankoos", "role": "writer"},
                        {"handle": "github:unexpected", "role": "reader"},
                    ]
                ),
            )
        return _healthy_runner(command, cwd)

    receipt = preflight(tmp_path, runner=extra_collaborator_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["source_mirror_access_private"] is False
    assert receipt["issues"] == ["source_mirror_access_private_failed"]
