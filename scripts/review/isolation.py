"""Fail-closed process/environment/filesystem isolation for code review (#5285).

A reviewed target may contain hostile project instructions, hooks, skills,
plugins, MCP config, executable shims, Git configuration, symlinks, or
secret-like files. Reviewer subprocesses must:

- resolve trusted executables from absolute paths *outside* the reviewed root;
- inherit only an allowlisted environment (no process-injection / Git
  redirects / unrelated provider credentials);
- reject credentialed or malformed proxy URLs before engine invocation;
- prove required CLI isolation capabilities or refuse the engine (never
  silently downgrade);
- preflight sensitive paths and secret-like content before transmission;
- run under an OS-enforced sandbox that can read only the neutral snapshot
  plus explicitly required runtime/auth material, and write only to a
  disposable area.

This module is intentionally self-contained and testable. It reuses the
repository's established secret-value patterns rather than importing a
multi-thousand-line external scanner.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.parse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS
from scripts.utils.claude_version import _parse_claude_semver

ISOLATION_POLICY_VERSION = "review-isolation-v2"
CLAUDE_MIN_SUPPORTED_CLI_VERSION = (2, 1, 116)

# Process-injection / Git-override variables stripped for every reviewer.
_PROCESS_INJECTION_ENV_KEYS = frozenset(
    {
        *GIT_REDIRECT_ENV_KEYS,
        "GIT_CONFIG",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_COUNT",
        "GIT_EXEC_PATH",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GIT_PROXY_COMMAND",
        "GIT_EXTERNAL_DIFF",
        "GIT_DIFF_OPTS",
        "GIT_TRACE",
        "GIT_TRACE2",
        "GIT_TRACE_SETUP",
        "GIT_CURL_VERBOSE",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "DYLD_LIBRARY_PATH",
        "DYLD_FRAMEWORK_PATH",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "PERL5LIB",
        "RUBYLIB",
        "NODE_OPTIONS",
        "NODE_PATH",
        "BASH_ENV",
        "ENV",
        "CDPATH",
        "IFS",
        "PROMPT_COMMAND",
        "GPG_TTY",
        "EDITOR",
        "VISUAL",
        "PAGER",
        "GIT_EDITOR",
        "GIT_PAGER",
        "GIT_SEQUENCE_EDITOR",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",  # re-set intentionally below
    }
)

_PROXY_ENV_KEYS = frozenset(
    {
        "ALL_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "all_proxy",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)

_COMMON_ENV_ALLOWLIST = frozenset(
    {
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "TMPDIR",
        "TMP",
        "TEMP",
        "SHELL",
        "PATH",
        "COLORTERM",
        "NO_COLOR",
        "FORCE_COLOR",
        "CI",
        "GITHUB_ACTIONS",
        "DO_NOT_TRACK",
        "DISABLE_TELEMETRY",
        "DISABLE_AUTOUPDATER",
        "DISABLE_ERROR_REPORTING",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_RUNTIME_DIR",
        *_PROXY_ENV_KEYS,
    }
)

# Only the selected engine's authentication material is forwarded.
_ENGINE_AUTH_ENV: dict[str, frozenset[str]] = {
    "claude": frozenset(
        {
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
        }
    ),
    "codex": frozenset(
        {
            "OPENAI_API_KEY",
            "CODEX_API_KEY",
            "OPENAI_ORGANIZATION",
            "OPENAI_PROJECT",
            "CODEX_HOME",
        }
    ),
    "agy": frozenset(
        {
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_GENERATIVE_AI_API_KEY",
        }
    ),
    "grok": frozenset(
        {
            "XAI_API_KEY",
            "GROK_API_KEY",
        }
    ),
    "grok-build": frozenset(
        {
            "XAI_API_KEY",
            "GROK_API_KEY",
        }
    ),
    "gemini": frozenset(
        {
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "GOOGLE_GENERATIVE_AI_API_KEY",
        }
    ),
}

# DEPRECATED for sandbox grants: whole provider trees must never be readable.
# Auth is staged via _ENGINE_AUTH_STAGE_FILES into the disposable write-root home.
_ENGINE_AUTH_READ_DIRS: dict[str, tuple[str, ...]] = {
    "claude": (),
    "codex": (),
    "agy": (),
    "grok": (),
    "grok-build": (),
    "gemini": (),
}

# Unrelated provider / package / telemetry credentials that must never leak.
_UNRELATED_CREDENTIAL_ENV = frozenset(
    {
        "NPM_TOKEN",
        "NODE_AUTH_TOKEN",
        "PYPI_TOKEN",
        "TWINE_PASSWORD",
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "SENTRY_AUTH_TOKEN",
        "SENTRY_DSN",
        "DD_API_KEY",
        "DATADOG_API_KEY",
        "TELEMETRY_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AZURE_CLIENT_SECRET",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GITLAB_TOKEN",
        "SSH_AUTH_SOCK",
    }
)

# Sensitive path fragments (directory components or full relative names).
_SENSITIVE_PATH_PARTS = frozenset(
    {
        ".ssh",
        ".gnupg",
        ".aws",
        ".azure",
        ".docker",
        ".kube",
        "private",
    }
)

_CREDENTIAL_FILE_RE = re.compile(
    r"(^|/)(?:\.netrc|\.git-credentials)$",
    re.IGNORECASE,
)
_ENV_FILE_RE = re.compile(
    r"(^|/)\.env(?:$|[._/-])",
    re.IGNORECASE,
)
# Allow design-token / benign fixtures: ``tokens.css``, ``design-tokens.json``,
# ``token_helpers.py`` — require credential-ish context for "token"/"secret".
_SENSITIVE_NAME_RE = re.compile(
    r"(^|/)(?:"
    r"(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)(?:\.pub)?|"
    r"[^/]*\.(?:pem|p12|pfx|key)|"
    r"(?:secrets?|credentials?|service[-_]?account|private[-_]?key|api[-_]?keys?)"
    r"(?:\.[^/]+)?|"
    r"(?:access|auth|refresh|session)[-_]?tokens?(?:\.[^/]+)?|"
    r"tokens?\.(?:json|ya?ml|toml|ini|conf|config|txt|env|pem|key)"
    r")$",
    re.IGNORECASE,
)

# Design-token / UI-token basenames that must remain reviewable.
_BENIGN_TOKEN_NAME_RE = re.compile(
    r"(^|/)(?:design[-_]?tokens?|color[-_]?tokens?|theme[-_]?tokens?|"
    r"tokens?\.(?:css|scss|less|ts|tsx|js|jsx)|token_helpers?\.py|"
    r"token[_-]?tests?\.py)$",
    re.IGNORECASE,
)

_SECRET_VALUE_RE = re.compile(
    r"(?:"
    r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----|"
    r"\bgithub_pat_[A-Za-z0-9_]{20,}|"
    r"\bgh[pousr]_[A-Za-z0-9_]{20,}|"
    r"\bglpat-[A-Za-z0-9_-]{20,}|"
    r"\bnpm_[A-Za-z0-9]{20,}|"
    r"\bxox[baprs]-[A-Za-z0-9-]{20,}|"
    r"\b(?:sk|rk|pk)-(?:proj|org-)?[A-Za-z0-9_-]{20,}|"
    r"\b(?:A3T|AKIA|ASIA)[A-Z0-9]{16}\b|"
    r"\bAIza[0-9A-Za-z_-]{35}\b|"
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    r")"
)

# Assignment of a high-entropy-looking secret value. Avoid bare ``token =``
# assignments that only mention design tokens / enums.
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:^|[\s,{])(?:"
    r"(?P<assignment_quote>['\"])(?:api[_-]?key|aws[_-]?secret[_-]?access[_-]?key|"
    r"client[_-]?secret|private[_-]?key|password|passwd|secret[_-]?key|"
    r"access[_-]?token|refresh[_-]?token|auth[_-]?token|id[_-]?token)"
    r"(?P=assignment_quote)|"
    r"(?:api[_-]?key|aws[_-]?secret[_-]?access[_-]?key|client[_-]?secret|"
    r"private[_-]?key|password|passwd|secret[_-]?key|"
    r"access[_-]?token|refresh[_-]?token|auth[_-]?token|id[_-]?token)"
    r")\s*[:=]\s*"
    r"(?:['\"][^'\"\n]{12,}['\"]|[A-Za-z0-9_./+=:@#$%&*!?-]{16,})"
)

_DEFAULT_EXTERNAL_PATHS = ("/usr/local/bin", "/opt/homebrew/bin", "/usr/bin", "/bin")

# Isolation capabilities each engine must prove before invocation.
_ENGINE_REQUIRED_CAPABILITIES: dict[str, frozenset[str]] = {
    "claude": frozenset(
        {
            "disable_project_instructions",
            "disable_hooks_skills_plugins",
            "disable_mcp",
            "read_only_or_no_write_tools",
            "no_nested_reviewers",
            "structured_output",
        }
    ),
    "codex": frozenset(
        {
            "ignore_user_config",
            "ignore_project_rules",
            "sandbox_or_empty_workspace",
            "read_only_or_no_write_tools",
            "no_nested_reviewers",
        }
    ),
    "agy": frozenset(
        {
            "disable_project_instructions",
            "read_only_or_no_write_tools",
            "no_nested_reviewers",
            "os_sandbox_required",
        }
    ),
    "grok": frozenset(
        {
            "plan_or_read_only_mode",
            "deny_write_shell",
            "no_nested_reviewers",
        }
    ),
    "grok-build": frozenset(
        {
            "plan_or_read_only_mode",
            "deny_write_shell",
            "no_nested_reviewers",
        }
    ),
    "gemini": frozenset(
        {
            "read_only_or_no_write_tools",
            "no_nested_reviewers",
        }
    ),
}

_SYSTEM_READ_SUBPATHS = (
    # Never grant all of /usr: /usr/local can contain user-managed config and
    # credentials. Runtime closure adds any exact third-party installation
    # paths separately.
    "/usr/bin",
    "/usr/sbin",
    "/usr/lib",
    "/usr/lib64",
    "/usr/libexec",
    "/usr/share",
    "/bin",
    "/sbin",
    "/System",
    # Only dyld/shared-cache metadata under /private/var — never all of
    # /private/var, /private/tmp, /tmp, or arbitrary host temp trees.
    "/private/var/db/timezone",
    "/private/var/select",
    "/dev",
    "/lib",
    "/lib64",
)

_NETWORK_READ_PATHS = (
    "/etc/ssl",
    "/private/etc/ssl",
    "/etc/hosts",
    "/private/etc/hosts",
    "/etc/resolv.conf",
    "/private/etc/resolv.conf",
)

# Narrow auth files staged into the disposable HOME (never whole provider trees).
_ENGINE_AUTH_STAGE_FILES: dict[str, tuple[str, ...]] = {
    "claude": (),  # subscription token is staged in env; no host .claude tree
    "codex": (".codex/auth.json",),
    "agy": (
        ".gemini/oauth_creds.json",
        ".gemini/google_accounts.json",
        ".agy/credentials.json",
        ".config/agy/credentials.json",
    ),
    # Native Grok needs a file-backed OAuth store while also exposing general
    # Read/Grep/Glob tools. The CLI provides no channel that keeps that store
    # outside model-tool scope, so isolated Grok reviews are refused below.
    "grok": (),
    "grok-build": (),
    "gemini": (
        ".gemini/oauth_creds.json",
        ".gemini/google_accounts.json",
    ),
}


class ReviewIsolationError(RuntimeError):
    """A fail-closed isolation or input-safety gate rejected the review run."""


@dataclass(frozen=True)
class EngineCapabilities:
    """Feature-detected isolation capabilities for one review engine binary."""

    engine: str
    binary: Path
    version_text: str
    capabilities: frozenset[str]
    missing: frozenset[str]

    @property
    def ok(self) -> bool:
        return not self.missing

    def public_digest(self) -> str:
        """Non-secret digest of the capability proof for evidence binding."""
        payload = {
            "engine": self.engine,
            "binary": str(self.binary),
            "binary_sha256": _file_sha256(self.binary),
            "capabilities": sorted(self.capabilities),
            "missing": sorted(self.missing),
            "version_sha256": hashlib.sha256(self.version_text.encode("utf-8", errors="replace")).hexdigest(),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class SandboxCapability:
    """Verified host sandbox mechanism for reviewer containment."""

    mechanism: str
    binary: Path | None
    profile_path: Path | None
    read_roots: tuple[str, ...]
    write_root: str
    verified: bool
    metadata_roots: tuple[str, ...] = ()
    probe_detail: str = ""
    network_allowed: bool = True

    def public_dict(self) -> dict[str, Any]:
        roots_digest = hashlib.sha256(
            json.dumps(
                {
                    "read_roots": list(self.read_roots),
                    "metadata_roots": list(self.metadata_roots),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            "mechanism": self.mechanism,
            "binary": str(self.binary) if self.binary else None,
            "verified": self.verified,
            "read_root_count": len(self.read_roots),
            "metadata_root_count": len(self.metadata_roots),
            "read_roots_digest": roots_digest,
            "read_roots": list(self.read_roots),
            "metadata_roots": list(self.metadata_roots),
            "write_root_basename": Path(self.write_root).name,
            "probe_detail": self.probe_detail,
            "network_allowed": self.network_allowed,
        }


@dataclass(frozen=True)
class IsolatedReviewLaunch:
    """Fully enforced argv + env for one isolated reviewer spawn."""

    argv: list[str]
    env: dict[str, str]
    cwd: Path
    write_root: Path
    snapshot_root: Path
    engine: str
    policy_version: str
    capabilities: EngineCapabilities
    sandbox: SandboxCapability
    evidence: dict[str, Any] = field(default_factory=dict)


def is_within(path: Path, root: Path) -> bool:
    """True if ``path`` is ``root`` or a descendant (after resolve)."""
    try:
        resolved = path.resolve()
        base = root.resolve()
    except OSError:
        return False
    return resolved == base or base in resolved.parents


def validate_private_review_roots(
    *,
    snapshot_root: Path,
    write_root: Path,
    reject_root: Path,
    reject_roots: Iterable[Path | str] = (),
) -> tuple[Path, Path]:
    """Validate parent-owned review roots before any adapter writes occur."""
    for label, raw in (("snapshot", snapshot_root), ("write", write_root)):
        try:
            st = raw.lstat()
        except OSError as exc:
            raise ReviewIsolationError(f"{label}_root_missing:{raw}") from exc
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise ReviewIsolationError(f"{label}_root_not_private_directory:{raw}")
    snap = snapshot_root.resolve(strict=True)
    write = write_root.resolve(strict=True)
    if snap == write or is_within(write, snap) or is_within(snap, write):
        raise ReviewIsolationError("snapshot_write_roots_overlap")
    broad = {
        Path("/").resolve(),
        Path.home().resolve(),
        Path(tempfile.gettempdir()).resolve(),
        Path("/tmp").resolve(),
        Path("/private/tmp").resolve(),
        Path("/var").resolve(),
        Path("/private/var").resolve(),
    }
    if write in broad:
        raise ReviewIsolationError(f"review_write_root_too_broad:{write}")
    rejects = _normalized_reject_roots(reject_root, reject_roots)
    if _inside_any(write, rejects):
        raise ReviewIsolationError("write_root_inside_reject_root")
    mode = write.stat().st_mode
    if hasattr(os, "getuid") and write.stat().st_uid != os.getuid():
        raise ReviewIsolationError("review_write_root_wrong_owner")
    if stat.S_IMODE(mode) & 0o077:
        raise ReviewIsolationError("review_write_root_not_owner_only")
    return snap, write


def validated_review_write_root(tool_config: Mapping[str, Any]) -> Path:
    """Adapter preflight for the parent-owned review write root."""
    if not tool_config.get("review_isolation"):
        raise ReviewIsolationError("review_isolation_flag_missing")
    snapshot_raw = tool_config.get("review_snapshot_root") or tool_config.get("repo_read_root")
    write_raw = tool_config.get("review_write_root")
    reject_raw = tool_config.get("review_reject_root") or snapshot_raw
    raw_rejects = tool_config.get("review_reject_roots") or ()
    if not snapshot_raw or not write_raw or not reject_raw:
        raise ReviewIsolationError("review_parent_owned_roots_missing")
    if not isinstance(raw_rejects, (list, tuple)) or not all(
        isinstance(item, str) and item for item in raw_rejects
    ):
        raise ReviewIsolationError("review_reject_roots_malformed")
    _snap, write = validate_private_review_roots(
        snapshot_root=Path(str(snapshot_raw)),
        write_root=Path(str(write_raw)),
        reject_root=Path(str(reject_raw)),
        reject_roots=tuple(Path(item) for item in raw_rejects),
    )
    for child in (write / "tmp", write / "home", write / "exec"):
        if not child.is_dir() or child.is_symlink():
            raise ReviewIsolationError(f"review_parent_owned_subdir_missing:{child.name}")
    return write


def _validate_private_exec_root(
    *,
    exec_root: Path,
    snapshot_root: Path,
    write_root: Path,
    reject_roots: Iterable[Path | str],
) -> Path:
    try:
        st = exec_root.lstat()
    except OSError as exc:
        raise ReviewIsolationError(f"review_exec_root_missing:{exec_root}") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ReviewIsolationError("review_exec_root_not_private_directory")
    root = exec_root.resolve(strict=True)
    if any(is_within(root, other) or is_within(other, root) for other in (snapshot_root, write_root)):
        raise ReviewIsolationError("review_exec_root_overlap")
    if _inside_any(root, tuple(Path(item).resolve() for item in reject_roots)):
        raise ReviewIsolationError("review_exec_root_inside_reject_root")
    if hasattr(os, "getuid") and st.st_uid != os.getuid():
        raise ReviewIsolationError("review_exec_root_wrong_owner")
    if stat.S_IMODE(st.st_mode) & 0o077:
        raise ReviewIsolationError("review_exec_root_not_owner_only")
    if any(root.iterdir()):
        raise ReviewIsolationError("review_exec_root_not_empty")
    return root


def _stage_pinned_reviewer_runtime(executable: Path, *, exec_root: Path) -> Path:
    """Copy the selected runtime to a private read-only root and return argv0.

    Package scripts are copied with their owning package so relative imports
    remain valid. Symlinks may only remain inside that copied package.
    """
    source = executable.resolve(strict=True)
    source_digest = _file_sha256(source)
    package_root: Path | None = None
    # Only Node package executables need an owning package copy. Never walk
    # into an unrelated ancestor package.json (for example one in $HOME),
    # which could stage an arbitrarily broad user tree.
    if "node_modules" in source.parts:
        node_index = max(index for index, part in enumerate(source.parts) if part == "node_modules")
        package_parts = source.parts[: node_index + 2]
        if len(source.parts) > node_index + 2 and source.parts[node_index + 1].startswith("@"):
            package_parts = source.parts[: node_index + 3]
        candidate_package = Path(*package_parts)
        if (candidate_package / "package.json").is_file() and is_within(source, candidate_package):
            package_root = candidate_package
    if package_root is None:
        staged = exec_root / "reviewer"
        source_fd = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            before = os.fstat(source_fd)
            dest_fd = os.open(
                staged,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o500,
            )
            try:
                while True:
                    chunk = os.read(source_fd, 1024 * 1024)
                    if not chunk:
                        break
                    _write_fd_all(dest_fd, chunk)
            finally:
                os.close(dest_fd)
            after = os.fstat(source_fd)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ReviewIsolationError("reviewer_binary_changed_during_stage")
        finally:
            os.close(source_fd)
    else:
        package_dest = exec_root / "package"
        shutil.copytree(package_root, package_dest, symlinks=True)
        staged = package_dest / source.relative_to(package_root)
        for dirpath, dirnames, filenames in os.walk(package_dest, followlinks=False):
            base = Path(dirpath)
            for name in [*dirnames, *filenames]:
                item = base / name
                if not item.is_symlink():
                    continue
                target = item.readlink()
                if target.is_absolute() or not is_within((item.parent / target).resolve(strict=False), package_dest):
                    raise ReviewIsolationError(f"reviewer_runtime_symlink_escape:{item}")
    if not staged.is_file() or staged.is_symlink() or _file_sha256(staged) != source_digest:
        raise ReviewIsolationError("reviewer_binary_stage_digest_mismatch")
    return staged


def _freeze_exec_root(exec_root: Path, *, staged_binary: Path) -> None:
    """Make staged runtime/prompt bytes read-only before sandbox construction."""
    for dirpath, dirnames, filenames in os.walk(exec_root, topdown=False, followlinks=False):
        base = Path(dirpath)
        for name in filenames:
            item = base / name
            if not item.is_symlink():
                item.chmod(0o500 if os.access(item, os.X_OK) or item == staged_binary else 0o400)
        for name in dirnames:
            item = base / name
            if not item.is_symlink():
                item.chmod(0o500)
    exec_root.chmod(0o500)


SEALED_READ_CHUNK_BYTES = 64 * 1024


_SEALED_READ_MCP_SOURCE = r'''#!/usr/bin/python3
import hashlib
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(sys.argv[1]).resolve(strict=True)
MAX_CHUNK_BYTES = 64 * 1024
MAX_REQUIRED_CHUNKS = 6
MAX_REQUIRED_ALL_CHUNKS = 64
MAX_REQUIRED_TOTAL_BYTES = 2 * 1024 * 1024
MAX_SEARCH_FILE_BYTES = 8 * 1024 * 1024
MAX_LISTED_FILES = 10000

def candidate_path(raw):
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError("invalid_path")
    parsed = PurePosixPath(raw)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError("invalid_path")
    candidate = ROOT / Path(*parsed.parts)
    candidate.resolve(strict=False).relative_to(ROOT)
    return candidate

def safe_path(raw):
    path = candidate_path(raw).resolve(strict=True)
    path.relative_to(ROOT)
    return path

def stable_stat(fd):
    value = os.fstat(fd)
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("not_regular")
    return value

def same_file(before, after):
    return (
        before.st_dev, before.st_ino, before.st_size,
        before.st_mtime_ns, before.st_ctime_ns,
    ) == (
        after.st_dev, after.st_ino, after.st_size,
        after.st_mtime_ns, after.st_ctime_ns,
    )

def file_sha256(fd):
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        block = os.read(fd, 1024 * 1024)
        if not block:
            break
        digest.update(block)
    return digest.hexdigest()

def read_chunk(raw, offset=0, max_bytes=MAX_CHUNK_BYTES):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("invalid_offset")
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or max_bytes < 1
        or max_bytes > MAX_CHUNK_BYTES
    ):
        raise ValueError("invalid_max_bytes")
    path = safe_path(raw)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = stable_stat(fd)
        if offset > before.st_size:
            raise ValueError("offset_past_end")
        digest = file_sha256(fd)
        os.lseek(fd, offset, os.SEEK_SET)
        remaining = min(max_bytes, before.st_size - offset)
        parts = []
        while remaining:
            part = os.read(fd, remaining)
            if not part:
                raise ValueError("short_read")
            parts.append(part)
            remaining -= len(part)
        data = b"".join(parts)
        while data:
            try:
                text = data.decode("utf-8", errors="strict")
                break
            except UnicodeDecodeError as exc:
                if exc.reason != "unexpected end of data" or len(data) <= 1:
                    raise ValueError("not_utf8") from exc
                data = data[:-1]
        else:
            text = ""
        after = stable_stat(fd)
        if not same_file(before, after):
            raise ValueError("file_changed")
        next_offset = offset + len(data)
        return {
            "path": raw,
            "sha256": digest,
            "offset": offset,
            "chunk_bytes": len(data),
            "chunk_sha256": hashlib.sha256(data).hexdigest(),
            "next_offset": next_offset,
            "total_bytes": before.st_size,
            "eof": next_offset == before.st_size,
            "content": text,
        }
    finally:
        os.close(fd)

def required_paths():
    manifest_path = ".review-bundle/manifest.json"
    manifest_chunk = read_chunk(manifest_path, 0, MAX_CHUNK_BYTES)
    if not manifest_chunk["eof"]:
        raise ValueError("required_manifest_split_required")
    try:
        manifest = json.loads(manifest_chunk["content"])
    except json.JSONDecodeError as exc:
        raise ValueError("required_manifest_invalid") from exc
    changed = manifest.get("changed_paths") if isinstance(manifest, dict) else None
    if not isinstance(changed, list) or not all(isinstance(item, str) for item in changed):
        raise ValueError("required_manifest_changed_paths_invalid")
    result = [manifest_path, ".review-bundle/patch.diff"]
    seen = set(result)
    for raw in changed:
        candidate = candidate_path(raw)
        if candidate.is_symlink():
            continue
        if not candidate.exists():
            continue
        if not candidate.is_file():
            raise ValueError("required_path_not_regular")
        safe_path(raw)
        if raw in seen:
            raise ValueError("required_path_duplicate")
        seen.add(raw)
        result.append(raw)
    return result

def read_required(index=0, offset=0):
    paths = required_paths()
    if (
        not isinstance(index, int)
        or isinstance(index, bool)
        or not isinstance(offset, int)
        or isinstance(offset, bool)
        or index < 0
        or index > len(paths)
        or offset < 0
        or (index == len(paths) and offset != 0)
    ):
        raise ValueError("invalid_required_cursor")
    start_index = index
    start_offset = offset
    chunks = []
    while index < len(paths) and len(chunks) < MAX_REQUIRED_CHUNKS:
        chunk = read_chunk(paths[index], offset, MAX_CHUNK_BYTES)
        chunks.append(chunk)
        if chunk["eof"]:
            index += 1
            offset = 0
        else:
            if chunk["next_offset"] <= offset:
                raise ValueError("required_cursor_stalled")
            offset = chunk["next_offset"]
    return {
        "index": start_index,
        "offset": start_offset,
        "next_index": index,
        "next_offset": offset,
        "required_path_count": len(paths),
        "eof": index == len(paths),
        "chunks": chunks,
    }

def read_required_all():
    paths = required_paths()
    total_bytes = sum(safe_path(raw).stat().st_size for raw in paths)
    if total_bytes > MAX_REQUIRED_TOTAL_BYTES:
        raise ValueError("required_evidence_split_required")
    chunks = []
    for raw in paths:
        offset = 0
        while True:
            chunk = read_chunk(raw, offset, MAX_CHUNK_BYTES)
            chunks.append(chunk)
            if len(chunks) > MAX_REQUIRED_ALL_CHUNKS:
                raise ValueError("required_chunk_count_split_required")
            if chunk["eof"]:
                break
            if chunk["next_offset"] <= offset:
                raise ValueError("required_cursor_stalled")
            offset = chunk["next_offset"]
    return {
        "required_path_count": len(paths),
        "total_bytes": total_bytes,
        "eof": True,
        "chunks": chunks,
    }

def files(prefix=""):
    if prefix:
        base = safe_path(prefix)
        if base.is_file():
            return [prefix]
    else:
        base = ROOT
    result = []
    for directory, dirnames, filenames in os.walk(base, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in filenames:
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("non_regular_entry")
            result.append(path.relative_to(ROOT).as_posix())
            if len(result) > MAX_LISTED_FILES:
                raise ValueError("file_list_split_required")
    return result

def search_file(raw, query):
    path = safe_path(raw)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = stable_stat(fd)
        if before.st_size > MAX_SEARCH_FILE_BYTES:
            raise ValueError("search_split_required")
        with os.fdopen(os.dup(fd), "r", encoding="utf-8", errors="strict") as handle:
            for number, line in enumerate(handle, 1):
                if len(line.encode("utf-8")) > MAX_CHUNK_BYTES:
                    raise ValueError("search_line_split_required")
                if query in line:
                    yield number, line.rstrip("\r\n")
        after = stable_stat(fd)
        if not same_file(before, after):
            raise ValueError("file_changed")
    finally:
        os.close(fd)

TOOLS = [
    {"name":"list_files","description":"List every safe UTF-8 file in the sealed review snapshot.","inputSchema":{"type":"object","properties":{"prefix":{"type":"string"}},"additionalProperties":False}},
    {"name":"read_file","description":"Read one hash-bound UTF-8 byte chunk. Start at offset 0 and repeat from next_offset until eof=true.","inputSchema":{"type":"object","properties":{"path":{"type":"string"},"offset":{"type":"integer","minimum":0},"max_bytes":{"type":"integer","minimum":1,"maximum":65536}},"required":["path"],"additionalProperties":False}},
    {"name":"read_required","description":"Read the next six hash-bound chunks from the authoritative required review stream. Start at index=0, offset=0 and repeat from next_index/next_offset until eof=true.","inputSchema":{"type":"object","properties":{"index":{"type":"integer","minimum":0},"offset":{"type":"integer","minimum":0}},"additionalProperties":False}},
    {"name":"read_required_all","description":"Read every hash-bound chunk from an authoritative required review scope of at most 2 MiB. Larger scopes fail closed and must be split.","inputSchema":{"type":"object","properties":{},"additionalProperties":False}},
    {"name":"search_text","description":"Search safe sealed files for an exact text substring; refine the query if truncated is true.","inputSchema":{"type":"object","properties":{"query":{"type":"string","minLength":1},"prefix":{"type":"string"}},"required":["query"],"additionalProperties":False}},
]

def call_tool(name, args):
    if not isinstance(args, dict):
        raise ValueError("arguments_must_be_object")
    if name == "list_files":
        payload = {"files": files(args.get("prefix", ""))}
    elif name == "read_file":
        payload = read_chunk(
            args.get("path"),
            args.get("offset", 0),
            args.get("max_bytes", MAX_CHUNK_BYTES),
        )
    elif name == "read_required":
        payload = read_required(args.get("index", 0), args.get("offset", 0))
    elif name == "read_required_all":
        payload = read_required_all()
    elif name == "search_text":
        query = args.get("query")
        if not isinstance(query, str) or not query:
            raise ValueError("invalid_query")
        matches = []
        truncated = False
        for rel in files(args.get("prefix", "")):
            for number, line in search_file(rel, query):
                if len(matches) == 200:
                    truncated = True
                    break
                matches.append({"path": rel, "line": number, "text": line})
            if truncated:
                break
        payload = {"matches": matches, "truncated": truncated}
    else:
        raise ValueError("unknown_tool")
    return {"content":[{"type":"text","text":json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}],"isError":False}

for raw in sys.stdin:
    request = None
    request_id = None
    try:
        request = json.loads(raw)
        method = request.get("method")
        request_id = request.get("id")
        if method == "initialize":
            result = {"protocolVersion":"2025-03-26","capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"sealed-review-reader","version":"1"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = request.get("params") or {}
            result = call_tool(params.get("name"), params.get("arguments") or {})
        elif method == "ping":
            result = {}
        elif request_id is None:
            continue
        else:
            raise ValueError("unsupported_method")
        response = {"jsonrpc":"2.0","id":request_id,"result":result}
    except Exception as exc:
        if isinstance(locals().get("request"), dict) and request.get("id") is None:
            continue
        response = {"jsonrpc":"2.0","id":locals().get("request_id"),"error":{"code":-32602,"message":type(exc).__name__ + ":" + str(exc)}}
    sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()
'''


def _stage_sealed_read_mcp(exec_root: Path) -> Path:
    """Stage the parent-owned read-only MCP helper beside the pinned reviewer."""
    helper = exec_root / "sealed-read-mcp.py"
    fd = os.open(
        helper,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o400,
    )
    try:
        _write_fd_all(fd, _SEALED_READ_MCP_SOURCE.encode("utf-8"))
    finally:
        os.close(fd)
    return helper


def _inject_codex_sealed_read_mcp(
    argv: Sequence[str],
    *,
    python_bin: Path,
    helper: Path,
    snapshot_root: Path,
) -> list[str]:
    """Inject only the parent-owned sealed reader into an empty Codex config."""
    command = f"mcp_servers.sealed_review.command={json.dumps(str(python_bin))}"
    args = "mcp_servers.sealed_review.args=" + json.dumps(
        ["-I", "-S", str(helper), str(snapshot_root)],
        separators=(",", ":"),
    )
    injected = list(argv)
    index = len(injected) - 1 if injected and injected[-1] == "-" else len(injected)
    injected[index:index] = [
        "-c",
        'approval_policy="never"',
        "-c",
        command,
        "-c",
        args,
        "-c",
        "mcp_servers.sealed_review.enabled=true",
    ]
    return injected


def _sealed_reader_python_runtime(
    python_bin: Path,
    *,
    reject_roots: Iterable[Path | str],
) -> tuple[Path, list[str]]:
    """Resolve the isolated stdlib/runtime needed by the sealed MCP helper.

    macOS ``/usr/bin/python3`` is commonly a shim into the Command Line Tools
    framework.  Its real interpreter and stdlib live outside ``/usr`` and must
    be granted explicitly.  The fixed interpreter is probed with ``-I -S`` so
    user site packages and environment configuration cannot affect discovery.
    """
    probe_source = (
        "import json,sys,sysconfig;"
        "print(json.dumps({'prefix':sys.prefix,'base_prefix':sys.base_prefix,"
        "'stdlib':sysconfig.get_path('stdlib'),"
        "'platstdlib':sysconfig.get_path('platstdlib'),"
        "'bindir':sysconfig.get_config_var('BINDIR'),"
        "'version':sysconfig.get_config_var('VERSION')},sort_keys=True))"
    )
    probe_env = {
        "HOME": "/var/empty",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }
    try:
        completed = subprocess.run(
            [str(python_bin), "-I", "-S", "-c", probe_source],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            env=probe_env,
            cwd=tempfile.gettempdir(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewIsolationError("sealed_reader_python_runtime_probe_failed") from exc
    if completed.returncode != 0:
        raise ReviewIsolationError(
            "sealed_reader_python_runtime_probe_failed:"
            f"rc={completed.returncode}:{(completed.stderr or '')[:160]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReviewIsolationError("sealed_reader_python_runtime_probe_malformed") from exc
    if not isinstance(payload, dict):
        raise ReviewIsolationError("sealed_reader_python_runtime_probe_malformed")

    rejects = tuple(Path(root).resolve() for root in reject_roots)
    bindir = payload.get("bindir")
    prefix = payload.get("prefix")
    version = payload.get("version")
    resolved_python = python_bin.resolve(strict=True)
    candidates: list[Path] = []
    if isinstance(version, str) and version:
        if isinstance(prefix, str) and prefix:
            candidates.append(Path(prefix) / "bin" / f"python{version}")
        if isinstance(bindir, str) and bindir:
            candidates.append(Path(bindir) / f"python{version}")
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            resolved_python = candidate.resolve(strict=True)
            break
    if _inside_any(resolved_python, rejects):
        raise ReviewIsolationError("sealed_reader_python_runtime_binary_rejected")

    broad_roots = {Path("/"), Path("/usr"), Path("/usr/local"), Path("/opt/homebrew")}
    discovered = resolve_runtime_closure(resolved_python, reject_roots=rejects)
    for key in ("prefix", "base_prefix", "stdlib", "platstdlib"):
        raw = payload.get(key)
        if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
            raise ReviewIsolationError(f"sealed_reader_python_runtime_{key}_invalid")
        try:
            resolved = Path(raw).resolve(strict=True)
        except OSError as exc:
            raise ReviewIsolationError(f"sealed_reader_python_runtime_{key}_missing") from exc
        if _inside_any(resolved, rejects):
            raise ReviewIsolationError(f"sealed_reader_python_runtime_{key}_rejected")
        if resolved in broad_roots:
            # System Python on Linux may report /usr; the fixed system read
            # roots already grant its narrow bin/lib/share paths.
            continue
        value = str(resolved)
        if value not in discovered:
            discovered.append(value)
    return resolved_python, discovered


def _probe_sealed_read_mcp(
    *,
    python_bin: Path,
    helper: Path,
    snapshot_root: Path,
    sandbox: SandboxCapability,
) -> None:
    """Execute the exact staged MCP helper inside the verified sandbox."""
    manifest = snapshot_root / ".review-bundle" / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise ReviewIsolationError("sealed_reader_probe_manifest_missing")
    requests = (
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {
                    "path": ".review-bundle/manifest.json",
                    "offset": 0,
                    "max_bytes": 1024,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "read_required",
                "arguments": {"index": 0, "offset": 0},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "read_required_all", "arguments": {}},
        },
    )
    command = wrap_argv_with_sandbox(
        [str(python_bin), "-I", "-S", str(helper), str(snapshot_root)],
        sandbox,
    )
    try:
        completed = subprocess.run(
            command,
            input="\n".join(json.dumps(item, separators=(",", ":")) for item in requests) + "\n",
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            env={"HOME": sandbox.write_root, "PATH": "/usr/bin:/bin", "LANG": "C"},
            cwd=str(snapshot_root),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewIsolationError("sealed_reader_probe_failed") from exc
    if completed.returncode != 0:
        raise ReviewIsolationError(
            f"sealed_reader_probe_failed:rc={completed.returncode}:{(completed.stderr or '')[:160]}"
        )
    try:
        responses = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
        listed = {tool["name"] for tool in responses[1]["result"]["tools"]}
        payload = json.loads(responses[2]["result"]["content"][0]["text"])
        required_payload = json.loads(responses[3]["result"]["content"][0]["text"])
        required_all_payload = json.loads(responses[4]["result"]["content"][0]["text"])
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ReviewIsolationError("sealed_reader_probe_malformed") from exc
    if {
        "list_files",
        "read_file",
        "read_required",
        "read_required_all",
        "search_text",
    } - listed:
        raise ReviewIsolationError("sealed_reader_probe_tools_missing")
    expected_digest = _file_sha256(manifest)
    if (
        payload.get("path") != ".review-bundle/manifest.json"
        or payload.get("offset") != 0
        or payload.get("sha256") != expected_digest
        or not isinstance(payload.get("chunk_bytes"), int)
        or payload.get("chunk_bytes", 0) > 1024
    ):
        raise ReviewIsolationError("sealed_reader_probe_read_mismatch")
    required_chunks = required_payload.get("chunks")
    if (
        required_payload.get("index") != 0
        or required_payload.get("offset") != 0
        or not isinstance(required_chunks, list)
        or not required_chunks
        or required_chunks[0].get("path") != ".review-bundle/manifest.json"
        or required_chunks[0].get("sha256") != expected_digest
    ):
        raise ReviewIsolationError("sealed_reader_probe_required_mismatch")
    required_all_chunks = required_all_payload.get("chunks")
    if (
        required_all_payload.get("eof") is not True
        or not isinstance(required_all_chunks, list)
        or not required_all_chunks
        or required_all_chunks[0].get("path") != ".review-bundle/manifest.json"
        or required_all_chunks[0].get("sha256") != expected_digest
    ):
        raise ReviewIsolationError("sealed_reader_probe_required_all_mismatch")


def _file_sha256(path: Path) -> str:
    """Hash one trusted executable without executing it."""
    try:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    except OSError as exc:
        raise ReviewIsolationError(f"executable_digest_failed:{path}") from exc


def _write_fd_all(fd: int, data: bytes) -> None:
    """Write every byte to a regular file descriptor or fail."""
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write")
        view = view[written:]


def _normalized_reject_roots(reject_root: Path, reject_roots: Iterable[Path | str] = ()) -> tuple[Path, ...]:
    roots = {reject_root.resolve()}
    for root in reject_roots:
        roots.add(Path(root).resolve())
    return tuple(sorted(roots, key=str))


def _inside_any(path: Path, roots: Iterable[Path]) -> bool:
    return any(is_within(path, root) for root in roots)


def normalize_engine_name(engine: str) -> str:
    """Canonical engine key for isolation policy tables."""
    key = engine.strip().lower()
    if key in {"grok-build", "grok_build"}:
        return "grok"
    return key


def resolve_external_executable(
    name: str,
    *,
    reject_root: Path,
    reject_roots: Iterable[Path | str] = (),
    path_env: str | None = None,
    fixed_only: bool = False,
) -> Path:
    """Resolve ``name`` to an absolute executable path outside ``reject_root``.

    Never executes or returns a binary that lives inside the reviewed checkout
    (repo-local ``git`` / ``gh`` / reviewer shims are unreachable).
    """
    if not name or name.startswith("-"):
        raise ReviewIsolationError(f"invalid_executable_name:{name!r}")

    rejects = _normalized_reject_roots(reject_root, reject_roots)
    candidate = Path(name)
    if candidate.is_absolute() or os.sep in name or (os.altsep and os.altsep in name):
        try:
            resolved = candidate.expanduser().resolve(strict=True)
        except OSError as exc:
            raise ReviewIsolationError(f"executable_not_found:{name}") from exc
        if _inside_any(resolved, rejects):
            raise ReviewIsolationError(f"executable_inside_review_root:{resolved}")
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise ReviewIsolationError(f"executable_not_runnable:{resolved}")
        return resolved

    if not fixed_only:
        search_path = path_env if path_env is not None else os.environ.get("PATH", "")
        for part in search_path.split(os.pathsep):
            if not part or part == ".":
                continue
            entry = Path(part)
            if not entry.is_absolute():
                continue
            try:
                entry_resolved = entry.resolve()
            except OSError:
                continue
            if _inside_any(entry_resolved, rejects):
                continue
            hit = entry_resolved / name
            if hit.is_file() and os.access(hit, os.X_OK):
                try:
                    return hit.resolve(strict=True)
                except OSError:
                    continue

    for default in _DEFAULT_EXTERNAL_PATHS:
        hit = Path(default) / name
        if hit.is_file() and os.access(hit, os.X_OK):
            try:
                resolved = hit.resolve(strict=True)
            except OSError:
                continue
            if not _inside_any(resolved, rejects):
                return resolved

    if not fixed_only:
        which = shutil.which(name)
        if which:
            resolved = Path(which).resolve()
            if not _inside_any(resolved, rejects) and resolved.is_file():
                return resolved

    raise ReviewIsolationError(f"executable_not_found:{name}")


def resolve_trusted_reviewer_executable(
    engine: str,
    *,
    reject_roots: Iterable[Path | str],
) -> Path:
    """Resolve a reviewer only from explicit installation locations.

    Ambient ``PATH`` is intentionally ignored. User-local launcher symlinks are
    accepted only when their resolved target remains inside the known provider
    installation roots; repository and worktree roots are always rejected.
    """
    engine_key = normalize_engine_name(engine)
    binary_name = {"grok": "grok", "codex": "codex", "claude": "claude"}.get(engine_key)
    if binary_name is None:
        raise ReviewIsolationError(f"trusted_reviewer_unsupported:{engine_key}")
    rejects = tuple(Path(root).resolve() for root in reject_roots)
    home = Path.home().resolve()
    candidates = [
        home / ".local" / "bin" / binary_name,
        *(Path(root) / binary_name for root in _DEFAULT_EXTERNAL_PATHS),
    ]
    allowed_targets = [
        Path("/usr/local").resolve(),
        Path("/opt/homebrew").resolve(),
        Path("/usr").resolve(),
        Path("/bin").resolve(),
    ]
    if engine_key == "codex":
        allowed_targets.extend(
            [
                home / ".hermes" / "node" / "lib" / "node_modules" / "@openai" / "codex",
                home / ".local" / "share" / "codex",
            ]
        )
    elif engine_key == "claude":
        allowed_targets.append(home / ".local" / "share" / "claude" / "versions")
    elif engine_key == "grok":
        allowed_targets.append(home / ".grok" / "bin")

    for candidate in candidates:
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if _inside_any(resolved, rejects):
            continue
        if not any(is_within(resolved, root) for root in allowed_targets):
            continue
        _file_sha256(resolved)
        return resolved
    raise ReviewIsolationError(f"trusted_reviewer_not_found:{engine_key}")


def _resolve_fixed_system_executable(name: str, *, reject_roots: Iterable[Path | str]) -> Path:
    """Resolve an OS sandbox launcher only from fixed system install roots."""
    rejects = tuple(Path(root).resolve() for root in reject_roots)
    for root in _DEFAULT_EXTERNAL_PATHS:
        candidate = Path(root) / name
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        resolved = candidate.resolve(strict=True)
        if not _inside_any(resolved, rejects):
            return resolved
    raise ReviewIsolationError(f"trusted_system_executable_not_found:{name}")


def safe_engine_path(reject_root: Path, *, extra: Iterable[Path] | None = None) -> str:
    """PATH for reviewer subprocesses: absolute entries outside the review root."""
    entries: list[str] = []
    reject = reject_root.resolve()

    def _add(path: Path) -> None:
        try:
            if not path.is_absolute():
                return
            resolved = path.resolve()
        except OSError:
            return
        if is_within(resolved, reject):
            return
        value = str(resolved)
        if value not in entries:
            entries.append(value)

    for path in extra or ():
        _add(path)
    for part in os.environ.get("PATH", "").split(os.pathsep):
        if part:
            _add(Path(part))
    for default in _DEFAULT_EXTERNAL_PATHS:
        _add(Path(default))
    return os.pathsep.join(entries)


def safe_proxy_url(value: str) -> bool:
    """True when proxy URL is credential-free and well-formed."""
    if not value or not value.strip():
        return False
    # Reject whitespace (malformed host / injection surface).
    if any(ch.isspace() for ch in value):
        return False
    try:
        candidate = value if "://" in value else f"http://{value}"
        parsed = urllib.parse.urlsplit(candidate)
        _ = parsed.port  # raises on invalid port
    except ValueError:
        return False
    host = parsed.hostname or ""
    if not host or any(ch.isspace() for ch in host) or "/" in host:
        return False
    if (
        "://" not in value
        and ":" not in value
        and "." not in value
        and host not in {"localhost"}
        and host != value
        and not value.startswith(host)
    ):
        return False
    return (
        parsed.scheme.lower() in {"http", "https", "socks", "socks4", "socks4a", "socks5", "socks5h"}
        and parsed.username is None
        and parsed.password is None
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
    )


def validate_proxy_env(env: Mapping[str, str]) -> None:
    """Fail closed on credentialed or malformed proxy configuration."""
    for key in _PROXY_ENV_KEYS:
        if key in {"NO_PROXY", "no_proxy"}:
            continue
        value = env.get(key)
        if value and not safe_proxy_url(value):
            raise ReviewIsolationError(f"unsafe_proxy:{key}:credentialed_or_malformed")


def is_sensitive_path(rel_path: str) -> bool:
    """True if a repo-relative path looks like credential storage."""
    normalized = rel_path.replace("\\", "/").strip("/")
    if not normalized:
        return False
    parts = normalized.split("/")
    # Sensitive parent directories always win. A benign-looking basename such
    # as ``tokens.css`` must not exempt ``.ssh/tokens.css`` or
    # ``credentials/token_helpers.py``.
    for part in parts[:-1]:
        if part.lower() in _SENSITIVE_PATH_PARTS | {"secrets", "credentials"}:
            return True
    if _BENIGN_TOKEN_NAME_RE.search(normalized):
        return False
    if _CREDENTIAL_FILE_RE.search(normalized):
        return True
    if _ENV_FILE_RE.search(normalized):
        # Keep ``.env.example`` / ``.env.sample`` reviewable.
        base = normalized.rsplit("/", 1)[-1].lower()
        if base in {".env.example", ".env.sample", ".env.template", ".env.sample.local"}:
            return False
        return not base.endswith((".example", ".sample", ".template"))
    for part in parts:
        if part.lower() in _SENSITIVE_PATH_PARTS:
            return True
        if part.lower() in {"secrets", "credentials"}:
            return True
    return bool(_SENSITIVE_NAME_RE.search(normalized))


def secret_like_findings(text: str) -> list[str]:
    """Return diagnostic codes for secret-like content (empty if clean)."""
    findings: list[str] = []
    value_found = False
    assignment_found = False
    # Both patterns are line-bounded. Scanning per line avoids pathological
    # backtracking and large transient matches on multi-megabyte tracked files.
    for line in text.splitlines():
        if not value_found and _SECRET_VALUE_RE.search(line):
            value_found = True
        if not assignment_found and _SECRET_ASSIGNMENT_RE.search(line):
            assignment_found = True
        if value_found and assignment_found:
            break
    if value_found:
        findings.append("secret_value_pattern")
    if assignment_found:
        findings.append("secret_assignment")
    return findings


def preflight_review_inputs(
    *,
    paths: Iterable[str],
    texts: Mapping[str, str] | None = None,
) -> None:
    """Fail closed before engine invocation on sensitive paths / secret text.

    Benign design-token fixtures and ordinary uses of the word ``token`` do
    not trip this gate. Never truncates input — caller still owns size policy.
    """
    for path in paths:
        if is_sensitive_path(path):
            raise ReviewIsolationError(f"sensitive_path:{path}")
    if not texts:
        return
    for path, text in texts.items():
        if is_sensitive_path(path):
            raise ReviewIsolationError(f"sensitive_path:{path}")
        hits = secret_like_findings(text)
        if hits:
            raise ReviewIsolationError(f"secret_like_content:{path}:{','.join(hits)}")


def build_reviewer_env(
    *,
    engine: str,
    reject_root: Path,
    source: Mapping[str, str] | None = None,
    home: str | None = None,
    tmpdir: str | None = None,
    forward_auth: bool = True,
) -> dict[str, str]:
    """Minimal allowlisted environment for a reviewer subprocess.

    Strips process-injection and Git override variables, forwards only the
    selected engine's authentication material, rejects credentialed proxies,
    and builds a PATH that cannot resolve repo-local shims.
    """
    raw = dict(source if source is not None else os.environ)
    engine_key = normalize_engine_name(engine)
    if engine_key == "codex" and raw.get("OPENAI_BASE_URL", "").strip():
        raise ReviewIsolationError("provider_endpoint_override_forbidden:OPENAI_BASE_URL")
    auth_keys = _ENGINE_AUTH_ENV.get(engine_key, frozenset())
    # Also accept historical "grok-build" keys from the table via normalize.
    if engine_key == "grok":
        auth_keys = auth_keys | _ENGINE_AUTH_ENV.get("grok-build", frozenset())

    env: dict[str, str] = {}
    for key, value in raw.items():
        if key in _PROCESS_INJECTION_ENV_KEYS:
            continue
        if key in _UNRELATED_CREDENTIAL_ENV and key not in auth_keys:
            continue
        if key.startswith("GIT_CONFIG_KEY_") or key.startswith("GIT_CONFIG_VALUE_"):
            continue
        # Strip editor / shell startup and tool overrides by name family.
        upper = key.upper()
        if upper.endswith(("_EDITOR", "_PAGER")) and key not in auth_keys:
            continue
        if key in auth_keys and forward_auth:
            env[key] = value
            continue
        if key in _COMMON_ENV_ALLOWLIST:
            env[key] = value
            continue
        if key.startswith("LC_"):
            env[key] = value

    # Explicitly drop any credential that slipped through via name allowlist.
    for key in list(env):
        if key in _UNRELATED_CREDENTIAL_ENV and key not in auth_keys:
            env.pop(key, None)

    validate_proxy_env(env)

    env["PATH"] = safe_engine_path(reject_root)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["LANG"] = env.get("LANG") or "C.UTF-8"
    env["LC_ALL"] = env.get("LC_ALL") or "C.UTF-8"

    if home is not None:
        env["HOME"] = home
    elif "HOME" in env:
        # Reject HOME that points into the reviewed tree (could load project config).
        try:
            if is_within(Path(env["HOME"]), reject_root):
                env.pop("HOME", None)
        except (OSError, TypeError):
            env.pop("HOME", None)

    if tmpdir is not None:
        env["TMPDIR"] = tmpdir
        env["TMP"] = tmpdir
        env["TEMP"] = tmpdir

    if engine_key == "claude":
        env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"

    # Mark the subprocess as isolation-bound (non-secret).
    env["LU_REVIEW_ISOLATION"] = "1"
    env["LU_REVIEW_ISOLATION_POLICY"] = ISOLATION_POLICY_VERSION
    return env


def required_capabilities_for(engine: str) -> frozenset[str]:
    """Return the isolation capabilities an engine must prove."""
    key = normalize_engine_name(engine)
    # Accept both grok and grok-build table keys.
    caps = _ENGINE_REQUIRED_CAPABILITIES.get(key) or _ENGINE_REQUIRED_CAPABILITIES.get(engine.strip().lower())
    if caps is None:
        raise ReviewIsolationError(f"unsupported_review_engine:{engine}")
    return caps


def detect_engine_capabilities(
    engine: str,
    binary: Path,
    *,
    help_text: str | None = None,
    version_text: str = "",
    policy_enforced: Mapping[str, bool] | None = None,
) -> EngineCapabilities:
    """Feature-detect isolation flags from help/version and active enforcement.

    Help/version text is the primary source. A capability may also be granted
    when ``policy_enforced`` proves the enforcement mechanism is active on the
    real launch path (for example OS sandbox verified, nested multi-agent
    disabled in argv, disposable HOME with no project load). Desired states
    and mere instructions never count.

    When ``help_text`` is omitted the binary is not executed — callers that need
    live detection must supply help/version output themselves or use
    :func:`probe_engine_capabilities`. Missing required capabilities are
    recorded; use :func:`require_engine_isolation` to fail closed.
    """
    engine_key = normalize_engine_name(engine)
    required = required_capabilities_for(engine_key)
    text = (help_text or "").lower()
    found: set[str] = set()
    enforced = {key: bool(value) for key, value in dict(policy_enforced or {}).items() if value}

    if engine_key == "claude":
        if "--safe-mode" in text or "--bare" in text or "--setting-sources" in text:
            found.add("disable_project_instructions")
        # ``--bare`` still permits slash-invoked skills.  Only safe mode is a
        # current native proof that skills, plugins, hooks, custom agents, and
        # commands are all disabled on the real review path.
        if "--safe-mode" in text:
            found.add("disable_hooks_skills_plugins")
        if "--setting-sources" in text:
            found.add("disable_project_instructions")
        if "--strict-mcp-config" in text:
            found.add("disable_mcp")
        if "--json-schema" in text:
            found.add("structured_output")
        if "--disallowedtools" in text or "--tools" in text or "--bare" in text:
            found.add("read_only_or_no_write_tools")
        if enforced.get("no_nested_reviewers"):
            found.add("no_nested_reviewers")
        elif "--bare" in text and ("--tools" in text or "tools" in text):
            # Empty-tools + bare is the nested-reviewer denial mechanism.
            found.add("no_nested_reviewers")
    elif engine_key == "codex":
        sandbox_flag = bool(
            re.search(r"(?<!\S)(?:-s(?:,|\s|$)|--sandbox(?:[=,\s]|$))", text)
        )
        if "--ignore-user-config" in text:
            found.add("ignore_user_config")
        if "--ignore-rules" in text:
            found.add("ignore_project_rules")
        if sandbox_flag or "--skip-git-repo-check" in text:
            found.add("sandbox_or_empty_workspace")
        if (sandbox_flag and "read-only" in text) or enforced.get("read_only_or_no_write_tools"):
            found.add("read_only_or_no_write_tools")
        # The actual isolated argv, not a help-text mention, must carry the
        # nested-reviewer denial mechanism (--disable multi_agent).
        if enforced.get("no_nested_reviewers"):
            found.add("no_nested_reviewers")
    elif engine_key == "agy":
        # AGY has no proven native suppression for repository instructions,
        # MCP/hooks, or nested reviewers. Never manufacture those capabilities
        # from an OS sandbox assertion; isolated AGY launches are refused.
        if "--sandbox" in text:
            found.add("os_sandbox_required")
        if "--mode" in text or "plan" in text or "accept-edits" in text:
            found.add("read_only_or_no_write_tools")
    elif engine_key in {"grok", "grok-build"}:
        if "plan" in text or "permission" in text or "bypasspermissions" in text:
            found.add("plan_or_read_only_mode")
        if "--deny" in text or "deny" in text or "--disallowed-tools" in text:
            found.add("deny_write_shell")
        if enforced.get("no_nested_reviewers") or "--disallowed-tools" in text or "--deny" in text:
            found.add("no_nested_reviewers")
    elif engine_key == "gemini":
        if "approval-mode" in text or "yolo" in text or "read-only" in text:
            found.add("read_only_or_no_write_tools")
        if enforced.get("no_nested_reviewers"):
            found.add("no_nested_reviewers")

    missing = frozenset(required - found)
    return EngineCapabilities(
        engine=engine_key,
        binary=binary,
        version_text=version_text,
        capabilities=frozenset(found),
        missing=missing,
    )


def probe_engine_help(
    binary: Path,
    *,
    timeout: float = 8.0,
    sandbox: SandboxCapability | None = None,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> str:
    """Probe the exact binary, optionally only through the verified sandbox."""
    chunks: list[str] = []
    for args in ([str(binary), "--help"], [str(binary), "--version"], [str(binary), "exec", "--help"]):
        command = wrap_argv_with_sandbox(args, sandbox) if sandbox is not None else args
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=dict(env) if env is not None else None,
                cwd=str(cwd) if cwd is not None else None,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        chunks.append(proc.stdout or "")
        chunks.append(proc.stderr or "")
    return "\n".join(chunks)


def require_supported_engine_version(engine: str, version_text: str) -> None:
    """Require a proven supported version for engines with a minimum."""
    engine_key = normalize_engine_name(engine)
    if engine_key != "claude":
        return
    version = _parse_claude_semver(version_text)
    if version is None:
        raise ReviewIsolationError("engine_version_unproven:claude")
    if version < CLAUDE_MIN_SUPPORTED_CLI_VERSION:
        rendered = ".".join(str(part) for part in version)
        minimum = ".".join(str(part) for part in CLAUDE_MIN_SUPPORTED_CLI_VERSION)
        raise ReviewIsolationError(
            f"engine_version_unsupported:claude:{rendered}:minimum={minimum}"
        )


def probe_engine_capabilities(
    engine: str,
    binary: Path,
    *,
    timeout: float = 8.0,
) -> EngineCapabilities:
    """Live help/version probe + capability feature detection (fail-closed)."""
    help_text = probe_engine_help(binary, timeout=timeout)
    return detect_engine_capabilities(
        engine,
        binary,
        help_text=help_text,
        version_text=help_text[:4000],
    )


def require_engine_isolation(capabilities: EngineCapabilities) -> None:
    """Refuse engines that cannot prove the required isolation contract."""
    if capabilities.ok:
        return
    missing = ", ".join(sorted(capabilities.missing))
    raise ReviewIsolationError(f"engine_isolation_unproven:{capabilities.engine}:{missing}")


def build_claude_review_argv(
    binary: Path,
    *,
    prompt: str,
    json_schema: Mapping[str, Any],
    model: str | None = None,
    capabilities: EngineCapabilities | None = None,
) -> list[str]:
    """Argv for an isolated Claude review invocation (no write/MCP/project load)."""
    if capabilities is not None:
        require_engine_isolation(capabilities)
    cmd = [str(binary.resolve()), "-p", "--output-format", "text"]
    if capabilities is None or "disable_project_instructions" in capabilities.capabilities:
        cmd.extend(
            [
                "--safe-mode",
                "--setting-sources",
                "",
                "--tools",
                "Read,Grep,Glob",
                "--json-schema",
                json.dumps(json_schema, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
            ]
        )
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["--", prompt])
    return cmd


def build_codex_review_argv(
    binary: Path,
    *,
    workspace: Path,
    prompt_via_stdin: bool = True,
    model: str | None = None,
    capabilities: EngineCapabilities | None = None,
) -> list[str]:
    """Argv for an isolated Codex review invocation."""
    if capabilities is not None:
        require_engine_isolation(capabilities)
    cmd = [
        str(binary.resolve()),
        "exec",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ignore-rules",
        "-s",
        "read-only",
        "-C",
        str(workspace),
        "--color",
        "never",
    ]
    if model:
        cmd.extend(["-m", model])
    if prompt_via_stdin:
        cmd.append("-")
    return cmd


def review_isolation_tool_config(engine: str) -> dict[str, object]:
    """tool_config fragment adapters should merge for isolated review runs.

    Keys match what each adapter actually consumes. Secret values must never
    be placed here — only non-secret policy flags and path strings.
    """
    engine_key = normalize_engine_name(engine)
    if engine_key == "agy":
        raise ReviewIsolationError(
            "agy_isolated_review_unsupported: native project-instruction, MCP, "
            "hook, and nested-reviewer suppression is not proven"
        )
    base: dict[str, object] = {
        "review_isolation": True,
        "isolation_policy_version": ISOLATION_POLICY_VERSION,
        "disable_project_instructions": True,
        "disable_hooks": True,
        "disable_skills": True,
        "disable_plugins": True,
        "disable_mcp": True,
        "disable_memory": True,
        "disable_sessions": True,
        "deny_write_tools": True,
        "deny_nested_reviewers": True,
        "deny_installs_tests_formatters": True,
    }
    if engine_key == "claude":
        base.update(
            {
                "allowed_tools": "Read,Grep,Glob",
                # ``--safe-mode`` suppresses project/plugin/hook loading while
                # preserving the normal subscription OAuth path. Claude Code
                # 2.1.211 deliberately limits ``--bare`` to API-key auth.
                "use_bare": False,
                "setting_sources": "",
                "strict_mcp_config": True,
                "output_format": "stream-json",
            }
        )
    elif engine_key == "codex":
        base.update(
            {
                "disable_features": [
                    "shell_tool",
                    "goals",
                    "browser_use",
                    "browser_use_external",
                    "in_app_browser",
                    "computer_use",
                    "image_generation",
                    "apps",
                    "enable_mcp_apps",
                    "plugins",
                    "plugin_sharing",
                    "skill_mcp_dependency_install",
                    "tool_suggest",
                    "auth_elicitation",
                    "tool_call_mcp_elicitation",
                    "hooks",
                    "multi_agent",
                ],
                "ignore_user_config": True,
                "ignore_rules": True,
            }
        )
    elif engine_key in {"grok", "grok-build"}:
        # Keys match GrokBuildAdapter: disallowed_tools → --disallowed-tools,
        # permission mode comes from mode="read-only" → plan, plus --deny rules.
        base.update(
            {
                "disallowed_tools": "Shell,Write,Edit,Bash,MultiEdit,NotebookEdit,search_replace",
                "allowed_tools": "Read,Grep,Glob",
                "permission_mode": "bypassPermissions",
                "review_deny_tools": [
                    "Write",
                    "Edit",
                    "MultiEdit",
                    "NotebookEdit",
                    "search_replace",
                    "Bash",
                    "Shell",
                ],
            }
        )
    return base


def canonical_isolated_review_schema(changed_paths: Sequence[str]) -> dict[str, Any]:
    """Return the canonical review schema constrained to the frozen surface.

    Target identity remains parent-owned isolation evidence; reviewer output
    uses the repository-wide ``code-review-findings.v1`` contract unchanged.
    """
    from scripts.review.review_contract import load_schema

    paths = list(dict.fromkeys(changed_paths))
    if not all(isinstance(path, str) and path for path in paths):
        raise ReviewIsolationError("review_schema_changed_paths_invalid")
    schema = copy.deepcopy(load_schema())
    # Claude CLI validates --json-schema with an Ajv instance that does not
    # register the Draft 2020-12 metaschema. The explicit declaration is
    # transport metadata, not part of the payload contract; removing it keeps
    # the canonical constraints while allowing the provider to compile them.
    schema.pop("$schema", None)
    findings = schema["properties"]["findings"]
    if paths:
        schema["$defs"]["location"]["properties"]["path"] = {
            "type": "string",
            "enum": paths,
        }
    else:
        findings["maxItems"] = 0
    return schema


def transport_isolated_review_schema() -> dict[str, Any]:
    """Return the bounded argv schema used only for provider transport.

    Exact changed-path membership remains enforced by the parent with
    :func:`canonical_isolated_review_schema`. Embedding every changed path in
    one ``--json-schema`` argument can exceed the kernel's per-argument limit.
    """
    from scripts.review.review_contract import load_schema

    schema = copy.deepcopy(load_schema())
    schema.pop("$schema", None)
    return schema


def _real(path: Path | str) -> str:
    return os.path.realpath(str(path))


def _engine_auth_read_paths(engine: str, home: Path | None = None) -> list[str]:
    """Legacy helper — always empty. Auth is staged, not host-tree granted."""
    _ = (engine, home)
    return []


def _resolve_trusted_runtime_command(name: str, *, reject_roots: Iterable[Path | str]) -> Path | None:
    """Resolve a shebang runtime from fixed host install locations, not PATH."""
    home = Path.home().resolve()
    candidates = [
        home / ".local" / "bin" / name,
        home / ".hermes" / "node" / "bin" / name,
        *(Path(root) / name for root in _DEFAULT_EXTERNAL_PATHS),
    ]
    rejects = tuple(Path(root).resolve() for root in reject_roots)
    allowed = (
        Path("/usr/local").resolve(),
        Path("/opt/homebrew").resolve(),
        Path("/usr").resolve(),
        home / ".hermes" / "node",
    )
    for candidate in candidates:
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if _inside_any(resolved, rejects):
            continue
        if any(is_within(resolved, root) for root in allowed):
            return resolved
    return None


def resolve_runtime_closure(executable: Path, *, reject_roots: Iterable[Path | str] = ()) -> list[str]:
    """Exact trusted executable plus narrow runtime dependencies.

    Never returns an entire home/tool tree. For Node CLIs this includes the
    resolved script, its package root (with nested ``node_modules`` of that
    package only), and the interpreter binary/parent. For native binaries
    this is the resolved binary and its parent directory.
    """
    paths: list[str] = []
    seen: set[str] = set()

    def _add(path: Path | str | None) -> None:
        if path is None:
            return
        try:
            real = _real(path)
        except OSError:
            return
        if not real or real in seen:
            return
        # Never allow a user's entire home as a "runtime" root.
        try:
            home = _real(Path.home())
        except OSError:
            home = ""
        if home and real == home:
            return
        seen.add(real)
        paths.append(real)

    try:
        resolved = executable.expanduser().resolve(strict=True)
    except OSError as exc:
        raise ReviewIsolationError(f"runtime_closure_unresolved:{executable}") from exc
    _add(resolved)
    _add(resolved.parent)

    # Shebang scripts (e.g. codex → node).
    try:
        with resolved.open("rb") as handle:
            first = handle.readline(256)
    except OSError:
        first = b""
    if first.startswith(b"#!"):
        shebang = first[2:].decode("utf-8", errors="replace").strip()
        parts = shebang.split()
        if parts:
            if parts[0].endswith("env") and len(parts) >= 2:
                interp_name = parts[1]
                interp = _resolve_trusted_runtime_command(interp_name, reject_roots=reject_roots)
                if interp:
                    _add(interp)
                    _add(interp.parent)
                else:
                    raise ReviewIsolationError(f"runtime_interpreter_untrusted:{interp_name}")
            else:
                interp_path = Path(parts[0])
                if interp_path.is_file():
                    _add(interp_path)
                    _add(interp_path.resolve().parent)

    # Node package root: walk up to the package that owns this script.
    package_root: Path | None = None
    for parent in (resolved.parent, *resolved.parents):
        pkg_json = parent / "package.json"
        if not pkg_json.is_file():
            continue
        # Prefer the package directory (not the top-level node_modules folder).
        if parent.name == "node_modules":
            continue
        package_root = parent
        break
    if package_root is not None:
        _add(package_root)
        nested = package_root / "node_modules"
        if nested.is_dir():
            _add(nested)

    # Native Claude versions live under ~/.local/share/claude/versions/<ver>.
    # Allow that exact version directory only (not all of ~/.local).
    try:
        parts = resolved.parts
        if "versions" in parts:
            idx = parts.index("versions")
            if idx + 1 < len(parts):
                version_dir = Path(*parts[: idx + 2])
                _add(version_dir)
    except (ValueError, OSError):
        pass

    return paths


def stage_engine_auth(
    engine: str,
    *,
    write_home: Path,
    source_home: Path | None = None,
    source_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Copy only selected auth files into disposable HOME.

    Returns selected auth/runtime env overrides (e.g. CODEX_HOME or one Claude
    OAuth access token). Never stages whole provider trees (history, sessions,
    skills, plugins, neighboring state). Values never enter evidence or logs.
    """
    engine_key = normalize_engine_name(engine)
    src_home = (source_home or Path.home()).expanduser().resolve()
    source = os.environ if source_env is None else source_env
    configured_codex_home: Path | None = None
    if engine_key == "codex" and source_home is None:
        raw_codex_home = source.get("CODEX_HOME", "").strip()
        if raw_codex_home:
            candidate = Path(raw_codex_home).expanduser()
            if not candidate.is_absolute():
                raise ReviewIsolationError("auth_stage_codex_home_not_absolute")
            configured_codex_home = candidate.resolve()
    write_home.mkdir(parents=True, exist_ok=True)
    for rel in _ENGINE_AUTH_STAGE_FILES.get(engine_key, ()):
        if engine_key == "codex" and configured_codex_home is not None:
            src = configured_codex_home / "auth.json"
        else:
            src = src_home / rel
        if is_within(src.resolve(strict=False), write_home.resolve()):
            raise ReviewIsolationError(f"auth_stage_source_inside_write_home:{engine_key}")
        try:
            source_stat = src.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ReviewIsolationError(f"auth_stage_source_failed:{engine_key}:{type(exc).__name__}") from exc
        if stat.S_ISLNK(source_stat.st_mode) or not stat.S_ISREG(source_stat.st_mode):
            raise ReviewIsolationError(f"auth_stage_source_not_regular:{engine_key}:{rel}")
        if hasattr(os, "getuid") and source_stat.st_uid != os.getuid():
            raise ReviewIsolationError(f"auth_stage_source_owner:{engine_key}:{rel}")
        if stat.S_IMODE(source_stat.st_mode) & 0o077:
            raise ReviewIsolationError(f"auth_stage_source_permissions:{engine_key}:{rel}")
        dest = write_home / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            source_fd = os.open(src, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                opened_stat = os.fstat(source_fd)
                if (opened_stat.st_dev, opened_stat.st_ino) != (source_stat.st_dev, source_stat.st_ino):
                    raise ReviewIsolationError(f"auth_stage_source_raced:{engine_key}:{rel}")
                dest_fd = os.open(
                    dest,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o400,
                )
                try:
                    while True:
                        chunk = os.read(source_fd, 1024 * 1024)
                        if not chunk:
                            break
                        _write_fd_all(dest_fd, chunk)
                finally:
                    os.close(dest_fd)
                closed_stat = os.fstat(source_fd)
                if (
                    closed_stat.st_dev,
                    closed_stat.st_ino,
                    closed_stat.st_size,
                    closed_stat.st_mtime_ns,
                    closed_stat.st_ctime_ns,
                ) != (
                    opened_stat.st_dev,
                    opened_stat.st_ino,
                    opened_stat.st_size,
                    opened_stat.st_mtime_ns,
                    opened_stat.st_ctime_ns,
                ):
                    raise ReviewIsolationError(f"auth_stage_source_raced:{engine_key}:{rel}")
            finally:
                os.close(source_fd)
        except OSError as exc:
            raise ReviewIsolationError(f"auth_stage_failed:{engine_key}:{type(exc).__name__}") from exc

    env_overrides: dict[str, str] = {}
    if engine_key == "codex":
        codex_home = write_home / ".codex"
        codex_home.mkdir(parents=True, exist_ok=True)
        env_overrides["CODEX_HOME"] = str(codex_home)
    elif engine_key == "claude":
        # Keep disposable config empty; safe-mode can use a narrowly staged
        # subscription token without exposing host Claude state.
        (write_home / ".claude").mkdir(parents=True, exist_ok=True)
        has_env_auth = any(
            source.get(key)
            for key in (
                "ANTHROPIC_API_KEY",
                "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_API_KEY",
                "CLAUDE_CODE_OAUTH_TOKEN",
            )
        )
        if not has_env_auth and platform.system() == "Darwin":
            security = Path("/usr/bin/security")
            if security.is_file():
                try:
                    completed = subprocess.run(
                        [
                            str(security),
                            "find-generic-password",
                            "-s",
                            "Claude Code-credentials",
                            "-w",
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5,
                        env={
                            "HOME": str(src_home),
                            "PATH": "/usr/bin:/bin",
                            "LANG": "C.UTF-8",
                        },
                    )
                    credential = json.loads(completed.stdout) if completed.returncode == 0 else {}
                    oauth = credential.get("claudeAiOauth", {})
                    token = oauth.get("accessToken") if isinstance(oauth, dict) else None
                    expires_at = oauth.get("expiresAt") if isinstance(oauth, dict) else None
                    if isinstance(expires_at, int) and expires_at > 10_000_000_000:
                        expires_at //= 1000
                    token_fresh = not isinstance(expires_at, int) or expires_at > int(time.time()) + 60
                    if (
                        isinstance(token, str)
                        and 20 <= len(token) <= 8192
                        and "\n" not in token
                        and "\0" not in token
                        and token_fresh
                    ):
                        env_overrides["CLAUDE_CODE_OAUTH_TOKEN"] = token
                except (
                    OSError,
                    subprocess.SubprocessError,
                    json.JSONDecodeError,
                    TypeError,
                ):
                    # Missing keychain auth is not fabricated; Claude fails
                    # explicitly unless another selected auth source exists.
                    pass
    return env_overrides


def _canonical_sandbox_read_roots(
    *,
    snapshot_root: Path,
    write_root: Path,
    runtime_reads: Sequence[Path | str],
) -> tuple[str, ...]:
    """Least-privilege roots shared by probes and real launches.

    Fixed host paths retain both their lexical spelling and canonical target
    so blank-root bwrap preserves merged-/usr aliases such as ``/bin`` and
    resolver-file aliases. Caller-controlled roots remain canonical-only.
    """
    roots: set[str] = set()
    forbidden_exact = {
        "/",
        "/tmp",
        "/private/tmp",
        "/private/var",
        "/var",
        "/private/var/folders",
        _real(Path.home()),
    }
    snap = _real(snapshot_root)
    write = _real(write_root)
    runtime_exact = {_real(item) for item in runtime_reads}

    def _allowed_target(real: str) -> bool:
        if real in forbidden_exact and real not in {snap, write}:
            return False
        return not (
            (real.startswith("/private/var/folders") or real.startswith("/var/folders"))
            and real not in {snap, write}
            and real not in runtime_exact
            and not real.startswith(snap + os.sep)
            and not real.startswith(write + os.sep)
        )

    # These values are module-owned trusted constants. Preserve their literal
    # absolute paths only after the canonical target passes the broad-root
    # filters. Never do this for caller-provided runtime aliases.
    for candidate in (*_SYSTEM_READ_SUBPATHS, *_NETWORK_READ_PATHS):
        path = Path(candidate)
        if not path.exists():
            continue
        real = _real(path)
        if not _allowed_target(real):
            continue
        literal = os.path.abspath(os.path.normpath(str(path)))
        if not literal.startswith("/"):
            raise ReviewIsolationError(f"sandbox_fixed_root_not_absolute:{candidate}")
        roots.add(literal)
        roots.add(real)

    for candidate in (snapshot_root, write_root, *runtime_reads):
        path = Path(candidate)
        if not path.exists():
            continue
        real = _real(path)
        if not _allowed_target(real):
            continue
        roots.add(real)
    if snap not in roots or write not in roots:
        raise ReviewIsolationError("sandbox_root_set_incomplete")
    ordered = sorted(roots, key=lambda value: (len(Path(value).parts), value))
    compact: list[str] = []
    for value in ordered:
        path = Path(value)
        # Lexical comparison is intentional: resolving here would collapse
        # /bin beneath /usr again and remove the alias bwrap must recreate.
        if any(path == Path(parent) or path.is_relative_to(Path(parent)) for parent in compact):
            continue
        compact.append(value)
    return tuple(sorted(compact))


def _sandbox_metadata_roots(read_roots: Sequence[str]) -> tuple[str, ...]:
    """Literal ancestors needed for realpath without granting file data."""
    metadata: set[str] = {"/"}
    for raw in read_roots:
        current = Path(raw)
        while current != Path("/"):
            metadata.add(str(current))
            current = current.parent
    return tuple(sorted(metadata))


def build_macos_sandbox_profile(
    *,
    snapshot_root: Path,
    write_root: Path,
    extra_read_roots: Sequence[Path | str] = (),
    profile_path: Path,
    network_allowed: bool = True,
) -> Path:
    """Write a seatbelt profile: read snapshot + system + exact runtime; write write_root."""
    snap = _real(snapshot_root)
    write = _real(write_root)
    reads = _canonical_sandbox_read_roots(
        snapshot_root=Path(snap),
        write_root=Path(write),
        runtime_reads=extra_read_roots,
    )
    metadata_reads = _sandbox_metadata_roots(reads)

    def _seatbelt_literal(value: str) -> str:
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    def _subpath_list(paths: Iterable[str]) -> str:
        return "\n  ".join(f"(subpath {_seatbelt_literal(p)})" for p in paths)

    def _literal_list(paths: Iterable[str]) -> str:
        return "\n  ".join(f"(literal {_seatbelt_literal(p)})" for p in paths)

    network_rule = "(allow network*)" if network_allowed else ""

    body = f"""(version 1)
(deny default)
(import "system.sb")
(allow process*)
(allow sysctl*)
(allow mach*)
(allow signal)
{network_rule}
(allow iokit*)
(allow file-read-metadata
  {_literal_list(metadata_reads)}
)
(allow file-read*
  {_subpath_list(reads)}
)
(allow file-write*
  (subpath {_seatbelt_literal(write)})
)
(allow file-ioctl
  (literal "/dev/dtracehelper")
  (literal "/dev/null")
  (literal "/dev/tty")
  (literal "/dev/zero")
  (literal "/dev/urandom")
  (literal "/dev/random")
)
(allow file-write-data
  (literal "/dev/null")
  (literal "/dev/dtracehelper")
  (literal "/dev/tty")
)
(allow file-read-data
  (literal "/dev/null")
  (literal "/dev/zero")
  (literal "/dev/urandom")
  (literal "/dev/random")
)
"""
    profile_path.write_text(body, encoding="utf-8")
    profile_path.chmod(0o444)
    return profile_path


def verify_macos_sandbox(
    *,
    sandbox_exec: Path,
    profile_path: Path,
    snapshot_root: Path,
    write_root: Path,
    denied_probe_path: Path,
    read_roots: tuple[str, ...],
    metadata_roots: tuple[str, ...],
) -> SandboxCapability:
    """Prove the profile allows snapshot reads and denies unrelated host paths."""
    # Snapshot is read-only; probe against an existing evidence file (or metadata).
    probe_ok: Path | None = None
    for candidate in (
        snapshot_root / ".review-snapshot-metadata.json",
        snapshot_root / "README.md",
        snapshot_root / ".review-bundle" / "manifest.json",
    ):
        if candidate.is_file():
            probe_ok = candidate
            break
    if probe_ok is None:
        for path in snapshot_root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                probe_ok = path
                break
    if probe_ok is None:
        raise ReviewIsolationError("sandbox_probe_no_readable_snapshot_file")

    allowed = subprocess.run(
        [str(sandbox_exec), "-f", str(profile_path), "/bin/cat", str(probe_ok)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if allowed.returncode != 0 or not (allowed.stdout or "").strip():
        raise ReviewIsolationError(f"sandbox_probe_allow_failed:rc={allowed.returncode}:{(allowed.stderr or '')[:200]}")
    denied = subprocess.run(
        [
            str(sandbox_exec),
            "-f",
            str(profile_path),
            "/bin/cat",
            str(denied_probe_path),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    denied_out = (denied.stdout or "") + (denied.stderr or "")
    if denied.returncode == 0:
        raise ReviewIsolationError(f"sandbox_probe_deny_failed:read_succeeded:{denied_probe_path}")
    write_probe_path = write_root / "sandbox-write-probe"
    write_probe = subprocess.run(
        [
            str(sandbox_exec),
            "-f",
            str(profile_path),
            "/bin/sh",
            "-c",
            'printf w > "$1" && cat "$1"',
            "review-probe",
            str(write_probe_path),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if write_probe.returncode != 0 or "w" not in (write_probe.stdout or ""):
        raise ReviewIsolationError(f"sandbox_probe_write_failed:rc={write_probe.returncode}")
    # Snapshot must not be writable.
    subprocess.run(
        [
            str(sandbox_exec),
            "-f",
            str(profile_path),
            "/bin/sh",
            "-c",
            'printf bad > "$1"',
            "review-probe",
            str(snapshot_root / "should-fail"),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if (snapshot_root / "should-fail").exists():
        raise ReviewIsolationError("sandbox_probe_snapshot_writable")
    detail = f"deny_rc={denied.returncode};deny_snip={denied_out[:80]!r}"
    return SandboxCapability(
        mechanism="macos-sandbox-exec",
        binary=sandbox_exec,
        profile_path=profile_path,
        read_roots=read_roots,
        write_root=str(write_root),
        verified=True,
        metadata_roots=metadata_roots,
        probe_detail=detail,
        network_allowed=True,
    )


def prepare_host_sandbox(
    *,
    engine: str,
    snapshot_root: Path,
    write_root: Path,
    reject_root: Path,
    reject_roots: Sequence[Path | str] = (),
    profile_dir: Path | None = None,
    runtime_reads: Sequence[Path | str] = (),
    executable: Path | None = None,
    network_allowed: bool = True,
) -> SandboxCapability:
    """Build and verify an OS sandbox for the reviewer process (fail closed)."""
    system = platform.system()
    snap, write = validate_private_review_roots(
        snapshot_root=snapshot_root,
        write_root=write_root,
        reject_root=reject_root,
        reject_roots=reject_roots,
    )

    extra_reads: list[Path] = [Path(p) for p in runtime_reads]
    if executable is not None:
        for p in resolve_runtime_closure(Path(executable), reject_roots=(reject_root,)):
            extra_reads.append(Path(p))
    # Auth is staged into write_root/home — no host provider-tree grants.
    read_roots = _canonical_sandbox_read_roots(
        snapshot_root=snap,
        write_root=write,
        runtime_reads=extra_reads,
    )
    metadata_roots = _sandbox_metadata_roots(read_roots)

    if system == "Darwin":
        try:
            sandbox_exec = _resolve_fixed_system_executable("sandbox-exec", reject_roots=(reject_root, *reject_roots))
        except ReviewIsolationError as exc:
            raise ReviewIsolationError(f"sandbox_unavailable:macos_sandbox_exec:{exc}") from exc
        parent = profile_dir or write
        parent.mkdir(parents=True, exist_ok=True)
        profile_path = parent / "review-sandbox.sb"
        # Profile must be writable while we create it.
        if profile_path.exists():
            profile_path.chmod(0o644)
        build_macos_sandbox_profile(
            snapshot_root=snap,
            write_root=write,
            extra_read_roots=extra_reads,
            profile_path=profile_path,
            network_allowed=network_allowed,
        )
        denied_fd, denied_raw = tempfile.mkstemp(prefix="lu-review-deny-probe-")
        denied = Path(denied_raw)
        try:
            with os.fdopen(denied_fd, "wb") as handle:
                handle.write(b"deny-sentinel\n")
            capability = verify_macos_sandbox(
                sandbox_exec=sandbox_exec,
                profile_path=profile_path,
                snapshot_root=snap,
                write_root=write,
                denied_probe_path=denied,
                read_roots=read_roots,
                metadata_roots=metadata_roots,
            )
            return SandboxCapability(
                **{**capability.__dict__, "network_allowed": network_allowed}
            )
        finally:
            with contextlib.suppress(OSError):
                denied.unlink()

    if system == "Linux":
        try:
            bwrap_path = _resolve_fixed_system_executable("bwrap", reject_roots=(reject_root, *reject_roots))
        except ReviewIsolationError as exc:
            raise ReviewIsolationError(
                "sandbox_unavailable:linux_bwrap_missing:install bubblewrap or refuse this engine on this host"
            ) from exc
        probe_ok: Path | None = None
        for candidate in (
            snap / ".review-snapshot-metadata.json",
            snap / "README.md",
        ):
            if candidate.is_file():
                probe_ok = candidate
                break
        if probe_ok is None:
            for path in snap.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    probe_ok = path
                    break
        if probe_ok is None:
            raise ReviewIsolationError("sandbox_probe_no_readable_snapshot_file")
        provisional = SandboxCapability(
            mechanism="linux-bwrap",
            binary=bwrap_path,
            profile_path=None,
            read_roots=read_roots,
            write_root=str(write),
            verified=True,
            metadata_roots=metadata_roots,
            probe_detail="bwrap_probe_pending",
            network_allowed=network_allowed,
        )
        cmd = wrap_argv_with_sandbox(["/bin/cat", str(probe_ok)], provisional)
        allowed = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        if allowed.returncode != 0 or not (allowed.stdout or "").strip():
            raise ReviewIsolationError(f"sandbox_probe_allow_failed:bwrap:rc={allowed.returncode}")
        denied_fd, denied_raw = tempfile.mkstemp(prefix="lu-review-deny-probe-")
        denied = Path(denied_raw)
        try:
            with os.fdopen(denied_fd, "wb") as handle:
                handle.write(b"deny-sentinel\n")
            denied_run = subprocess.run(
                wrap_argv_with_sandbox(["/bin/cat", str(denied)], provisional),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if denied_run.returncode == 0:
                raise ReviewIsolationError("sandbox_probe_deny_failed:bwrap")
            write_probe = write / "sandbox-write-probe"
            writable = subprocess.run(
                wrap_argv_with_sandbox(
                    [
                        "/bin/sh",
                        "-c",
                        'printf w > "$1" && cat "$1"',
                        "review-probe",
                        str(write_probe),
                    ],
                    provisional,
                ),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if writable.returncode != 0 or writable.stdout != "w":
                raise ReviewIsolationError(f"sandbox_probe_write_failed:bwrap:rc={writable.returncode}")
            snapshot_probe = snap / "should-fail"
            subprocess.run(
                wrap_argv_with_sandbox(
                    [
                        "/bin/sh",
                        "-c",
                        'printf bad > "$1"',
                        "review-probe",
                        str(snapshot_probe),
                    ],
                    provisional,
                ),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if snapshot_probe.exists():
                raise ReviewIsolationError("sandbox_probe_snapshot_writable:bwrap")
        finally:
            with contextlib.suppress(OSError):
                denied.unlink()
        return SandboxCapability(
            mechanism="linux-bwrap",
            binary=bwrap_path,
            profile_path=None,
            read_roots=read_roots,
            write_root=str(write),
            verified=True,
            metadata_roots=metadata_roots,
            probe_detail="allow_read+deny_host+allow_write+deny_snapshot",
            network_allowed=network_allowed,
        )

    raise ReviewIsolationError(f"sandbox_unavailable:unsupported_os:{system}")


def wrap_argv_with_sandbox(argv: Sequence[str], sandbox: SandboxCapability) -> list[str]:
    """Prefix argv with the verified OS sandbox launcher."""
    if not sandbox.verified:
        raise ReviewIsolationError("sandbox_not_verified")
    if not argv:
        raise ReviewIsolationError("empty_argv")
    # Ensure absolute executable for the inner command.
    inner = list(argv)
    first = Path(inner[0])
    if not first.is_absolute():
        raise ReviewIsolationError(f"argv0_not_absolute:{inner[0]!r}")

    if sandbox.mechanism == "macos-sandbox-exec":
        if sandbox.binary is None or sandbox.profile_path is None:
            raise ReviewIsolationError("sandbox_profile_missing")
        return [
            str(sandbox.binary),
            "-f",
            str(sandbox.profile_path),
            *inner,
        ]
    if sandbox.mechanism == "linux-bwrap":
        if sandbox.binary is None:
            raise ReviewIsolationError("sandbox_binary_missing")
        write = sandbox.write_root
        cmd = [
            str(sandbox.binary),
            "--unshare-pid",
            "--unshare-ipc",
            "--unshare-uts",
            "--unshare-cgroup-try",
            "--new-session",
            "--die-with-parent",
            "--tmpfs",
            "/",
        ]
        if not sandbox.network_allowed:
            cmd.append("--unshare-net")
        roots = [Path(root) for root in sandbox.read_roots if root != "/dev"]
        destination_parents: set[Path] = {Path("/tmp"), Path("/proc")}
        for root in [*roots, Path(write)]:
            current = root.parent
            while current != Path("/"):
                destination_parents.add(current)
                current = current.parent
        for directory in sorted(destination_parents, key=lambda value: (len(value.parts), str(value))):
            cmd.extend(["--dir", str(directory)])
        for root in roots:
            if str(root) == write:
                continue
            cmd.extend(["--ro-bind", str(root), str(root)])
        cmd.extend(
            [
                "--bind",
                write,
                write,
                "--dev",
                "/dev",
            ]
        )
        cmd.extend(inner)
        return cmd
    raise ReviewIsolationError(f"sandbox_mechanism_unknown:{sandbox.mechanism}")


def ensure_absolute_argv0(
    argv: Sequence[str],
    *,
    reject_root: Path,
    reject_roots: Iterable[Path | str] = (),
) -> list[str]:
    """Resolve argv[0] to an absolute trusted executable."""
    if not argv:
        raise ReviewIsolationError("empty_argv")
    first = Path(argv[0])
    resolved = (
        first.resolve()
        if first.is_absolute()
        else resolve_external_executable(argv[0], reject_root=reject_root, reject_roots=reject_roots)
    )
    if _inside_any(resolved, _normalized_reject_roots(reject_root, reject_roots)):
        raise ReviewIsolationError(f"executable_inside_review_root:{resolved}")
    return [str(resolved), *list(argv[1:])]


_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_FULL_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ISOLATION_EVIDENCE_SCHEMA = "review-isolation-evidence.v1"


def capability_proof_payload(capabilities: EngineCapabilities) -> dict[str, Any]:
    """Canonical non-secret capability proof object (digest input)."""
    return {
        "engine": capabilities.engine,
        "binary": str(capabilities.binary),
        "binary_sha256": _file_sha256(capabilities.binary),
        "capabilities": sorted(capabilities.capabilities),
        "missing": sorted(capabilities.missing),
        "version_sha256": hashlib.sha256(capabilities.version_text.encode("utf-8", errors="replace")).hexdigest(),
    }


def build_isolation_evidence(
    *,
    engine: str,
    capabilities: EngineCapabilities,
    sandbox: SandboxCapability,
    snapshot_fingerprint: str,
    source_state_id: str,
    patch_digest: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: Sequence[str],
    invocation_argv_digest: str,
    prompt_sha256: str,
    prompt_transport: str,
    bundle_identity: str = "",
) -> dict[str, Any]:
    """Non-secret evidence metadata bound into receipts / snapshots."""
    proof = capability_proof_payload(capabilities)
    proof_digest = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    # public_digest() must remain the sole capability identity for binding.
    if proof_digest != capabilities.public_digest():
        raise ReviewIsolationError("capability_proof_digest_mismatch")
    return {
        "schema_version": ISOLATION_EVIDENCE_SCHEMA,
        "isolation_policy_version": ISOLATION_POLICY_VERSION,
        "engine": normalize_engine_name(engine),
        "engine_capability_digest": capabilities.public_digest(),
        "engine_capabilities": sorted(capabilities.capabilities),
        "capability_proof": proof,
        "sandbox": sandbox.public_dict(),
        "snapshot_fingerprint": snapshot_fingerprint,
        "source_state_id": source_state_id,
        "patch_digest": patch_digest,
        "bundle_identity": bundle_identity,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "changed_path_count": len(tuple(changed_paths)),
        "changed_paths_digest": hashlib.sha256("\0".join(changed_paths).encode("utf-8")).hexdigest(),
        "invocation_argv_digest": invocation_argv_digest,
        "prompt_sha256": prompt_sha256,
        "prompt_transport": prompt_transport,
    }


def validate_isolation_evidence(
    evidence: Mapping[str, Any],
    *,
    expected_engine: str | None,
    expected_policy_version: str,
    snapshot_fingerprint: str,
    source_state_id: str,
    patch_digest: str,
    bundle_identity: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: Sequence[str],
    expected_capability_digest: str | None = None,
    expected_prompt_sha256: str | None = None,
    expected_prompt_transport: str | None = None,
) -> None:
    """Fail closed on missing, empty, fake-format, stale, or mismatched evidence.

    Capability proof is recomputed from the embedded proof payload and checked
    against ``required_capabilities_for(engine)``. Callers must not supply a
    tautological expected digest copied from the same evidence object; when
    ``expected_capability_digest`` is provided it must come from trusted
    in-memory runner state independent of the evidence mapping being validated.
    """
    if not isinstance(evidence, Mapping):
        raise ReviewIsolationError("isolation_evidence_malformed")
    if evidence.get("schema_version") != ISOLATION_EVIDENCE_SCHEMA:
        raise ReviewIsolationError("isolation_evidence_schema")
    if evidence.get("isolation_policy_version") != expected_policy_version:
        raise ReviewIsolationError("policy_mismatch")

    eng = evidence.get("engine")
    if not isinstance(eng, str) or not eng.strip():
        raise ReviewIsolationError("engine_missing")
    eng_norm = normalize_engine_name(eng)
    if expected_engine is not None:
        exp = normalize_engine_name(expected_engine)
        if eng_norm != exp:
            raise ReviewIsolationError("engine_mismatch")

    # Capability set + proof (never accept a bare digest without a set/proof).
    caps_raw = evidence.get("engine_capabilities")
    if not isinstance(caps_raw, list) or not caps_raw:
        raise ReviewIsolationError("capability_set_missing")
    if not all(isinstance(c, str) and c for c in caps_raw):
        raise ReviewIsolationError("capability_set_malformed")
    caps_set = frozenset(caps_raw)
    required = required_capabilities_for(eng_norm)
    missing = required - caps_set
    if missing:
        raise ReviewIsolationError("capability_missing:" + ",".join(sorted(missing)))

    proof = evidence.get("capability_proof")
    if not isinstance(proof, Mapping):
        raise ReviewIsolationError("capability_proof_missing")
    for key in (
        "engine",
        "binary",
        "binary_sha256",
        "capabilities",
        "missing",
        "version_sha256",
    ):
        if key not in proof:
            raise ReviewIsolationError(f"capability_proof_field_missing:{key}")
    if normalize_engine_name(str(proof.get("engine") or "")) != eng_norm:
        raise ReviewIsolationError("capability_proof_engine_mismatch")
    if not isinstance(proof.get("binary"), str) or not str(proof.get("binary")).strip():
        raise ReviewIsolationError("capability_proof_binary_missing")
    binary_sha = proof.get("binary_sha256")
    if not isinstance(binary_sha, str) or not _SHA256_HEX_RE.fullmatch(binary_sha):
        raise ReviewIsolationError("capability_proof_binary_digest")
    proof_binary = Path(str(proof["binary"]))
    if not proof_binary.is_file() or proof_binary.is_symlink() or _file_sha256(proof_binary) != binary_sha:
        raise ReviewIsolationError("capability_proof_binary_drift")
    if not isinstance(proof.get("capabilities"), list):
        raise ReviewIsolationError("capability_proof_capabilities_malformed")
    if frozenset(proof.get("capabilities") or ()) != caps_set:
        raise ReviewIsolationError("capability_proof_set_mismatch")
    missing_list = list(proof.get("missing") or [])
    if missing_list:
        # Accept empty missing only; non-empty missing means unproven.
        raise ReviewIsolationError("capability_proof_reports_missing")
    ver = proof.get("version_sha256")
    if not isinstance(ver, str) or not _SHA256_HEX_RE.fullmatch(ver):
        raise ReviewIsolationError("capability_proof_version_digest")

    recomputed = hashlib.sha256(
        json.dumps(
            {
                "engine": proof["engine"],
                "binary": proof["binary"],
                "binary_sha256": binary_sha,
                "capabilities": sorted(proof["capabilities"]),
                "missing": sorted(proof.get("missing") or []),
                "version_sha256": ver,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    digest = evidence.get("engine_capability_digest")
    if not isinstance(digest, str) or not _SHA256_HEX_RE.fullmatch(digest):
        raise ReviewIsolationError("capability_digest_missing")
    if digest != recomputed:
        raise ReviewIsolationError("capability_digest_mismatch")
    # Independent expected digest only when provided by trusted runner memory.
    if expected_capability_digest is not None:
        if not isinstance(expected_capability_digest, str) or not _SHA256_HEX_RE.fullmatch(expected_capability_digest):
            raise ReviewIsolationError("expected_capability_digest_invalid")
        if digest != expected_capability_digest:
            raise ReviewIsolationError("capability_mismatch")

    sandbox = evidence.get("sandbox")
    if not isinstance(sandbox, Mapping):
        raise ReviewIsolationError("sandbox_evidence")
    if sandbox.get("verified") is not True:
        raise ReviewIsolationError("sandbox_evidence")
    if sandbox.get("network_allowed") is not True:
        raise ReviewIsolationError("sandbox_network_evidence")
    mechanism = sandbox.get("mechanism")
    if not isinstance(mechanism, str) or not mechanism.strip():
        raise ReviewIsolationError("sandbox_mechanism_missing")
    root_count = sandbox.get("read_root_count")
    metadata_count = sandbox.get("metadata_root_count")
    root_digest = sandbox.get("read_roots_digest")
    if not isinstance(root_count, int) or isinstance(root_count, bool) or root_count <= 0:
        raise ReviewIsolationError("sandbox_read_root_count")
    if not isinstance(metadata_count, int) or isinstance(metadata_count, bool) or metadata_count <= 0:
        raise ReviewIsolationError("sandbox_metadata_root_count")
    if not isinstance(root_digest, str) or not _SHA256_HEX_RE.fullmatch(root_digest):
        raise ReviewIsolationError("sandbox_read_roots_digest")
    read_roots = sandbox.get("read_roots")
    metadata_roots = sandbox.get("metadata_roots")
    if not isinstance(read_roots, list) or not all(
        isinstance(root, str) and root.startswith("/") for root in read_roots
    ):
        raise ReviewIsolationError("sandbox_read_roots")
    if not isinstance(metadata_roots, list) or not all(
        isinstance(root, str) and root.startswith("/") for root in metadata_roots
    ):
        raise ReviewIsolationError("sandbox_metadata_roots")
    if len(read_roots) != root_count or len(metadata_roots) != metadata_count:
        raise ReviewIsolationError("sandbox_root_count_mismatch")
    recomputed_roots = hashlib.sha256(
        json.dumps(
            {"read_roots": read_roots, "metadata_roots": metadata_roots},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if root_digest != recomputed_roots:
        raise ReviewIsolationError("sandbox_read_roots_digest_mismatch")
    # Probe identity: require non-empty detail or binary path for mechanism.
    probe = sandbox.get("probe_detail")
    binary = sandbox.get("binary")
    if not ((isinstance(probe, str) and probe.strip()) or (isinstance(binary, str) and binary.strip())):
        raise ReviewIsolationError("sandbox_probe_identity_missing")

    for field_name, expected in (
        ("snapshot_fingerprint", snapshot_fingerprint),
        ("source_state_id", source_state_id),
        ("patch_digest", patch_digest),
        ("bundle_identity", bundle_identity),
    ):
        value = evidence.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ReviewIsolationError(f"evidence_{field_name}_missing")
        # Fingerprints, digests, bundle id, and source_state_id are sha256 hex.
        if not _SHA256_HEX_RE.fullmatch(value):
            raise ReviewIsolationError(f"evidence_{field_name}_format")
        if value != expected:
            raise ReviewIsolationError(f"evidence_{field_name}")

    # Base identity: explicit null only when snapshot base is null.
    ev_base = evidence.get("base_sha")
    if base_sha is None:
        if ev_base not in {None}:
            # Empty string is not an acceptable stand-in for null base.
            raise ReviewIsolationError("evidence_base_sha")
    else:
        if not isinstance(ev_base, str) or not _FULL_GIT_SHA_RE.fullmatch(ev_base):
            raise ReviewIsolationError("evidence_base_sha")
        if ev_base != base_sha:
            raise ReviewIsolationError("evidence_base_sha")

    ev_head = evidence.get("head_sha")
    if not isinstance(ev_head, str) or not _FULL_GIT_SHA_RE.fullmatch(ev_head):
        raise ReviewIsolationError("evidence_head_sha")
    if not head_sha or ev_head != head_sha:
        raise ReviewIsolationError("evidence_head_sha")

    expected_cp = hashlib.sha256("\0".join(changed_paths).encode("utf-8")).hexdigest()
    cp_digest = evidence.get("changed_paths_digest")
    if not isinstance(cp_digest, str) or not _SHA256_HEX_RE.fullmatch(cp_digest):
        raise ReviewIsolationError("changed_paths_digest")
    if cp_digest != expected_cp:
        raise ReviewIsolationError("changed_paths_digest")
    count = evidence.get("changed_path_count")
    if not isinstance(count, int) or isinstance(count, bool) or count != len(tuple(changed_paths)):
        raise ReviewIsolationError("changed_path_count")

    inv = evidence.get("invocation_argv_digest")
    if not isinstance(inv, str) or not _SHA256_HEX_RE.fullmatch(inv):
        raise ReviewIsolationError("invocation_identity_missing")
    prompt_digest = evidence.get("prompt_sha256")
    if not isinstance(prompt_digest, str) or not _SHA256_HEX_RE.fullmatch(prompt_digest):
        raise ReviewIsolationError("prompt_digest_missing")
    if expected_prompt_sha256 is None or prompt_digest != expected_prompt_sha256:
        raise ReviewIsolationError("prompt_digest_mismatch")
    transport = evidence.get("prompt_transport")
    if transport not in {"stdin", "prompt-file"}:
        raise ReviewIsolationError("prompt_transport_invalid")
    if expected_prompt_transport is None or transport != expected_prompt_transport:
        raise ReviewIsolationError("prompt_transport_mismatch")


def prepare_isolated_review_launch(
    *,
    engine: str,
    argv: Sequence[str],
    snapshot_root: Path,
    reject_root: Path,
    reject_roots: Sequence[Path | str] = (),
    expected_binary: Path | None = None,
    write_root: Path | None = None,
    exec_root: Path | None = None,
    cwd: Path | None = None,
    source_env: Mapping[str, str] | None = None,
    capabilities: EngineCapabilities | None = None,
    help_text: str | None = None,
    snapshot_fingerprint: str = "",
    source_state_id: str = "",
    patch_digest: str = "",
    bundle_identity: str = "",
    base_sha: str | None = None,
    head_sha: str = "",
    changed_paths: Sequence[str] = (),
    prompt_payload: str = "",
    prompt_transport: str = "",
) -> IsolatedReviewLaunch:
    """Single fail-closed policy: env + capability + OS sandbox + absolute argv.

    This is the enforced entry for exact-target reviewer launches. Callers
    must not spawn a reviewer subprocess without going through this (or
    :func:`apply_review_isolation_to_invocation` which delegates here).
    """
    engine_key = normalize_engine_name(engine)
    if engine_key == "kimi":
        raise ReviewIsolationError(
            "kimi_isolated_review_unsupported: sealed formal CF isolation is not proven "
            "for native Kimi Code (project instructions / MCP / hooks / nested reviewers). "
            "Use review-pr --reviewer claude|glm|codex. See #5556 / docs/runbooks/kimi-formal-cf-isolation.md."
        )
    if engine_key == "agy":
        raise ReviewIsolationError(
            "agy_isolated_review_unsupported: native project-instruction, MCP, "
            "hook, and nested-reviewer suppression is not proven"
        )
    if engine_key == "grok":
        raise ReviewIsolationError(
            "grok_isolated_review_unsupported: native OAuth credentials cannot "
            "be hidden from the required Read/Grep/Glob tools"
        )
    snap = snapshot_root.resolve()
    reject = reject_root.resolve()
    if not snap.is_dir():
        raise ReviewIsolationError(f"snapshot_missing:{snap}")

    if write_root is None or exec_root is None:
        raise ReviewIsolationError("review_roots_must_be_parent_owned")

    all_rejects = _normalized_reject_roots(reject, reject_roots)
    snap, write = validate_private_review_roots(
        snapshot_root=snap,
        write_root=write_root,
        reject_root=reject,
        reject_roots=all_rejects,
    )
    execution_root = _validate_private_exec_root(
        exec_root=exec_root,
        snapshot_root=snap,
        write_root=write,
        reject_roots=all_rejects,
    )
    if help_text is not None or capabilities is not None:
        raise ReviewIsolationError("caller_capability_override_forbidden")
    abs_argv = ensure_absolute_argv0(argv, reject_root=reject, reject_roots=all_rejects)
    binary = Path(abs_argv[0])
    if expected_binary is not None:
        expected = expected_binary.resolve(strict=True)
        if binary != expected:
            raise ReviewIsolationError(f"reviewer_binary_mismatch:expected={expected}:actual={binary}")
    binary = _stage_pinned_reviewer_runtime(binary, exec_root=execution_root)
    abs_argv[0] = str(binary)
    sealed_reader_helper: Path | None = None
    sealed_reader_python: Path | None = None
    sealed_reader_runtime: list[str] = []
    if engine_key == "codex":
        sealed_reader_helper = _stage_sealed_read_mcp(execution_root)
        requested_python = _resolve_fixed_system_executable(
            "python3",
            reject_roots=all_rejects,
        )
        sealed_reader_python, sealed_reader_runtime = _sealed_reader_python_runtime(
            requested_python,
            reject_roots=all_rejects,
        )
        abs_argv = _inject_codex_sealed_read_mcp(
            abs_argv,
            python_bin=sealed_reader_python,
            helper=sealed_reader_helper,
            snapshot_root=snap,
        )
    if not prompt_payload:
        raise ReviewIsolationError("review_prompt_missing")
    if prompt_transport not in {"stdin", "prompt-file"}:
        raise ReviewIsolationError("review_prompt_transport_invalid")
    prompt_bytes = prompt_payload.encode("utf-8")
    prompt_digest = hashlib.sha256(prompt_bytes).hexdigest()
    if prompt_transport == "prompt-file":
        try:
            marker = abs_argv.index("--prompt-file")
            prompt_path = Path(abs_argv[marker + 1])
        except (ValueError, IndexError) as exc:
            raise ReviewIsolationError("review_prompt_file_argument_missing") from exc
        try:
            prompt_stat = prompt_path.lstat()
        except OSError as exc:
            raise ReviewIsolationError("review_prompt_file_missing") from exc
        if stat.S_ISLNK(prompt_stat.st_mode) or not stat.S_ISREG(prompt_stat.st_mode):
            raise ReviewIsolationError("review_prompt_file_not_regular")
        if not is_within(prompt_path, write / "tmp"):
            raise ReviewIsolationError("review_prompt_file_outside_write_root")
        captured_prompt = prompt_path.read_bytes()
        if captured_prompt != prompt_bytes:
            raise ReviewIsolationError("review_prompt_file_drift")
        pinned_prompt = execution_root / "review-prompt.txt"
        prompt_fd = os.open(
            pinned_prompt,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o400,
        )
        try:
            _write_fd_all(prompt_fd, captured_prompt)
        finally:
            os.close(prompt_fd)
        abs_argv[marker + 1] = str(pinned_prompt)
        prompt_path.unlink()
    _freeze_exec_root(execution_root, staged_binary=binary)
    runtime_reads = resolve_runtime_closure(binary, reject_roots=all_rejects)
    # The entire exec root is parent-created, private, and frozen above.  It
    # contains the staged reviewer, prompt, and sealed MCP helper, all of which
    # must remain readable after the live checkout and host temp roots are
    # denied by the OS sandbox.
    execution_value = str(execution_root)
    if execution_value not in runtime_reads:
        runtime_reads.append(execution_value)
    for runtime_path in sealed_reader_runtime:
        if runtime_path not in runtime_reads:
            runtime_reads.append(runtime_path)

    write_home = write / "home"
    write_tmp = write / "tmp"
    if not write_home.is_dir() or not write_tmp.is_dir():
        raise ReviewIsolationError("review_parent_owned_subdirs_missing")

    # Capability probes run without provider credentials and without network.
    # Only a binary that passes this gate receives authentication afterward.
    probe_sandbox = prepare_host_sandbox(
        engine=engine_key,
        snapshot_root=snap,
        write_root=write,
        reject_root=reject,
        reject_roots=all_rejects,
        profile_dir=write,
        runtime_reads=runtime_reads,
        executable=binary,
        network_allowed=False,
    )
    if sealed_reader_python is not None and sealed_reader_helper is not None:
        _probe_sealed_read_mcp(
            python_bin=sealed_reader_python,
            helper=sealed_reader_helper,
            snapshot_root=snap,
            sandbox=probe_sandbox,
        )
    probe_env = build_reviewer_env(
        engine=engine_key,
        reject_root=reject,
        source=source_env,
        home=str(write_home),
        tmpdir=str(write_tmp),
        forward_auth=False,
    )
    runtime_path_dirs: list[str] = []
    for raw in [str(binary), *runtime_reads, "/usr/bin", "/bin"]:
        path = Path(raw)
        directory = path.parent if path.is_file() else path
        value = str(directory.resolve())
        if value not in runtime_path_dirs:
            runtime_path_dirs.append(value)
    probe_env["PATH"] = os.pathsep.join(runtime_path_dirs)
    help_text = probe_engine_help(
        binary,
        sandbox=probe_sandbox,
        env=probe_env,
        cwd=snap,
    )
    effective_help = help_text or ""
    require_supported_engine_version(engine_key, effective_help)

    argv_joined = " ".join(abs_argv).lower()
    policy_enforced: dict[str, bool] = {
        "os_sandbox_required": bool(probe_sandbox.verified),
        "no_nested_reviewers": (
            "multi_agent" in argv_joined
            or "--disable" in argv_joined
            or "--tools" in argv_joined
            or "--bare" in argv_joined
            or "--disallowed-tools" in argv_joined
        ),
        "disable_project_instructions": True,
        "read_only_or_no_write_tools": bool(probe_sandbox.verified),
    }
    capabilities = detect_engine_capabilities(
        engine_key,
        binary,
        help_text=effective_help,
        version_text=effective_help[:4000],
        policy_enforced=policy_enforced,
    )
    require_engine_isolation(capabilities)

    auth_env = stage_engine_auth(
        engine_key,
        write_home=write_home,
        source_env=source_env,
    )
    sandbox = prepare_host_sandbox(
        engine=engine_key,
        snapshot_root=snap,
        write_root=write,
        reject_root=reject,
        reject_roots=all_rejects,
        profile_dir=write,
        runtime_reads=runtime_reads,
        executable=binary,
        network_allowed=True,
    )
    env = build_reviewer_env(
        engine=engine_key,
        reject_root=reject,
        source=source_env,
        home=str(write_home),
        tmpdir=str(write_tmp),
        forward_auth=True,
    )
    env["HOME"] = str(write_home)
    env["TMPDIR"] = str(write_tmp)
    env["TMP"] = str(write_tmp)
    env["TEMP"] = str(write_tmp)
    if engine_key == "claude":
        # Native Claude/Bun consult these before the generic TMPDIR fallback.
        # Keep its per-UID scratch directory inside the disposable write root.
        env["CLAUDE_CODE_TMPDIR"] = str(write_tmp)
        env["CLAUDE_TMPDIR"] = str(write_tmp)
        env["BUN_TMPDIR"] = str(write_tmp)
    env["PATH"] = os.pathsep.join(runtime_path_dirs)
    # Selected auth/runtime staging env. Values never enter evidence/logs.
    for key, value in auth_env.items():
        env[key] = value

    wrapped = wrap_argv_with_sandbox(abs_argv, sandbox)
    argv_digest = hashlib.sha256(json.dumps(wrapped, separators=(",", ":")).encode("utf-8")).hexdigest()
    evidence = build_isolation_evidence(
        engine=engine_key,
        capabilities=capabilities,
        sandbox=sandbox,
        snapshot_fingerprint=snapshot_fingerprint,
        source_state_id=source_state_id,
        patch_digest=patch_digest,
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        invocation_argv_digest=argv_digest,
        prompt_sha256=prompt_digest,
        prompt_transport=prompt_transport,
        bundle_identity=bundle_identity,
    )
    work_cwd = (cwd or snap).resolve()
    if not (is_within(work_cwd, snap) or is_within(work_cwd, write)):
        raise ReviewIsolationError(f"review_cwd_outside_isolation_roots:{work_cwd}")
    return IsolatedReviewLaunch(
        argv=wrapped,
        env=env,
        cwd=work_cwd,
        write_root=write,
        snapshot_root=snap,
        engine=engine_key,
        policy_version=ISOLATION_POLICY_VERSION,
        capabilities=capabilities,
        sandbox=sandbox,
        evidence=evidence,
    )


def apply_review_isolation_to_invocation(
    *,
    engine: str,
    cmd: Sequence[str],
    cwd: Path,
    tool_config: Mapping[str, Any],
    env_overrides: Mapping[str, str] | None = None,
    reject_root: Path | None = None,
    prompt_payload: str = "",
    prompt_transport: str = "",
) -> tuple[list[str], dict[str, str], Path, dict[str, Any], str, str, str]:
    """Runner seam: enforce isolation when tool_config requests review isolation.

    Returns ``(argv, env, cwd, evidence)``. Secret values never enter evidence.
    """
    if not tool_config.get("review_isolation"):
        raise ReviewIsolationError("apply_review_isolation_requires_review_isolation_flag")

    snapshot_root = tool_config.get("review_snapshot_root") or tool_config.get("repo_read_root")
    if not snapshot_root:
        # Fall back to cwd when the adapter already set cwd to the snapshot.
        snapshot_root = str(cwd)
    snap = Path(str(snapshot_root)).resolve()
    reject = (reject_root or Path(str(tool_config.get("review_reject_root") or snap))).resolve()
    raw_rejects = tool_config.get("review_reject_roots") or ()
    if not isinstance(raw_rejects, (list, tuple)) or not all(isinstance(item, str) and item for item in raw_rejects):
        raise ReviewIsolationError("review_reject_roots_malformed")
    reject_roots = tuple(Path(item).resolve() for item in raw_rejects)
    binary_raw = tool_config.get("review_engine_binary")
    if not isinstance(binary_raw, str) or not binary_raw:
        raise ReviewIsolationError("trusted_reviewer_binary_missing")
    expected_binary = Path(binary_raw).resolve(strict=True)
    write_raw = tool_config.get("review_write_root")
    write = Path(str(write_raw)).resolve() if write_raw else None
    exec_raw = tool_config.get("review_exec_root")
    execution_root = Path(str(exec_raw)).resolve() if exec_raw else None

    # Merge env overrides into a temporary source map for selected keys only.
    source = dict(os.environ)
    if env_overrides:
        for key, value in dict(env_overrides).items():
            # The Codex adapter points the child at the disposable review home
            # before this seam runs. That destination must not replace the
            # caller's original CODEX_HOME as the auth source to stage.
            if normalize_engine_name(engine) == "codex" and key == "CODEX_HOME":
                continue
            source[key] = value

    launch = prepare_isolated_review_launch(
        engine=str(tool_config.get("review_engine") or engine),
        argv=cmd,
        snapshot_root=snap,
        reject_root=reject,
        reject_roots=reject_roots,
        expected_binary=expected_binary,
        write_root=write,
        exec_root=execution_root,
        cwd=cwd,
        source_env=source,
        snapshot_fingerprint=str(tool_config.get("review_snapshot_fingerprint") or ""),
        source_state_id=str(tool_config.get("review_source_state_id") or ""),
        patch_digest=str(tool_config.get("review_patch_digest") or ""),
        bundle_identity=str(tool_config.get("review_bundle_identity") or ""),
        base_sha=tool_config.get("review_base_sha")  # type: ignore[arg-type]
        if tool_config.get("review_base_sha") is None or isinstance(tool_config.get("review_base_sha"), str)
        else None,
        head_sha=str(tool_config.get("review_head_sha") or ""),
        changed_paths=tuple(tool_config.get("review_changed_paths") or ()),
        prompt_payload=prompt_payload,
        prompt_transport=prompt_transport,
    )
    capability_digest = launch.capabilities.public_digest()
    prompt_digest = hashlib.sha256(prompt_payload.encode("utf-8")).hexdigest()
    return (
        launch.argv,
        launch.env,
        launch.cwd,
        launch.evidence,
        capability_digest,
        prompt_digest,
        prompt_transport,
    )


def redact_secrets_from_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with credential-like values redacted (for logs/receipts)."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        key_l = str(key).lower()
        if any(tok in key_l for tok in ("key", "token", "secret", "password", "passwd", "credential")):
            out[str(key)] = "[redacted]"
            continue
        if isinstance(value, str) and secret_like_findings(value):
            out[str(key)] = "[redacted]"
            continue
        if isinstance(value, Mapping):
            out[str(key)] = redact_secrets_from_mapping(value)
        else:
            out[str(key)] = value
    return out
