"""Security-sensitive review paths approved for #9125.

Changed paths are authoritative; owned scope is a fallback before changes exist.
Git collection disables rename compaction so both names and deletions survive.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path

from scripts.common.repo_root import machinery_root
from scripts.review.target_resolution import TargetResolutionError, _run_git

# Machinery files are matched by their checkout-relative paths, which start with the
# machinery package's directory whatever it is called. The literal ``scripts/`` entries
# are product-repository files and stay where they are.
_MACHINERY = machinery_root().name

SECURITY_SENSITIVE_PATHS = (
    ".githooks/**",
    ".github/workflows/**",
    "agents_extensions/*/hooks/**",
    "agents_extensions/*/hooks*.json",
    "agents_extensions/*/settings*.json",
    "agents_extensions/*/config.toml",
    "agents_extensions/shared/session_streams/**",
    "start-*.sh",
    "run-dispatcher.sh",
    "services.sh",
    f"{_MACHINERY}/start-*.sh",
    f"{_MACHINERY}/session_start.sh",
    f"{_MACHINERY}/install_git_hooks.sh",
    f"{_MACHINERY}/launchers/**",
    f"{_MACHINERY}/launchd/**",
    f"{_MACHINERY}/lib/*.sh",
    f"{_MACHINERY}/lib/kimi_coding_oauth.py",
    f"{_MACHINERY}/hooks/**",
    f"{_MACHINERY}/guardrails/**",
    "scripts/lexical_sandbox.py",
    f"{_MACHINERY}/agent_runtime/**",
    f"{_MACHINERY}/session_supervisor/**",
    "scripts/delegate.py",
    f"{_MACHINERY}/dispatch.py",
    f"{_MACHINERY}/dispatcher/**",
    f"{_MACHINERY}/orchestration/dispatch_admission.py",
    f"{_MACHINERY}/api/delegate_router.py",
    f"{_MACHINERY}/opsec/**",
    f"{_MACHINERY}/secret_redactor.py",
    "scripts/audit/secret_scan_local.py",
    f"{_MACHINERY}/ci/secret_scan_scope.py",
    "scripts/ocr/_credentials.py",
    "packages/v4-runtime/src/learn_ukrainian_v4_runtime/credential_custody.py",
    f"{_MACHINERY}/review/*.py",
    "scripts/review/*.py",
    "scripts/review/receipts/**",
    "scripts/review/validate/**",
    "scripts/build/cf_preflight.py",
    f"{_MACHINERY}/publish/**",
    f"{_MACHINERY}/ai_agent_bridge/_review*.py",
    f"{_MACHINERY}/ai_agent_bridge/routing_guard.py",
    f"{_MACHINERY}/config/model_catalog.yaml",
    f"{_MACHINERY}/config/agent_runtime*.yaml",
    f"{_MACHINERY}/config/agent_fallback_substitutions.yaml",
)


def is_security_sensitive_change(changed_paths: Iterable[str], owned_paths: Iterable[str] = ()) -> bool:
    """Match actual changes, or conservative owned scope when no changes exist."""

    def normalized(path: str) -> str:
        while path.startswith("./"):
            path = path[2:]
        return path

    changed = tuple(changed_paths)
    if changed:
        return any(fnmatchcase(normalized(path), pattern) for path in changed for pattern in SECURITY_SENSITIVE_PATHS)
    for path in owned_paths:
        path = normalized(path).rstrip("/")
        if path in {"", "."}:
            return True
        directory = path + "/"
        for pattern in SECURITY_SENSITIVE_PATHS:
            # The inventory's first wildcard is always '*'. fnmatch lets it
            # cross '/', so it can absorb any descendant prefix before the
            # remaining literal suffix (e.g. scripts/lib/nested/run.sh).
            literal_prefix, wildcard, _suffix = pattern.partition("*")
            if (
                fnmatchcase(path, pattern)
                or pattern.startswith(directory)
                or (wildcard and directory.startswith(literal_prefix))
            ):
                return True
    return False


def effective_review_risk(
    requested: str, changed_paths: Iterable[str], owned_paths: Iterable[str] = (), *, profile: str = "code"
) -> str:
    """Raise security-sensitive code/infra targets to critical; preserve other risk."""
    if profile.strip().casefold() not in {"code", "infra"}:
        return requested
    return "critical" if is_security_sensitive_change(changed_paths, owned_paths) else requested


def git_changed_paths(repo_root: Path, base_sha: str, head_sha: str | None = None) -> tuple[str, ...]:
    """Read exact filenames, including both rename names, for a review diff.

    A missing head means the local tracked working tree versus HEAD. Untracked
    paths are already supplied by the local target and are unioned by the caller.
    """
    endpoints = [base_sha, head_sha] if head_sha is not None else [base_sha]
    if any(not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", sha) for sha in endpoints):
        raise TargetResolutionError("security review target_sha_invalid: expected full commit SHAs")
    try:
        proc = _run_git(["diff", "--no-renames", "--name-only", "-z", *endpoints, "--"], repo_root)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TargetResolutionError("security review changed-path collection failed") from exc
    if proc.returncode != 0:
        raise TargetResolutionError("security review changed-path collection failed")
    return tuple(path for path in proc.stdout.split("\0") if path)
