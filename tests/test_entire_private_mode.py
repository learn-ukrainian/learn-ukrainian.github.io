from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from scripts.entire import private_mode_preflight
from scripts.entire.private_mode_preflight import PINNED_VERSION, preflight
from scripts.entire.validate_checkpoint_routing import EXPECTED_PRIVATE_RECALL
from scripts.entire_context.provider import REQUIRED_ENTIRE_VERSION

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_REPO = "learn-ukrainian/entire-checkpoints-private"
SOURCE_REPO = "learn-ukrainian/learn-ukrainian.github.io"
OPERATOR_GRANT = {
    "granteeId": "acct-operator",
    "granteeName": "github:krisztiankoos",
    "role": "writer",
    "source": "github",
}


def _write_config(root: Path) -> None:
    entire = root / ".entire"
    entire.mkdir()
    (entire / "settings.json").write_text(
        json.dumps({"strategy_options": {"checkpoint_remote": {"provider": "github", "repo": CHECKPOINT_REPO}}}),
        encoding="utf-8",
    )
    (entire / "phase05-allowlist.json").write_text(
        json.dumps({"checkpoint_endpoints": [{"github_repo": CHECKPOINT_REPO}]}),
        encoding="utf-8",
    )
    (entire / "private-recall.json").write_text(
        json.dumps(EXPECTED_PRIVATE_RECALL),
        encoding="utf-8",
    )


def _completed(command: Sequence[str], stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(list(command), returncode, stdout, "")


def _mirror_view(repository: str, *, private: bool, status: str = "ready") -> str:
    # `entire repo view /gh/<owner>/<repo> --json` in 0.11.5: one directory row.
    return json.dumps(
        {
            "repo": f"/gh/{repository}",
            "private": private,
            "status": status,
            "placements": [
                {
                    "cluster": "cluster.example",
                    "clusterSlug": "cluster-eu",
                    "jurisdiction": "eu",
                    "status": status,
                }
            ],
        }
    )


def _status(**overrides: object) -> str:
    payload = {
        "enabled": True,
        "agents": ["Claude Code"],
        "active_sessions": [],
        "checkpoint_sync_remote": CHECKPOINT_REPO,
        "checkpoint_sync_remote_source": "dedicated",
    }
    payload.update(overrides)
    return json.dumps({key: value for key, value in payload.items() if value is not None})


def _entire_0115_runner(command: Sequence[str], _cwd: Path):
    """Answer like the Entire 0.11.5 CLI does for the commands the preflight runs.

    Argument vectors that 0.11.5 removed (canary #10846: `repo mirror
    collaborators list` prints usage and exits 1) are rejected the same way.
    """
    key = tuple(command)
    if key == ("entire", "version"):
        return _completed(command, "Entire CLI 0.11.5\nGo version: go1.27.1\nOS/Arch: linux/amd64\n")
    if key == ("entire", "status", "--json"):
        return _completed(command, _status())
    if key[:4] == ("gh", "repo", "view", CHECKPOINT_REPO):
        return _completed(command, '{"isPrivate":true,"visibility":"PRIVATE"}\n')
    if key == ("git", "ls-remote", "--heads", "origin", "entire/*"):
        return _completed(command)
    if key[:4] == ("git", "ls-remote", "--heads", f"https://github.com/{CHECKPOINT_REPO}.git"):
        return _completed(command, "abc\trefs/heads/entire/checkpoints/v1\n")
    if key == ("entire", "auth", "status"):
        return _completed(command, "● Logged in\n")
    if key == ("entire", "repo", "view", f"/gh/{CHECKPOINT_REPO}", "--json"):
        return _completed(command, _mirror_view(CHECKPOINT_REPO, private=True))
    if key == ("entire", "repo", "view", f"/gh/{SOURCE_REPO}", "--json"):
        return _completed(command, _mirror_view(SOURCE_REPO, private=False))
    if key in {
        ("entire", "repo", "grant", "list", f"/gh/{CHECKPOINT_REPO}", "--json"),
        ("entire", "repo", "grant", "list", f"/gh/{SOURCE_REPO}", "--json"),
    }:
        return _completed(command, json.dumps([OPERATOR_GRANT]))
    if key[:2] == ("entire", "repo"):
        return _completed(command, "Usage:\n  entire [flags]\n", returncode=1)
    raise AssertionError(f"unexpected command: {key}")


def _with(overrides: dict[tuple[str, ...], subprocess.CompletedProcess[str]]):
    def runner(command: Sequence[str], cwd: Path):
        return overrides.get(tuple(command)) or _entire_0115_runner(command, cwd)

    return runner


def test_entire_pins_agree_on_0_11_5() -> None:
    recall = json.loads((ROOT / ".entire" / "private-recall.json").read_text(encoding="utf-8"))
    installer = (ROOT / "scripts" / "entire" / "install_fleet_external_agent.sh").read_text(encoding="utf-8")

    assert PINNED_VERSION == "0.11.5"
    assert REQUIRED_ENTIRE_VERSION == PINNED_VERSION
    assert EXPECTED_PRIVATE_RECALL["required_cli_version"] == PINNED_VERSION
    assert recall["required_cli_version"] == PINNED_VERSION
    assert '!= "Entire CLI 0.11.5" ]]' in installer


def test_private_mode_preflight_accepts_the_full_private_boundary(tmp_path: Path) -> None:
    _write_config(tmp_path)
    calls: list[tuple[str, ...]] = []

    def recording_runner(command: Sequence[str], cwd: Path):
        calls.append(tuple(command))
        return _entire_0115_runner(command, cwd)

    receipt = preflight(tmp_path, runner=recording_runner)

    assert receipt["ready"] is True
    assert receipt["issues"] == []
    assert all(receipt["checks"].values())
    assert set(receipt["checks"]) == {
        "routing_allowlist",
        "pinned_cli",
        "checkpoint_route_private",
        "checkpoint_repository_private",
        "public_origin_clean",
        "private_checkpoint_ref",
        "entire_authenticated",
        "private_mirror_ready",
        "source_mirror_ready",
        "checkpoint_mirror_access_private",
        "source_mirror_access_private",
    }
    assert "output" not in json.dumps(receipt)
    assert ("entire", "repo", "grant", "list", f"/gh/{CHECKPOINT_REPO}", "--json") in calls
    assert ("entire", "repo", "view", f"/gh/{SOURCE_REPO}", "--json") in calls
    assert not any(call[:4] == ("entire", "repo", "mirror", "collaborators") for call in calls)
    assert not any(call[:4] == ("entire", "repo", "mirror", "list") for call in calls)


def test_mirror_helpers_use_the_0_11_5_forge_reference() -> None:
    assert private_mode_preflight.mirror_view_args(SOURCE_REPO) == ("repo", "view", f"/gh/{SOURCE_REPO}", "--json")
    row = json.loads(_mirror_view(SOURCE_REPO, private=False))
    assert private_mode_preflight.mirror_row(row, SOURCE_REPO) == row
    assert private_mode_preflight.mirror_row(row, CHECKPOINT_REPO) is None
    assert private_mode_preflight.mirror_row([row], SOURCE_REPO) is None


def test_private_mode_preflight_fails_closed_without_private_visibility(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with(
        {
            ("gh", "repo", "view", CHECKPOINT_REPO, "--json", "isPrivate,visibility"): _completed(
                [], '{"isPrivate":false,"visibility":"PUBLIC"}\n'
            )
        }
    )

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["checkpoint_repository_private"] is False
    assert receipt["issues"] == ["checkpoint_repository_private_failed"]


def test_private_mode_preflight_fails_closed_when_public_refs_exist(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with(
        {
            ("git", "ls-remote", "--heads", "origin", "entire/*"): _completed(
                [], "abc\trefs/heads/entire/checkpoints/v1\n"
            )
        }
    )

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["public_origin_clean"] is False
    assert receipt["issues"] == ["public_origin_clean_failed"]


@pytest.mark.parametrize(
    "version_stdout",
    [
        "Entire CLI 0.8.42\nGo version: go1.26.4\n",
        "Entire CLI 0.11.4\n",
        "Entire CLI 0.11.50\n",
        "Entire CLI 0.11.5-nightly.20261015\n",
        "Go version: go1.27.1\nEntire CLI 0.11.5\n",
        "",
    ],
)
def test_private_mode_preflight_fails_closed_on_version_mismatch(tmp_path: Path, version_stdout: str) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "version"): _completed([], version_stdout)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["pinned_cli"] is False
    assert receipt["issues"] == ["pinned_cli_failed"]
    # Version-specific status fields are not interpreted for an unpinned CLI.
    assert "checkpoint_route_private" not in receipt["checks"]


def test_private_mode_preflight_fails_closed_when_version_command_fails(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "version"): _completed([], "Entire CLI 0.11.5\n", returncode=1)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["issues"] == ["pinned_cli_failed"]


@pytest.mark.parametrize(
    "status_stdout",
    [
        # S3 canary: an origin owned by someone else makes 0.11.5 ignore
        # checkpoint_remote and elect origin for checkpoint pushes.
        _status(
            checkpoint_sync_remote="origin",
            checkpoint_sync_remote_source="default",
            checkpoint_remote_ignored=CHECKPOINT_REPO,
            checkpoint_remote_ignored_verdict="disproved",
        ),
        _status(checkpoint_sync_remote="learn-ukrainian/other-store"),
        _status(checkpoint_remote_ignored=CHECKPOINT_REPO),
        _status(checkpoint_sync_error="checkpoint_push_remote has no configured fetch URL"),
        _status(checkpoint_sync_remote=None, checkpoint_sync_remote_source=None),
        "not json",
        "[]",
    ],
)
def test_private_mode_preflight_requires_the_dedicated_checkpoint_route(tmp_path: Path, status_stdout: str) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "status", "--json"): _completed([], status_stdout)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["checkpoint_route_private"] is False
    assert receipt["issues"] == ["checkpoint_route_private_failed"]


def test_private_mode_preflight_returns_body_free_failure_on_command_timeout(tmp_path: Path) -> None:
    _write_config(tmp_path)

    def timeout_runner(command: Sequence[str], cwd: Path):
        if tuple(command) == ("entire", "version"):
            raise subprocess.TimeoutExpired(command, timeout=30)
        return _entire_0115_runner(command, cwd)

    receipt = preflight(tmp_path, runner=timeout_runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["pinned_cli"] is False
    assert receipt["issues"] == ["pinned_cli_failed"]
    assert "output" not in json.dumps(receipt)


def test_private_mode_preflight_fails_closed_without_checkpoint_ref(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with(
        {("git", "ls-remote", "--heads", f"https://github.com/{CHECKPOINT_REPO}.git", "entire/*"): _completed([])}
    )

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["private_checkpoint_ref"] is False
    assert receipt["issues"] == ["private_checkpoint_ref_failed"]


def test_private_mode_preflight_fails_closed_without_entire_auth(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "auth", "status"): _completed([], returncode=1)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["entire_authenticated"] is False
    assert receipt["issues"] == ["entire_authenticated_failed"]


@pytest.mark.parametrize(
    "auth_stdout",
    [
        # Entire 0.11.5 logged out (canary #10846), exit 0.
        "○ Not logged in\nRun 'entire login' to authenticate.\n",
        "Not logged in.\nRun 'entire login' to authenticate.\n",
        "Not logged in.\n",
        "NOT LOGGED IN.\n",
        "Run 'entire login' to authenticate.\n",
        "RUN 'ENTIRE LOGIN' TO AUTHENTICATE.\n",
    ],
)
def test_private_mode_preflight_rejects_logged_out_success(tmp_path: Path, auth_stdout: str) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "auth", "status"): _completed([], auth_stdout)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["checks"]["entire_authenticated"] is False
    assert receipt["ready"] is False
    assert receipt["issues"] == ["entire_authenticated_failed"]
    serialized = json.dumps(receipt).lower()
    assert "not logged in" not in serialized
    assert "entire login" not in serialized


@pytest.mark.parametrize(
    "view_stdout",
    [
        _mirror_view(CHECKPOINT_REPO, private=True, status="processing"),
        _mirror_view(CHECKPOINT_REPO, private=True, status="mixed"),
        _mirror_view(CHECKPOINT_REPO, private=False),
        # `repo view` returns the first filter match; another repository is not this mirror.
        _mirror_view("learn-ukrainian/entire-checkpoints-private-old", private=True),
        # The 0.8.42 `repo mirror list` row shape is not a 0.11.5 `repo view` row.
        json.dumps(
            {
                "clusterHost": "cluster.example",
                "owner": "learn-ukrainian",
                "repo": "entire-checkpoints-private",
                "isPrivate": True,
                "status": "ready",
            }
        ),
    ],
)
def test_private_mode_preflight_fails_closed_without_ready_private_mirror(tmp_path: Path, view_stdout: str) -> None:
    _write_config(tmp_path)
    runner = _with({("entire", "repo", "view", f"/gh/{CHECKPOINT_REPO}", "--json"): _completed([], view_stdout)})

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["private_mirror_ready"] is False
    assert receipt["issues"] == ["private_mirror_ready_failed"]
    assert "checkpoint_mirror_access_private" not in receipt["checks"]


@pytest.mark.parametrize(
    "grant_rows",
    [
        [
            OPERATOR_GRANT,
            {**OPERATOR_GRANT, "granteeId": "acct-other", "granteeName": "github:unexpected", "role": "reader"},
        ],
        [{**OPERATOR_GRANT, "role": "admin"}],
        # A grant row from anything but the GitHub mirror is not this ACL.
        [{**OPERATOR_GRANT, "source": "direct", "granteeType": "account"}],
        # 0.8.42 spelling: `handle` was renamed to `granteeName`.
        [{"handle": "github:krisztiankoos", "role": "writer"}],
        [],
    ],
)
def test_private_mode_preflight_rejects_unexpected_source_mirror_access(tmp_path: Path, grant_rows: list) -> None:
    _write_config(tmp_path)
    runner = _with(
        {("entire", "repo", "grant", "list", f"/gh/{SOURCE_REPO}", "--json"): _completed([], json.dumps(grant_rows))}
    )

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["source_mirror_access_private"] is False
    assert receipt["issues"] == ["source_mirror_access_private_failed"]


def test_private_mode_preflight_fails_closed_when_grant_list_is_rejected(tmp_path: Path) -> None:
    _write_config(tmp_path)
    runner = _with(
        {
            ("entire", "repo", "grant", "list", f"/gh/{CHECKPOINT_REPO}", "--json"): _completed(
                [], "Usage:\n  entire [flags]\n", returncode=1
            )
        }
    )

    receipt = preflight(tmp_path, runner=runner)

    assert receipt["ready"] is False
    assert receipt["checks"]["checkpoint_mirror_access_private"] is False
    assert receipt["issues"] == ["checkpoint_mirror_access_private_failed"]
