"""Security-sensitive review paths approved for #9125.

Changed paths are authoritative; caller-owned paths can only add coverage.
Git collection disables rename compaction so both names and deletions survive.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path

from scripts.review.target_resolution import TargetResolutionError, _run_git

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
    "scripts/start-*.sh",
    "scripts/session_start.sh",
    "scripts/install_git_hooks.sh",
    "scripts/launchers/**",
    "scripts/launchd/**",
    "scripts/lib/*.sh",
    "scripts/lib/kimi_coding_oauth.py",
    "scripts/hooks/**",
    "scripts/guardrails/**",
    "scripts/lexical_sandbox.py",
    "scripts/agent_runtime/**",
    "scripts/session_supervisor/**",
    "scripts/delegate.py",
    "scripts/orchestration/dispatch_admission.py",
    "scripts/api/delegate_router.py",
    "scripts/opsec/**",
    "scripts/secret_redactor.py",
    "scripts/audit/secret_scan_local.py",
    "scripts/ci/secret_scan_scope.py",
    "scripts/ocr/_credentials.py",
    "packages/v4-runtime/src/learn_ukrainian_v4_runtime/credential_custody.py",
    "scripts/review/*.py",
    "scripts/review/receipts/**",
    "scripts/review/validate/**",
    "scripts/build/cf_preflight.py",
    "scripts/publish/**",
    "scripts/ai_agent_bridge/_review*.py",
    "scripts/ai_agent_bridge/routing_guard.py",
    "scripts/config/model_catalog.yaml",
    "scripts/config/agent_runtime*.yaml",
    "scripts/config/agent_fallback_substitutions.yaml",
)


def is_security_sensitive_change(changed_paths: Iterable[str], owned_paths: Iterable[str] = ()) -> bool:
    """Match literal changes plus owned files or directories containing security paths."""

    def normalized(path: str) -> str:
        while path.startswith("./"):
            path = path[2:]
        return path

    if any(fnmatchcase(normalized(path), pattern) for path in changed_paths for pattern in SECURITY_SENSITIVE_PATHS):
        return True
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
