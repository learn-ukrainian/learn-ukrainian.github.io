"""Prove the private Entire boundary before prompt-bearing native recall."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client

try:
    from scripts.entire.validate_checkpoint_routing import validate
except ModuleNotFoundError:  # Direct script execution from the repository root.
    from validate_checkpoint_routing import validate

PINNED_VERSION = "0.11.5"
CHECKPOINT_REF = "refs/heads/entire/checkpoints/v1"
SOURCE_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
# `entire status --json` names the route checkpoints take; "dedicated" means the
# configured checkpoint_remote, not a git remote of this checkout.
DEDICATED_ROUTE = "dedicated"

Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def mirror_ref(repository: str) -> str:
    """Return the forge-qualified reference Entire uses for a GitHub mirror."""
    return f"/gh/{repository}"


def mirror_view_args(repository: str) -> tuple[str, ...]:
    """Return the `entire` arguments that look up one GitHub mirror by exact name."""
    return ("repo", "view", mirror_ref(repository), "--json")


def mirror_row(payload: Any, repository: str) -> dict[str, Any] | None:
    """Return the `repo view --json` row only when it describes ``repository``."""
    if isinstance(payload, dict) and payload.get("repo") == mirror_ref(repository):
        return payload
    return None


def _run(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return github_client.run(
        list(command),
        cwd=cwd,
        fresh=True, capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _load_json(result: subprocess.CompletedProcess[str]) -> Any:
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return None


def _invoke(runner: Runner, command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return runner(command, cwd)
    except (OSError, subprocess.SubprocessError):
        return subprocess.CompletedProcess(list(command), 127, "", "")


def preflight(root: Path, *, runner: Runner = _run) -> dict[str, Any]:
    """Return a body-free receipt; never include command output or local paths."""
    root = root.resolve()
    checks: dict[str, bool] = {}
    issues: list[str] = []

    routing_error = validate(root)
    checks["routing_allowlist"] = routing_error is None
    if routing_error is not None:
        issues.append("routing_allowlist_failed")
        return {
            "schema": "entire-private-preflight.v1",
            "ready": False,
            "checks": checks,
            "issues": issues,
        }

    settings = json.loads((root / ".entire/settings.json").read_text(encoding="utf-8"))
    policy = json.loads((root / ".entire/private-recall.json").read_text(encoding="utf-8"))
    checkpoint_repo = settings["strategy_options"]["checkpoint_remote"]["repo"]
    expected_principals = policy["entire_access_principals"]

    version = _invoke(runner, ("entire", "version"), root)
    # Exact first line: a substring match would also admit e.g. 0.11.50.
    version_line = next(iter(version.stdout.splitlines()), "").strip()
    checks["pinned_cli"] = version.returncode == 0 and version_line == f"Entire CLI {PINNED_VERSION}"
    if checks["pinned_cli"]:
        status = _load_json(_invoke(runner, ("entire", "status", "--json"), root))
        checks["checkpoint_route_private"] = bool(
            isinstance(status, dict)
            and status.get("checkpoint_sync_remote_source") == DEDICATED_ROUTE
            and status.get("checkpoint_sync_remote") == checkpoint_repo
            and not status.get("checkpoint_remote_ignored")
            and not status.get("checkpoint_sync_error")
        )

    private_repo = _load_json(
        _invoke(
            runner,
            (
                "gh",
                "repo",
                "view",
                checkpoint_repo,
                "--json",
                "isPrivate,visibility",
            ),
            root,
        )
    )
    checks["checkpoint_repository_private"] = bool(
        isinstance(private_repo, dict)
        and private_repo.get("isPrivate") is True
        and private_repo.get("visibility") == "PRIVATE"
    )

    public_refs = _invoke(runner, ("git", "ls-remote", "--heads", "origin", "entire/*"), root)
    checks["public_origin_clean"] = public_refs.returncode == 0 and not public_refs.stdout.strip()

    private_refs = _invoke(
        runner,
        (
            "git",
            "ls-remote",
            "--heads",
            f"https://github.com/{checkpoint_repo}.git",
            "entire/*",
        ),
        root,
    )
    private_ref_names = {line.split("\t", 1)[1] for line in private_refs.stdout.splitlines() if "\t" in line}
    checks["private_checkpoint_ref"] = private_refs.returncode == 0 and CHECKPOINT_REF in private_ref_names

    auth = _invoke(runner, ("entire", "auth", "status"), root)
    auth_stdout = auth.stdout.lower()
    checks["entire_authenticated"] = auth.returncode == 0 and not any(
        marker in auth_stdout for marker in ("not logged in", "run 'entire login'")
    )

    private_mirror = mirror_row(
        _load_json(_invoke(runner, ("entire", *mirror_view_args(checkpoint_repo)), root)),
        checkpoint_repo,
    )
    source_mirror = mirror_row(
        _load_json(_invoke(runner, ("entire", *mirror_view_args(SOURCE_REPOSITORY)), root)),
        SOURCE_REPOSITORY,
    )
    checks["private_mirror_ready"] = bool(
        private_mirror and private_mirror.get("private") is True and private_mirror.get("status") == "ready"
    )
    checks["source_mirror_ready"] = bool(source_mirror and source_mirror.get("status") == "ready")

    def _mirror_principals(repository: str) -> Any:
        return _load_json(
            _invoke(runner, ("entire", "repo", "grant", "list", mirror_ref(repository), "--json"), root)
        )

    def _normalize_principals(value: Any) -> list[dict[str, Any]] | None:
        # A GitHub mirror's grant rows carry source "github"; any other row is
        # not the mirror ACL this check is about.
        if not isinstance(value, list) or not all(
            isinstance(row, dict) and row.get("source") == "github" for row in value
        ):
            return None
        return [{"handle": row.get("granteeName"), "role": row.get("role")} for row in value]

    if checks["private_mirror_ready"]:
        private_principals = _normalize_principals(_mirror_principals(checkpoint_repo))
        checks["checkpoint_mirror_access_private"] = private_principals == expected_principals
    if checks["source_mirror_ready"]:
        source_principals = _normalize_principals(_mirror_principals(SOURCE_REPOSITORY))
        checks["source_mirror_access_private"] = source_principals == expected_principals

    issues.extend(f"{name}_failed" for name, passed in checks.items() if not passed)
    return {
        "schema": "entire-private-preflight.v1",
        "ready": not issues,
        "checks": checks,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify private Entire routing without reading session bodies.\n"
            "Use before native recall; this does not log in or configure mirrors."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: scripts/entire/private_mode_preflight.py --repo-root .\n"
            "Outputs: body-free JSON receipt on stdout; no files written.\n"
            "Exit codes: 0 = ready; 2 = preflight failed.\n"
            "Related: .entire/private-recall.json; Entire CLI 0.11.5; #6283, #10846."
        ),
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(),
        help="Repository to verify (default: current directory; example: .).",
    )
    args = parser.parse_args()
    receipt = preflight(args.repo_root)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
