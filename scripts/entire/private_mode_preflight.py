"""Prove the private Entire boundary before prompt-bearing native recall."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

try:
    from scripts.entire.validate_checkpoint_routing import validate
except ModuleNotFoundError:  # Direct script execution from the repository root.
    from validate_checkpoint_routing import validate

PINNED_VERSION = "0.8.42"
CHECKPOINT_REF = "refs/heads/entire/checkpoints/v1"
SOURCE_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"

Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def _run(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
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
    checks["pinned_cli"] = version.returncode == 0 and f"Entire CLI {PINNED_VERSION}" in version.stdout

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
    checks["entire_authenticated"] = auth.returncode == 0

    mirrors = _load_json(
        _invoke(
            runner,
            (
                "entire",
                "repo",
                "mirror",
                "list",
                "--name",
                "learn-ukrainian",
                "--json",
            ),
            root,
        )
    )
    mirror_rows = mirrors if isinstance(mirrors, list) else []
    private_mirror = next(
        (
            row
            for row in mirror_rows
            if isinstance(row, dict) and f"{row.get('owner')}/{row.get('repo')}" == checkpoint_repo
        ),
        None,
    )
    source_mirror = next(
        (
            row
            for row in mirror_rows
            if isinstance(row, dict) and f"{row.get('owner')}/{row.get('repo')}" == SOURCE_REPOSITORY
        ),
        None,
    )
    checks["private_mirror_ready"] = bool(
        private_mirror and private_mirror.get("isPrivate") is True and private_mirror.get("status") == "ready"
    )
    checks["source_mirror_ready"] = bool(source_mirror and source_mirror.get("status") == "ready")

    def _mirror_principals(repository: str, mirror: dict[str, Any] | None) -> Any:
        if not mirror or not isinstance(mirror.get("clusterHost"), str):
            return None
        return _load_json(
            _invoke(
                runner,
                (
                    "entire",
                    "repo",
                    "mirror",
                    "collaborators",
                    "list",
                    f"github.com/{repository}",
                    mirror["clusterHost"],
                    "--json",
                ),
                root,
            )
        )

    def _normalize_principals(value: Any) -> list[dict[str, Any]] | None:
        if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
            return None
        return [{"handle": row.get("handle"), "role": row.get("role")} for row in value]

    if checks["private_mirror_ready"]:
        private_principals = _normalize_principals(_mirror_principals(checkpoint_repo, private_mirror))
        checks["checkpoint_mirror_access_private"] = private_principals == expected_principals
    if checks["source_mirror_ready"]:
        source_principals = _normalize_principals(_mirror_principals(SOURCE_REPOSITORY, source_mirror))
        checks["source_mirror_access_private"] = source_principals == expected_principals

    issues.extend(f"{name}_failed" for name, passed in checks.items() if not passed)
    return {
        "schema": "entire-private-preflight.v1",
        "ready": not issues,
        "checks": checks,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify private Entire routing without reading session bodies.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    receipt = preflight(args.repo_root)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
