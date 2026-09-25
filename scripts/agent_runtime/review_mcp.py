"""Per-attempt stdio sources MCP launcher and receipt ledger provisioner.

Issue: #8517 (Refs #8430, #8397)

Provisions a per-attempt MCP configuration and empty receipt ledger for review
seats. Formal reviews require audit-grade receipts recorded over stdio via
attempt-specific environment variables:
- LU_REVIEW_ATTEMPT_ID
- LU_REVIEW_MANIFEST_SHA256
- LU_REVIEW_LEDGER_PATH

The generated MCP configuration defines exclusively a `sources` server started
over stdio from the primary checkout's virtual environment and server script,
bypassing the shared streamable-HTTP daemon (127.0.0.1:8766).

Codex has no ``--mcp-config`` flag, and per-invocation ``-c mcp_servers.X`` overrides
MERGE with the user's global ``~/.codex/config.toml``. A Codex attempt therefore also
gets a scoped ``CODEX_HOME`` directory (``<attempt_id>.codex-home/``, always the sibling
of the attempt's ``.mcp.json``) holding a ``config.toml`` that registers only the stdio
``sources`` server, plus an ``auth.json`` symlink. Because trusted *project* config can
still add servers, the worker runs ``verify_codex_review_effective_mcp`` before launch
and refuses the attempt unless the effective server set is exactly that one server.

AGY has no per-invocation MCP flag either, and reads its MCP servers from
``$HOME/.gemini/config/mcp_config.json`` (proven by the #8617 spike: ``agy -p`` does
not load ``antigravity-cli/mcp_config.json``). An AGY attempt therefore gets a scoped
home (``<attempt_id>.agy-home/``, sibling of the attempt's ``.mcp.json``) whose
``.gemini/config/mcp_config.json`` holds only the stdio ``sources`` server, plus a
symlink to the OAuth token (the only credential ``agy -p`` needs). The launch runs with
``HOME`` and ``AGY_APP_DATA_DIR`` pointing into it, and ``verify_agy_review_launch``
refuses the attempt unless ``agy mcp list`` under that same environment shows exactly
that one server.

Note: Ledger creation and sidecar management will be consolidated once R1
(cursor/impl-review-r1-schema-ledger) merges to main.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common.repo_root import resolve_repo_root
from scripts.review.receipts.ledger import REVIEW_TOOLS

ENV_ATTEMPT_ID = "LU_REVIEW_ATTEMPT_ID"
ENV_MANIFEST_SHA256 = "LU_REVIEW_MANIFEST_SHA256"
ENV_LEDGER_PATH = "LU_REVIEW_LEDGER_PATH"
ENV_KEYS = (ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH)

SUPPORTED_HARNESSES: frozenset[str] = frozenset({"agy", "claude", "codex", "cursor"})

UNSUPPORTED_HARNESS_REASONS: dict[str, str] = {
    "gemini": "Gemini has one global MCP config without per-invocation MCP config support",
    "grok": "not yet proven",
    "grok-build": "not yet proven",
    "kimicc": "not yet supported",
    "kimi": "Native Kimi Code reads global profile config and cannot take a per-attempt stdio config",
    "grok-hermes": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
    "deepseek": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
    "qwen": "Hermes-routed agents read global ~/.hermes/config.yaml and cannot take a per-attempt stdio config",
}

_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
_MCP_CONFIG_SUFFIX = ".mcp.json"
_CODEX_HOME_SUFFIX = ".codex-home"
_CODEX_MCP_LIST_TIMEOUT_S = 60.0
_AGY_HOME_SUFFIX = ".agy-home"
_AGY_MCP_LIST_TIMEOUT_S = 60.0
_AGY_TOKEN_NAME = "antigravity-oauth-token"
_LINK_ELSEWHERE = "points elsewhere"
_AGY_MCP_LIST_COLUMNS = ("NAME", "TYPE", "STATUS", "COMMAND/URL")

_LISTED_NAMES = 5
_DIAGNOSTICS_SUFFIX = ".diagnostics.log"
_FINGERPRINT_LEN = 12
# The only shape an untrusted identifier may echo in a refusal. No ``/``, ``\``, ``%`` or ``~``
# by construction, so a path in any encoding (relative, URL-encoded, ``file://``, unicode slash) fails.
_ECHO_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9_.:-]{1,64}")
_MIN_MASKED_VALUE_LEN = 3
_PATH_MASK = "<path>"
# Anything path-shaped, run to the next delimiter so a path with spaces is masked whole:
# ``C:\x`` / ``C:/x``, UNC ``\\host``, ``~/x`` / ``~user/x``, ``./x`` / ``../x`` and ``/x``.
_PATH_SHAPED_RE = re.compile(
    r"""(?:
        (?<![\w])[A-Za-z]:[\\/]
      | \\\\(?=[^\s\\])
      | (?<![\w.~])~[\w.-]*[\\/]
      | (?<![\w.])\.{1,2}[\\/]
      | (?<![\w.~])/(?=\S)
    )[^'"`,;<>|)\]}\r\n]*""",
    re.VERBOSE,
)


def _known_values(extra: Mapping[str, str | None] | None = None) -> dict[str, str | None]:
    """The values a refusal must never carry: the operator home and the scoped-launch env values."""
    values: dict[str, str | None] = {
        "~": os.path.expanduser("~"),
        "$HOME": os.environ.get("HOME"),
        "$CODEX_HOME": os.environ.get("CODEX_HOME"),
        "$AGY_APP_DATA_DIR": os.environ.get("AGY_APP_DATA_DIR"),
    }
    values.update(extra or {})
    return values


def _mask(text: object, values: Mapping[str, str | None] | None = None) -> str:
    """Mask the log-unsafe values and path shapes in ``text`` and flatten whitespace.

    Masks each known log-unsafe value with its label (longest first, so a nested path collapses to
    its innermost label; empty, root and tiny values are skipped, since masking ``/`` or ``1`` would
    mangle everything), then masks anything path-shaped. This is a blocklist, so it is only a
    whole-message safety net over refusals that already carry no untrusted free text: those never
    interpolate stderr, stdout, exception strings, ``strerror``, config or table text (see
    ``_untrusted``) and show an untrusted identifier only through ``_echo_identifier``.
    """
    cleaned = str(text)
    for label, value in sorted(_known_values(values).items(), key=lambda item: len(item[1] or ""), reverse=True):
        if value and len(value.strip("/")) >= _MIN_MASKED_VALUE_LEN:
            cleaned = cleaned.replace(value, label)
    cleaned = _PATH_SHAPED_RE.sub(_PATH_MASK, cleaned)
    return " ".join("".join(ch if ch.isprintable() else " " for ch in cleaned).split())


def _echo_identifier(value: object) -> str:
    """An untrusted identifier (server/tool name, table cell, id, harness) as a refusal may show it.

    An allowlist: the value is echoed only when it fully matches ``_ECHO_IDENTIFIER_RE``. Anything
    else (a path in any encoding, a URL, a secret, free text, a non-string) is shown as its size
    only, so no encoding of a path can slip past a blocklist.
    """
    if not isinstance(value, str):
        return f"<redacted: a {type(value).__name__}>"
    if _ECHO_IDENTIFIER_RE.fullmatch(value):
        return value
    return f"<redacted: {len(value)} chars>"


def review_diagnostics_path(config_path: Path | str) -> Path:
    """Return the local diagnostics file that pairs with an attempt's ``.mcp.json``.

    It sits beside the attempt's ledger under the ignored ``batch_state/`` runtime tree (never
    committed) and holds the full untrusted text a refusal deliberately does not echo.
    """
    config = Path(config_path)
    if not config.name.endswith(_MCP_CONFIG_SUFFIX):
        raise ValueError(f"review MCP config path must end in {_MCP_CONFIG_SUFFIX}: {_echo_identifier(config.name)!r}")
    return config.with_name(config.name[: -len(_MCP_CONFIG_SUFFIX)] + _DIAGNOSTICS_SUFFIX)


class ReviewDirectoryError(ValueError):
    """A review runtime directory is a symlink, not a directory, or not owned by the current user."""


_UNSAFE_DIRECTORY = (
    "review attempt refused: a review runtime directory is a symlink, is not a directory, "
    "or is not owned by the current user (#8652)"
)
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _open_owned_dir(name: Path | str, *, dir_fd: int | None = None) -> int:
    """Open ``name`` as a directory without following a symlink; refuse unless the caller owns it.

    ``O_NOFOLLOW`` guards only the final component, so callers walk a path one component at a
    time with ``dir_fd``. The owner check runs on the opened descriptor (``fstat``), so it
    describes the very directory that is then used, whatever happens to the path afterwards.
    The refusal is fixed wording: it never names the path.
    """
    try:
        fd = os.open(name, _DIRECTORY_FLAGS, dir_fd=dir_fd)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ReviewDirectoryError(_UNSAFE_DIRECTORY) from None
        raise
    try:
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            raise ReviewDirectoryError(_UNSAFE_DIRECTORY)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _open_runtime_dir(anchor: Path, components: Sequence[str]) -> int:
    """Create-or-open ``components`` under the trusted ``anchor``, never following a symlink.

    Each component is made with ``mkdir`` (mode 0700) relative to its parent's descriptor, then
    opened ``O_DIRECTORY | O_NOFOLLOW`` and checked for ownership, so a symlink planted at any
    level (or swapped in later) is refused rather than followed. Returns the last directory's fd.
    """
    fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for name in components:
            with contextlib.suppress(FileExistsError):
                os.mkdir(name, 0o700, dir_fd=fd)
            child = _open_owned_dir(name, dir_fd=fd)
            os.close(fd)
            fd = child
    except BaseException:
        os.close(fd)
        raise
    return fd


def _lexists(name: str, dir_fd: int) -> bool:
    """Whether ``name`` exists in ``dir_fd`` (a dangling symlink counts; nothing is followed)."""
    try:
        os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _create_file(name: str, dir_fd: int, payload: bytes) -> None:
    """Create ``name`` exclusively (0600) inside ``dir_fd`` and write ``payload``."""
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
    with os.fdopen(fd, "wb") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(payload)


def _untrusted(label: str, text: object, diagnostics: Path) -> str:
    """The stand-in a refusal shows for untrusted free text: its size and fingerprint, never its content.

    Untrusted free text (tool stderr/stdout, exception strings, ``strerror``, config and table text)
    is never echoed, in whole or in part, because no filter can prove a fragment of it path-free.
    The refusal carries our fixed wording, the text's length, ``sha256(text)[:12]`` for correlation
    and the diagnostics file's basename; the full text is appended to that file (mode 0600).
    ``label`` is fixed wording from our code.
    """
    raw = text if isinstance(text, str) else str(text)
    payload = raw.encode("utf-8", errors="backslashreplace")
    fingerprint = hashlib.sha256(payload).hexdigest()[:_FINGERPRINT_LEN]
    saved = f"details in {diagnostics.name}"
    try:
        # Open the attempt directory without following a symlink and create the file relative to it,
        # so a directory swapped in after prepare_review_attempt cannot redirect the write.
        dir_fd = _open_owned_dir(diagnostics.parent)
        try:
            fd = os.open(diagnostics.name, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
            try:
                os.fchmod(fd, 0o600)
                os.write(
                    fd, f"--- {label} ({len(raw)} chars, sha256 {fingerprint}) ---\n".encode("ascii") + payload + b"\n"
                )
            finally:
                os.close(fd)
        finally:
            os.close(dir_fd)
    except (OSError, ReviewDirectoryError) as exc:
        reason = _errno_name(exc) if isinstance(exc, OSError) else None
        saved = f"details not saved: {reason or 'unsafe directory'}"
    return f"<{label}: {len(raw)} chars, sha256 {fingerprint}; {saved}>"


def _errno_name(exc: OSError) -> str | None:
    """The symbolic errno (``ENOENT``) of an ``OSError``, or ``None`` when it carries none."""
    code = exc.errno
    return errno.errorcode.get(code) if isinstance(code, int) else None


def _describe_identifier(value: object) -> str:
    """Describe an invalid identifier: verbatim only if it is allowlist-clean, else its size only."""
    return _echo_identifier(value)


def _describe_names(names: Sequence[object]) -> str:
    """List server names for a refusal: a bounded count of allowlisted-or-redacted names."""
    shown = [_echo_identifier(name) for name in names[:_LISTED_NAMES]]
    if len(names) > _LISTED_NAMES:
        shown.append(f"... {len(names) - _LISTED_NAMES} more")
    return repr(shown)


class CodexReviewMcpGateError(ValueError):
    """The effective Codex MCP server set for a review attempt is not exactly ``sources``."""


class AgyReviewMcpGateError(ValueError):
    """The effective AGY MCP server set for a review attempt is not exactly ``sources``."""


@dataclass(frozen=True)
class ReviewMcpPlan:
    """Plan and options for running a review attempt with isolated stdio sources MCP."""

    config_path: Path
    adapter_options: dict[str, Any]
    ledger_path: Path
    sidecar_path: Path
    manifest_sha256: str
    review_id: str
    attempt_id: str
    harness: str
    codex_home: Path | None = None
    agy_home: Path | None = None

    @property
    def mcp_config_path(self) -> Path:
        return self.config_path

    @property
    def strict_mcp_config(self) -> bool:
        return True


def review_tools_allowed_csv(harness: str) -> str | None:
    """Return the Claude Code ``--allowedTools`` names for the sources server.

    Only Claude Code understands these names. Kimi reviews use that same
    grant on the kimicc read-only dispatch path, which calls this with
    ``claude`` because the headless binary is Claude Code.
    """
    if harness.lower().strip() != "claude":
        return None
    return ",".join(f"mcp__sources__{name}" for name in sorted(REVIEW_TOOLS))


def codex_review_home_path(config_path: Path | str) -> Path:
    """Return the scoped ``CODEX_HOME`` directory that pairs with an attempt's ``.mcp.json``."""
    config = Path(config_path)
    if not config.name.endswith(_MCP_CONFIG_SUFFIX):
        raise ValueError(f"review MCP config path must end in {_MCP_CONFIG_SUFFIX}: {_echo_identifier(config.name)!r}")
    return config.with_name(config.name[: -len(_MCP_CONFIG_SUFFIX)] + _CODEX_HOME_SUFFIX)


def agy_review_home_path(config_path: Path | str) -> Path:
    """Return the scoped AGY ``HOME`` directory that pairs with an attempt's ``.mcp.json``."""
    config = Path(config_path)
    if not config.name.endswith(_MCP_CONFIG_SUFFIX):
        raise ValueError(f"review MCP config path must end in {_MCP_CONFIG_SUFFIX}: {_echo_identifier(config.name)!r}")
    return config.with_name(config.name[: -len(_MCP_CONFIG_SUFFIX)] + _AGY_HOME_SUFFIX)


def agy_review_app_data_dir(agy_home: Path | str) -> Path:
    """Return the ``AGY_APP_DATA_DIR`` inside a scoped AGY home."""
    return Path(agy_home) / ".gemini" / "antigravity-cli"


def agy_review_mcp_config_path(agy_home: Path | str) -> Path:
    """Return the one MCP config file ``agy -p`` loads from a home (#8617 spike)."""
    return Path(agy_home) / ".gemini" / "config" / "mcp_config.json"


def _toml_string(value: str) -> str:
    # JSON string escapes are a subset of TOML basic-string escapes.
    return json.dumps(value, ensure_ascii=True)


def _render_codex_review_config(python_bin: Path, sources_server: Path, env: dict[str, str]) -> str:
    """Render the minimal Codex config: one stdio ``sources`` server, nothing else."""
    lines = [
        "# Auto-generated by review_mcp.prepare_review_attempt (#8517).",
        "# Scoped CODEX_HOME for ONE review attempt: only the stdio sources server.",
        "",
        "[mcp_servers.sources]",
        f"command = {_toml_string(str(python_bin))}",
        f"args = [{_toml_string(str(sources_server))}]",
        "required = true",
        'default_tools_approval_mode = "approve"',
        "",
        "[mcp_servers.sources.env]",
    ]
    lines.extend(f"{key} = {_toml_string(value)}" for key, value in env.items())
    return "\n".join(lines) + "\n"


def _link_codex_auth(home_fd: int) -> None:
    """Symlink the user's Codex ``auth.json`` into the scoped home (as ``_ensure_codex_writer_home`` does)."""
    real_auth = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "auth.json"
    if real_auth.exists():
        os.symlink(real_auth, "auth.json", dir_fd=home_fd)


def _real_agy_token() -> Path:
    """The user's AGY OAuth token, honoring an ``AGY_APP_DATA_DIR`` export like ``_link_codex_auth``."""
    app_data = os.environ.get("AGY_APP_DATA_DIR") or Path.home() / ".gemini" / "antigravity-cli"
    return Path(app_data) / _AGY_TOKEN_NAME


def _populate_agy_review_home(home_fd: int, real_token: Path, config_bytes: bytes) -> None:
    """Fill a freshly created scoped AGY home (open as ``home_fd``): the sources-only MCP config and a linked token.

    Only the OAuth token is linked (never copied): the #8617 spike proved it is the
    sole credential ``agy -p`` needs. Everything else agy wants it creates itself.
    Every directory and file is made relative to descriptors, never by path.
    """
    parts = agy_review_app_data_dir(Path()).parts  # .gemini / antigravity-cli
    config_parts = agy_review_mcp_config_path(Path()).parts  # .gemini / config / mcp_config.json
    gemini_fd = config_fd = app_data_fd = None
    try:
        os.mkdir(parts[0], 0o700, dir_fd=home_fd)
        gemini_fd = _open_owned_dir(parts[0], dir_fd=home_fd)
        os.mkdir(config_parts[1], 0o700, dir_fd=gemini_fd)
        config_fd = _open_owned_dir(config_parts[1], dir_fd=gemini_fd)
        os.mkdir(parts[1], 0o700, dir_fd=gemini_fd)
        app_data_fd = _open_owned_dir(parts[1], dir_fd=gemini_fd)
        _create_file(config_parts[2], config_fd, config_bytes)
        # A symlink, not a copy, by design: a token refresh (which may rotate the refresh
        # token) must land in the real token file. A refreshed copy would leave the real
        # token stale or invalidated and break every other AGY lane. "Nothing written to the
        # real ~/.gemini" means configuration; agy_oauth_link_problem() guards the link itself.
        os.symlink(real_token, _AGY_TOKEN_NAME, dir_fd=app_data_fd)
    finally:
        for fd in (app_data_fd, config_fd, gemini_fd):
            if fd is not None:
                os.close(fd)


def agy_oauth_link_problem(config_path: Path | str) -> str | None:
    """Describe how a scoped AGY home's OAuth link deviates from the real token, or ``None`` if intact.

    Intact means ``antigravity-oauth-token`` in the scoped app-data dir is still a symlink
    whose target resolves to the original real token path. Credentials are never copied
    or repaired here; a deviation is left untouched for the operator.
    """
    agy_home = agy_review_home_path(config_path)
    link = agy_review_app_data_dir(agy_home) / _AGY_TOKEN_NAME
    real_token = _real_agy_token()
    # The message lands in task state and stderr logs that get quoted into issues and PRs, so it
    # names the scoped link relative to the attempt directory and the real token only by a label:
    # no absolute path (which would expose the operator's home directory) is ever included.
    link_label = link.relative_to(agy_home.parent)
    state = _agy_oauth_link_state(link, real_token)
    if state is None:
        return None
    if state == _LINK_ELSEWHERE:
        return f"{link_label} {state}, not to the real AGY OAuth token"
    return f"{link_label} {state}, not a symlink to the real AGY OAuth token"


def _agy_oauth_link_state(link: Path, real_token: Path) -> str | None:
    """Fixed wording for how ``link`` deviates from the real token (``None`` when intact)."""
    if not link.is_symlink():
        return "is a regular file" if link.exists() else "is missing"
    if os.path.realpath(link) != os.path.realpath(real_token):
        return _LINK_ELSEWHERE
    return None


def prepare_review_attempt(
    review_id: str,
    attempt_id: str,
    manifest_path: Path | str,
    harness: str,
    *,
    receipts_root: Path | None = None,
) -> ReviewMcpPlan:
    """Prepare the per-attempt stdio sources MCP config, empty ledger, and sidecar.

    Args:
        review_id: Identifier of the formal review job.
        attempt_id: Unique attempt identifier.
        manifest_path: Path to the review manifest YAML.
        harness: Agent harness name (e.g. 'claude', 'cursor').
        receipts_root: Optional override for the receipts base directory (used in tests).

    Returns:
        ReviewMcpPlan containing the written config path and adapter options.

    Raises:
        ValueError: If tokens are invalid or harness is unsupported.
        FileExistsError: If ledger, sidecar, or config already exists.
        FileNotFoundError: If manifest_path does not exist.
    """
    if not isinstance(review_id, str) or not _TOKEN_RE.match(review_id):
        raise ValueError(f"invalid review_id: must match {_TOKEN_RE.pattern} (got {_describe_identifier(review_id)})")
    if not isinstance(attempt_id, str) or not _TOKEN_RE.match(attempt_id):
        raise ValueError(f"invalid attempt_id: must match {_TOKEN_RE.pattern} (got {_describe_identifier(attempt_id)})")

    canonical_harness = (harness or "").lower().strip()
    if canonical_harness in UNSUPPORTED_HARNESS_REASONS:
        raise ValueError(
            f"review attempt refused for {canonical_harness}: {UNSUPPORTED_HARNESS_REASONS[canonical_harness]} (#8517)"
        )
    if canonical_harness not in SUPPORTED_HARNESSES:
        raise ValueError(
            f"review attempt refused for unsupported harness (supported: {', '.join(sorted(SUPPORTED_HARNESSES))}; "
            f"got {_describe_identifier(canonical_harness)}) (#8517)"
        )

    manifest_file = Path(manifest_path).resolve()
    if not manifest_file.is_file():
        raise FileNotFoundError(f"review manifest file not found: {_echo_identifier(manifest_file.name)!r}")

    manifest_bytes = manifest_file.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    # Primary checkout root: resolved via repository helper scripts.common.repo_root
    primary_root = resolve_repo_root(Path(__file__), 2)
    python_bin = primary_root / ".venv" / "bin" / "python"
    sources_server = primary_root / ".mcp" / "servers" / "sources" / "server.py"

    if receipts_root is None:
        # The primary checkout is the trusted anchor; every runtime component below it is walked.
        base_dir = primary_root / "batch_state" / "review-receipts"
        anchor, components = primary_root, ("batch_state", "review-receipts", review_id)
    else:
        # An explicit root: its nearest existing ancestor is trusted, everything below is walked.
        base_dir = Path(os.path.abspath(receipts_root))
        anchor = base_dir.parent
        while not anchor.exists():
            anchor = anchor.parent
        components = (*base_dir.relative_to(anchor).parts, review_id)
    review_dir = base_dir / review_id

    ledger_name = f"{attempt_id}.jsonl"
    sidecar_name = f"{attempt_id}.jsonl.sha256"
    config_name = f"{attempt_id}.mcp.json"
    ledger_path = review_dir / ledger_name
    sidecar_path = review_dir / sidecar_name
    config_path = review_dir / config_name
    codex_home = codex_review_home_path(config_path) if canonical_harness == "codex" else None
    agy_home = agy_review_home_path(config_path) if canonical_harness == "agy" else None
    real_agy_token = _real_agy_token() if agy_home is not None else None
    if real_agy_token is not None and not real_agy_token.exists():
        raise ValueError(
            f"AGY OAuth token not found for the scoped review home: no {_AGY_TOKEN_NAME} in the "
            "real AGY_APP_DATA_DIR (default ~/.gemini/antigravity-cli) (#8617)"
        )

    sidecar_bytes = f"{_EMPTY_SHA256}\n".encode("ascii")
    config_payload = {
        "mcpServers": {
            "sources": {
                "command": str(python_bin),
                "args": [str(sources_server)],
                "env": {
                    ENV_ATTEMPT_ID: attempt_id,
                    ENV_MANIFEST_SHA256: manifest_sha256,
                    ENV_LEDGER_PATH: str(ledger_path),
                },
            }
        }
    }
    config_bytes = (json.dumps(config_payload, indent=2) + "\n").encode("utf-8")

    # Create or open each runtime directory without following symlinks (refusing any that is a
    # symlink or foreign-owned), then create every per-attempt file relative to this descriptor
    # so a component swapped in after the check cannot redirect them (#8652).
    review_fd = _open_runtime_dir(anchor, components)
    created: list[str] = []

    def _rollback() -> None:
        for name in reversed(created):
            with contextlib.suppress(OSError):
                if stat.S_ISDIR(os.stat(name, dir_fd=review_fd, follow_symlinks=False).st_mode):
                    shutil.rmtree(name, ignore_errors=True, dir_fd=review_fd)
                else:
                    os.unlink(name, dir_fd=review_fd)

    def _already_exists() -> FileExistsError:
        return FileExistsError(
            f"review attempt {_echo_identifier(attempt_id)!r} already exists for review {_echo_identifier(review_id)!r}"
        )

    try:
        # Driver settlement 5: create ledger, sidecar, and config with O_EXCL; refuse if any already exists
        existing = [ledger_name, sidecar_name, config_name]
        existing += [home.name for home in (codex_home, agy_home) if home is not None]
        if any(_lexists(name, review_fd) for name in existing):
            raise _already_exists()

        for name, payload in ((ledger_name, b""), (sidecar_name, sidecar_bytes), (config_name, config_bytes)):
            _create_file(name, review_fd, payload)
            created.append(name)

        if codex_home is not None:
            # Exclusive mkdir: refuses a pre-existing (or pre-planted) home.
            os.mkdir(codex_home.name, 0o700, dir_fd=review_fd)
            created.append(codex_home.name)
            home_fd = _open_owned_dir(codex_home.name, dir_fd=review_fd)
            try:
                _create_file(
                    "config.toml",
                    home_fd,
                    _render_codex_review_config(
                        python_bin, sources_server, config_payload["mcpServers"]["sources"]["env"]
                    ).encode("utf-8"),
                )
                _link_codex_auth(home_fd)
            finally:
                os.close(home_fd)

        if agy_home is not None and real_agy_token is not None:
            # Exclusive mkdir: refuses a pre-existing (or pre-planted) home.
            os.mkdir(agy_home.name, 0o700, dir_fd=review_fd)
            created.append(agy_home.name)
            home_fd = _open_owned_dir(agy_home.name, dir_fd=review_fd)
            try:
                _populate_agy_review_home(home_fd, real_agy_token, config_bytes)
            finally:
                os.close(home_fd)
    except FileExistsError as exc:
        _rollback()
        raise _already_exists() from exc
    except BaseException:
        _rollback()
        raise
    finally:
        os.close(review_fd)

    adapter_options: dict[str, Any] = {
        "mcp_config_path": str(config_path),
        "strict_mcp_config": True,
        "mcp_server_names": ["sources"],
    }
    allowed_tools = review_tools_allowed_csv(canonical_harness)
    if allowed_tools is not None:
        adapter_options["allowed_tools"] = allowed_tools
    if codex_home is not None:
        adapter_options["codex_home_override"] = str(codex_home)
    if agy_home is not None:
        adapter_options["agy_home_override"] = str(agy_home)

    return ReviewMcpPlan(
        config_path=config_path,
        adapter_options=adapter_options,
        ledger_path=ledger_path,
        sidecar_path=sidecar_path,
        manifest_sha256=manifest_sha256,
        review_id=review_id,
        attempt_id=attempt_id,
        harness=canonical_harness,
        codex_home=codex_home,
        agy_home=agy_home,
    )


def _config_flags(argv: Sequence[str]) -> list[str]:
    """Return the config-affecting flags (``-c``/``--enable``/``--disable`` pairs) of a Codex argv."""
    flags: list[str] = []
    for index, item in enumerate(argv[:-1]):
        if item in {"-c", "--config", "--enable", "--disable"}:
            flags.extend([item, argv[index + 1]])
    return flags


def verify_codex_review_effective_mcp(
    *,
    config_path: Path | str,
    cwd: Path | str,
    config_flags: Sequence[str] = (),
    codex_bin: str | None = None,
    timeout: float = _CODEX_MCP_LIST_TIMEOUT_S,
) -> None:
    """Refuse a Codex review attempt unless its effective MCP set is exactly ``sources``.

    Runs ``codex mcp list --json`` with the attempt's scoped ``CODEX_HOME``, the launch
    cwd and the launch config flags, so trusted project config and ``-c`` overrides are
    counted. Fails closed: a failed probe is a refusal, never a pass.

    Raises:
        CodexReviewMcpGateError: on any deviation, naming #8517.
    """
    config = Path(config_path)
    codex_home = codex_review_home_path(config)
    log_unsafe = {"$CODEX_HOME": str(codex_home), "~": os.path.expanduser("~")}
    diagnostics = review_diagnostics_path(config)

    def refuse(reason: str) -> CodexReviewMcpGateError:
        return CodexReviewMcpGateError(f"codex review attempt refused: {_mask(reason, log_unsafe)} (#8517)")

    try:
        expected = json.loads(config.read_text(encoding="utf-8"))["mcpServers"]["sources"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise refuse(
            f"cannot read the attempt MCP config {_echo_identifier(config.name)!r}: {_exc_reason(exc, diagnostics)}"
        ) from exc
    if not (codex_home / "config.toml").is_file():
        raise refuse("the scoped CODEX_HOME has no config.toml")

    binary = codex_bin or shutil.which("codex") or "codex"
    env = {**os.environ, "CODEX_HOME": str(codex_home)}
    try:
        proc = subprocess.run(
            [binary, "mcp", "list", "--json", *config_flags],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise refuse(f"could not compute the effective MCP set ({_exc_reason(exc, diagnostics)})") from exc
    if proc.returncode != 0:
        raise refuse(f"`codex mcp list` exited {proc.returncode}: {_untrusted('stderr', proc.stderr, diagnostics)}")
    try:
        servers = json.loads(proc.stdout)
    except ValueError as exc:
        raise refuse(
            f"`codex mcp list --json` did not return JSON: {_exc_reason(exc, diagnostics)}; "
            f"{_untrusted('stdout', proc.stdout, diagnostics)}"
        ) from exc
    if not isinstance(servers, list):
        raise refuse("`codex mcp list --json` did not return a list")

    names = sorted(str(item.get("name")) if isinstance(item, dict) else repr(item) for item in servers)
    if names != ["sources"]:
        raise refuse(f"effective MCP servers are {_describe_names(names)}; exactly ['sources'] is allowed")
    server = servers[0]
    transport = server.get("transport") or {}
    if server.get("enabled") is not True:
        raise refuse("the sources server is not enabled")
    if transport.get("type") != "stdio":
        raise refuse(f"the sources server transport is {_echo_identifier(transport.get('type'))!r}, not stdio")
    if transport.get("command") != expected["command"] or list(transport.get("args") or []) != expected["args"]:
        raise refuse("the sources server command/args differ from the attempt's .mcp.json")
    if dict(transport.get("env") or {}) != expected["env"]:
        raise refuse("the sources server env differs from the attempt's .mcp.json")


def verify_codex_review_launch(
    *,
    config_path: Path | str,
    cwd: Path,
    mode: str,
    model: str | None,
    effort: str | None,
    task_id: str,
    tool_config: dict[str, Any],
) -> None:
    """Run the effective-config gate with the exact flags the Codex adapter will launch with."""
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    plan = CodexAdapter().build_invocation(
        prompt="",
        mode=mode,
        cwd=cwd,
        model=model,
        task_id=task_id,
        session_id=None,
        tool_config=dict(tool_config),
        effort=effort,
    )
    try:
        verify_codex_review_effective_mcp(
            config_path=config_path,
            cwd=plan.cwd,
            config_flags=_config_flags(plan.cmd),
            codex_bin=plan.cmd[0],
        )
    finally:
        with contextlib.suppress(OSError):
            Path(plan.output_file).unlink(missing_ok=True)


def _agy_mcp_list_rows(
    stdout: str, refuse: Callable[[str], AgyReviewMcpGateError], diagnostics: Path
) -> list[dict[str, str]]:
    """Strictly parse ``agy mcp list`` (a padded text table with no JSON mode).

    The header must be exactly ``NAME TYPE STATUS COMMAND/URL``; every other non-empty
    line must be a data row whose cells start at the header's column offsets. Anything
    short, misaligned, blank-celled or repeated is a refusal, never a skipped line.
    """
    lines = [line.rstrip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise refuse("`agy mcp list` printed no table")
    header = re.fullmatch(r"(NAME)(\s+)(TYPE)(\s+)(STATUS)(\s+)(COMMAND/URL)", lines[0])
    if header is None or header.start(1) != 0:
        raise refuse(
            f"`agy mcp list` header is not {' '.join(_AGY_MCP_LIST_COLUMNS)!r}: "
            f"{_untrusted('header', lines[0], diagnostics)}"
        )
    offsets = [header.start(group) for group in (1, 3, 5, 7)]

    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if len(line) <= offsets[3] or any(line[offset - 1] != " " or line[offset] == " " for offset in offsets[1:]):
            raise refuse(f"`agy mcp list` row is truncated or misaligned: {_untrusted('row', line, diagnostics)}")
        name = line[offsets[0] : offsets[1]].strip()
        kind = line[offsets[1] : offsets[2]].strip()
        status = line[offsets[2] : offsets[3]].strip()
        target = line[offsets[3] :].strip()
        if any(not cell or any(ch.isspace() for ch in cell) for cell in (name, kind, status)):
            raise refuse(f"`agy mcp list` row cannot be parsed: {_untrusted('row', line, diagnostics)}")
        rows.append({"name": name, "type": kind, "status": status, "target": target})
    names = [row["name"] for row in rows]
    if len(set(names)) != len(names):
        raise refuse(f"`agy mcp list` repeats a server name: {_describe_names(names)}")
    return rows


def _exc_reason(exc: BaseException, diagnostics: Path) -> str:
    """Describe an exception for a refusal: its class, its errno code and a fingerprint, never its text.

    ``str(exc)`` is untrusted (``OSError`` carries the file name and ``strerror``, ``SubprocessError``
    the command line, a parser error a slice of the input), so it goes to the diagnostics file and
    the refusal shows only the class name, ``errno.errorcode[exc.errno]`` (e.g. ``ENOENT``) when
    present, and ``_untrusted``'s length and fingerprint.
    """
    code = _errno_name(exc) if isinstance(exc, OSError) else None
    head = f"{type(exc).__name__} ({code})" if code else type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        head = f"{head} after {exc.timeout:g}s"
    return f"{head}: {_untrusted('exception', exc, diagnostics)}"


def _strict_json_object(text: str) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        if len(set(keys)) != len(keys):
            raise ValueError(f"duplicate JSON keys: {_describe_names(keys)}")
        return dict(pairs)

    return json.loads(text, object_pairs_hook=no_duplicates)


def verify_agy_review_effective_mcp(
    *,
    config_path: Path | str,
    cwd: Path | str,
    env: Mapping[str, str],
    agy_bin: str,
    timeout: float = _AGY_MCP_LIST_TIMEOUT_S,
) -> None:
    """Refuse an AGY review attempt unless its effective MCP set is exactly ``sources``.

    ``agy mcp list`` (run under ``env``, the environment the launch will get) proves the
    server set, name, transport, enabled state and command line; it does not show ``env``,
    so the one config file ``agy -p`` loads is read back and compared as well. Fails
    closed: a failed probe is a refusal, never a pass.

    Raises:
        AgyReviewMcpGateError: on any deviation, naming #8617.
    """
    config = Path(config_path)
    # The launch environment is not log-safe: its HOME/AGY_APP_DATA_DIR and the operator's home
    # can surface in probe output echoed into a refusal, so every refusal masks them.
    log_unsafe = {
        "$AGY_APP_DATA_DIR": env.get("AGY_APP_DATA_DIR"),
        "$HOME": env.get("HOME"),
        "~": os.path.expanduser("~"),
    }
    diagnostics = review_diagnostics_path(config)

    def refuse(reason: str) -> AgyReviewMcpGateError:
        return AgyReviewMcpGateError(f"agy review attempt refused: {_mask(reason, log_unsafe)} (#8617)")

    try:
        expected = json.loads(config.read_text(encoding="utf-8"))["mcpServers"]["sources"]
        command = expected["command"]
        args = list(expected["args"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise refuse(
            f"cannot read the attempt MCP config {_echo_identifier(config.name)!r}: {_exc_reason(exc, diagnostics)}"
        ) from exc
    if not isinstance(expected.get("env"), dict) or set(expected["env"]) != set(ENV_KEYS):
        raise refuse("the attempt MCP config does not carry exactly the three LU_REVIEW_* variables")

    agy_home = agy_review_home_path(config)
    app_data = agy_review_app_data_dir(agy_home)
    if env.get("HOME") != str(agy_home) or env.get("AGY_APP_DATA_DIR") != str(app_data):
        # Name the variables, never their values: the launch environment is not log-safe.
        raise refuse("the launch environment does not carry the scoped HOME/AGY_APP_DATA_DIR")
    if (app_data / "mcp_config.json").exists() or (app_data / "mcp_config.json").is_symlink():
        raise refuse("the scoped AGY_APP_DATA_DIR holds an unexpected mcp_config.json")

    parts = [command, *args]
    if any(not isinstance(part, str) or not part or any(ch.isspace() for ch in part) for part in parts):
        raise refuse(
            "the attempt command or args contain whitespace or an empty part, so the flat "
            "`agy mcp list` COMMAND/URL text cannot identify them uniquely"
        )
    expected_target = " ".join(parts)

    try:
        proc = subprocess.run(
            [agy_bin, "mcp", "list"],
            cwd=str(cwd),
            env=dict(env),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise refuse(f"could not compute the effective MCP set ({_exc_reason(exc, diagnostics)})") from exc
    if proc.returncode != 0:
        raise refuse(f"`agy mcp list` exited {proc.returncode}: {_untrusted('stderr', proc.stderr, diagnostics)}")

    rows = _agy_mcp_list_rows(proc.stdout, refuse, diagnostics)
    if [row["name"] for row in rows] != ["sources"]:
        raise refuse(
            f"effective MCP servers are {_describe_names([row['name'] for row in rows])}; exactly ['sources'] is allowed"
        )
    row = rows[0]
    if row["type"] != "stdio":
        raise refuse(f"the sources server type is {_echo_identifier(row['type'])!r}, not stdio")
    if row["status"] != "enabled":
        raise refuse(f"the sources server status is {_echo_identifier(row['status'])!r}, not enabled")
    if row["target"] != expected_target:
        raise refuse("the sources server command/args differ from the attempt's .mcp.json")

    scoped_config = agy_review_mcp_config_path(agy_home)
    try:
        loaded = _strict_json_object(scoped_config.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refuse(
            f"cannot read the scoped agy MCP config (.gemini/config/mcp_config.json under the scoped HOME): "
            f"{_exc_reason(exc, diagnostics)}"
        ) from exc
    if not isinstance(loaded, dict) or set(loaded) != {"mcpServers"}:
        raise refuse("the scoped agy MCP config has keys other than mcpServers")
    servers = loaded["mcpServers"]
    if not isinstance(servers, dict) or set(servers) != {"sources"}:
        raise refuse("the scoped agy MCP config does not hold exactly the one sources server")
    if servers["sources"] != expected:
        raise refuse(
            "the scoped agy MCP config's sources server (command/args/env) differs from the attempt's .mcp.json"
        )


def verify_agy_review_launch(
    *,
    config_path: Path | str,
    cwd: Path,
    mode: str,
    model: str | None,
    effort: str | None,
    task_id: str,
    tool_config: dict[str, Any],
) -> None:
    """Run the effective-config gate under the exact environment the AGY launch will get."""
    from scripts.agent_runtime.adapters.agy import AgyAdapter
    from scripts.agent_runtime.env_sanitize import build_agent_env

    agy_home = agy_review_home_path(config_path)
    link_state = _agy_oauth_link_state(agy_review_app_data_dir(agy_home) / _AGY_TOKEN_NAME, _real_agy_token())
    if link_state is not None:
        raise AgyReviewMcpGateError(
            f"agy review attempt refused: OAuth link not intact: the scoped {_AGY_TOKEN_NAME} {link_state} (#8617)"
        )

    plan = AgyAdapter().build_invocation(
        prompt="",
        mode=mode,
        cwd=cwd,
        model=model,
        task_id=task_id,
        session_id=None,
        tool_config=dict(tool_config),
        effort=effort,
    )
    env = build_agent_env(provider="agy", overrides=plan.env_overrides)
    try:
        for key in plan.env_unsets:
            env.pop(key, None)
        verify_agy_review_effective_mcp(config_path=config_path, cwd=plan.cwd, env=env, agy_bin=plan.cmd[0])
    finally:
        # build_agent_env leaves a throwaway git-config sandbox; the gate has no use for it.
        sandbox = Path(env.get("GIT_CONFIG_GLOBAL", "")).parent
        if sandbox.name.startswith("lu-agent-runtime-git-"):
            shutil.rmtree(sandbox, ignore_errors=True)
