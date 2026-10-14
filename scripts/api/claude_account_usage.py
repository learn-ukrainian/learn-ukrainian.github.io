"""Per-account Claude usage rows for the routing budget (#10630).

One bounded CodexBar probe per registered Claude account label, run only by
the background usage refresh. ``claude_accounts_snapshot`` serves the cache: it
never starts a probe and never opens, reads or parses a file. Rows carry
numbers and freshness, never identity: no account id, email, organization or
directory appears in any row.

Label ``a`` is the host's default Claude directory, bound to the account
recorded at login beside it. Every other label takes its directory and account
from the private binding read by ``load_claude_account_binding``; a missing or
refused binding makes that row unknown, never an endpoint error.

Threat model: the label is accounting and display, not isolation against a
hostile process of the same user. The risk closed here is a row of the wrong
account published as ``ok`` or preferred through accidental or latent drift: a
binding reassigned or removed while its sample is cached, a directory replaced
or linked between validation and probe, credentials of another account in the
bound directory while its login record still names the bound one, or an answer
naming an account other than the bound one. Each of these withholds the row as
``unknown``, never ``ok``. Restoring a file between two checks is out of scope.

The selected directory is the only thing that selects the account. The query
pins CodexBar's Claude source to OAuth, which reads only that directory's
credentials, and the child runs with a fresh private home, cache and data
location and no CodexBar configuration, so no shared configuration, token
account or cache can substitute another account.

Proof: a sample is attributed to its label only on positive proof. The
provider names the owner of the access token the label's directory holds, the
token CodexBar's OAuth source reads, and that owner must be the bound account.
Login metadata, CodexBar's own identity fields and pairwise inequality are not
proof. ``account_binding`` validates a label's directory and holds it open for
the whole probe; afterwards the binding must validate again to the same
generation (directory identity and bound account), and credentials rewritten in
between must be proven the bound account's too, or the sample is refused. An
account id CodexBar names must be the bound account; any other identity it
names is compared only across labels. When two served samples share an
account, one names its account and another does not, or one cannot be
identified, every served row is withheld as ``account_ambiguous``.

Serving: every read, parse and provider question runs in the background. Each
sample keeps the cheap stat facts of every file its validation read (type,
device and inode; for files also mode, owner, size and change times), with its
generation and private fingerprints of its account, none of them published,
logged or serialised. Serving only ``lstat``s those paths: any difference
withholds the row as ``not_probed`` and schedules one background revalidation,
which re-arms the sample when the binding still validates to the same
generation (asking the provider again only about changed credentials) and
otherwise forgets it.

Freshness is computed when a row is served, from the measured state's
timestamp, never frozen into a stored payload.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import logging
import math
import os
import secrets
import selectors
import shutil
import signal
import stat
import subprocess
import threading
import time
from collections.abc import Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.attempt_boundary import (
    _CLAUDE_ACCOUNT_UUID_RE,
    CLAUDE_ACCOUNT_LABELS,
    CLAUDE_ACCOUNT_REFUSAL_CODES,
    DEFAULT_CLAUDE_ACCOUNT,
    ClaudeAccountRefused,
    _claude_access_token,
    _claude_config_account_uuid,
    _claude_selected_identity,
    _open_claude_directory,
    claude_accounts_file,
    load_claude_account_binding,
)
from scripts.api.subscription_usage import _codexbar_bin, _codexbar_cache_ttl_s, _parse_resets_at_any
from scripts.common import scratch

_log = logging.getLogger(__name__)

PROBE_TIMEOUT_S = 60.0
MAX_OUTPUT_BYTES = 1024 * 1024
# ``--source oauth`` wins over any configured source; in CodexBar's CLI runtime
# it runs the OAuth step alone, with no web or CLI fallback.
_SOURCE = "oauth"
_QUERY = ("usage", "--json", "--provider", "claude", "--source", _SOURCE)
# The child gets these names from the API process and nothing else. Credential
# variables (ANTHROPIC_*, CLAUDE_CODE_OAUTH_TOKEN, CLAUDE_SECURESTORAGE_CONFIG_DIR,
# ...) and shared configuration locations never reach it.
_INHERITED_ENV_NAMES = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ")
# Every home, cache, data and config location points at the probe's private sandbox.
_SANDBOX_ENV_NAMES = (
    "HOME",
    "TMPDIR",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
)
# Never created: CodexBar runs with its built-in defaults and no token accounts.
_CODEXBAR_CONFIG_NAME = "codexbar-config.json"
# Probe sandboxes live in this private directory under the fleet scratch root.
_SANDBOX_PARENT = "account-usage-probe"
_SANDBOX_PREFIX = "lu-claude-usage-"
_LOGIN_RECORD = ".claude.json"
_CREDENTIALS = ".credentials.json"
_WINDOWS = (("primary", "session5h"), ("secondary", "weekly"))
_WINDOW_FIELDS = ("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct")

ACCOUNT_AMBIGUOUS = "account_ambiguous"
# Every probe failure code. Codes name no value or location.
PROBE_FAILURE_CODES = frozenset(
    {
        "missing_binary",
        "spawn_error",
        "timeout",
        "oversized",
        "exit_nonzero",
        "bad_json",
        "provider_mismatch",
        "provider_error",
        "source_mismatch",
        "no_usage",
        "out_of_range",
        "bad_timestamp",
        "sandbox_unavailable",
        "probe_error",
    }
)
# Every ``reason`` a published row may carry.
ROW_REASON_CODES = PROBE_FAILURE_CODES | CLAUDE_ACCOUNT_REFUSAL_CODES | {"not_probed", "expired", ACCOUNT_AMBIGUOUS}


Facts = tuple[int, ...]


@dataclass(frozen=True)
class _Watch:
    """What one binding validation read, as cheap stat facts; never published or logged."""

    roots: tuple[Path | None, ...] = field(repr=False)  # where the validation starts, found without reading
    entries: tuple[tuple[Path, bool, Facts | None], ...] = field(repr=False)  # (path, is directory, facts)
    generation: bytes = field(repr=False)  # digest of the directory identity and the bound account
    credentials: Facts | None = field(repr=False)  # the credentials whose owner the provider named


@dataclass(frozen=True)
class _Binding:
    """A label's validated binding while its directory is held open; never published or logged."""

    config_dir: Path = field(repr=False)
    account: str = field(repr=False)  # the bound account, proven owner of the directory's credentials
    watch: _Watch = field(repr=False)

    @property
    def generation(self) -> bytes:
        return self.watch.generation


@dataclass(frozen=True)
class _Accounts:
    """What a sample is attributed to; never published, logged or serialised."""

    watch: _Watch = field(repr=False)  # the validation it is served under
    fingerprints: frozenset[bytes] = field(repr=False)  # the bound and the named accounts
    named: bool = field(repr=False)  # CodexBar's answer named an account

    @property
    def generation(self) -> bytes:
        return self.watch.generation


@dataclass(frozen=True)
class _Sample:
    """A label's last good measurement."""

    source_at: float  # epoch seconds of the measured state
    windows: dict[str, dict[str, Any]]
    accounts: _Accounts = field(repr=False)


_lock = threading.Lock()
_last_good: dict[str, _Sample] = {}
# label -> failure code of the newest probe or revalidation; absent after a success
_last_failure: dict[str, str] = {}
_revalidation_lock = threading.Lock()
_revalidation: threading.Thread | None = None
_sandbox_residue = 0  # probe sandboxes this process could not remove


class _ProbeFailed(Exception):
    """A probe failure; the code names no value or location."""

    def __init__(self, code: str):
        if code not in PROBE_FAILURE_CODES:
            raise AssertionError("unregistered probe failure code")
        super().__init__(code)
        self.code = code


def row_key(label: str) -> str:
    return f"claude:{label}"


@contextlib.contextmanager
def _open_default_directory(path: Path) -> Iterator[int]:
    """The host's own Claude directory: a real directory, never a link.

    The host chose it, so its mode and ancestors are not checked as a bound
    directory's are.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        raise ClaudeAccountRefused("claude_account_config_dir_missing") from None
    except OSError as exc:
        code = "not_private" if exc.errno in {errno.ELOOP, errno.ENOTDIR} else "unavailable"
        raise ClaudeAccountRefused(f"claude_account_config_dir_{code}") from None
    try:
        yield fd
    finally:
        os.close(fd)


def _facts(path: Path | str, *, directory: bool = False, dir_fd: int | None = None) -> Facts | None:
    """Stat facts of a path, never following its final link; ``None`` when absent.

    A directory is its identity; a file adds mode, owner, size and change times,
    so any rewrite changes them.
    """
    try:
        info = os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    identity = (stat.S_IFMT(info.st_mode), info.st_dev, info.st_ino)
    if directory:
        return identity
    return (*identity, stat.S_IMODE(info.st_mode), info.st_uid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _facts_before_reading(path: Path | str, code: str, *, dir_fd: int | None = None) -> Facts | None:
    """Facts taken before the file is read, so any later rewrite differs from them."""
    try:
        return _facts(path, dir_fd=dir_fd)
    except OSError:
        raise ClaudeAccountRefused(f"{code}_unavailable") from None


def _root_paths(label: str) -> tuple[Path | None, ...]:
    """Where a label's validation starts, found without reading a file."""
    if label == DEFAULT_CLAUDE_ACCOUNT:
        home = Path.home()
        return (home / ".claude", home / _LOGIN_RECORD)
    return (claude_accounts_file(),)


def _generation(label: str, config_dir: Path, directory: Facts, account: str) -> bytes:
    """Digest of the binding facts: label, directory path and identity, bound account."""
    facts = [label, str(config_dir), *directory, account]
    return hashlib.sha256(json.dumps(facts).encode()).digest()


def _prove_owner(directory: int, account: str) -> None:
    """Refuse unless the provider names ``account`` as the owner of the directory's access token.

    The token is the one CodexBar's OAuth source reads from this directory. It
    stays in this frame; refusals carry fixed codes only.
    """
    from scripts.review.isolation import ReviewIsolationError  # noqa: PLC0415  # lazy-ok: review stack off API import

    try:
        token = _claude_access_token(Path(_CREDENTIALS), dir_fd=directory)
    except ReviewIsolationError as exc:
        suffix = str(exc).removeprefix("attempt_claude_auth_")
        raise ClaudeAccountRefused(f"claude_account_credentials_{suffix}") from None
    if token is None:
        raise ClaudeAccountRefused("claude_account_credentials_missing")
    if _claude_selected_identity(token) != account:
        raise ClaudeAccountRefused("claude_account_unverified")


def _proven(
    label: str,
    config_dir: Path,
    directory: int,
    account: str,
    entries: list[tuple[Path, bool, Facts | None]],
    verified: _Watch | None,
) -> _Binding:
    """The binding, once the provider has named its account as the credentials' owner.

    ``verified`` is an earlier validation of the same label: when it proved these
    same credentials for the same generation, the provider is not asked again.
    """
    info = os.fstat(directory)
    identity = (stat.S_IFMT(info.st_mode), info.st_dev, info.st_ino)
    generation = _generation(label, config_dir, identity, account)
    credentials = _facts_before_reading(_CREDENTIALS, "claude_account_credentials", dir_fd=directory)
    proven = (
        verified is not None
        and credentials is not None
        and verified.generation == generation
        and verified.credentials == credentials
    )
    if not proven:
        _prove_owner(directory, account)
    entries = [(config_dir, True, identity), *entries, (config_dir / _CREDENTIALS, False, credentials)]
    return _Binding(config_dir, account, _Watch(_root_paths(label), tuple(entries), generation, credentials))


@contextlib.contextmanager
def account_binding(label: str, *, verified: _Watch | None = None) -> Iterator[_Binding]:
    """Validate a label's binding and hold its Claude directory open until exit.

    The default label is the host's ``~/.claude``, bound to the account recorded
    at login beside it. Any other label is refused with ``ClaudeAccountRefused``
    for a missing, invalid or unsafe binding, one that names the default
    directory (that would count one account twice), or one whose directory does
    not hold the bound account. Either label is refused unless the provider names
    the bound account as the owner of the directory's credentials. Background
    only: it reads, parses and may ask the provider.
    """
    if label == DEFAULT_CLAUDE_ACCOUNT:
        home = Path.home()
        default, record = home / ".claude", home / _LOGIN_RECORD
        with _open_default_directory(default) as directory:
            recorded_facts = _facts_before_reading(record, "claude_account_config")
            recorded = _claude_config_account_uuid(record)
            account = recorded.strip().lower() if isinstance(recorded, str) else ""
            if not _CLAUDE_ACCOUNT_UUID_RE.fullmatch(account):
                raise ClaudeAccountRefused("claude_account_unverified")  # no recorded account to prove
            yield _proven(label, default, directory, account, [(record, False, recorded_facts)], verified)
        return
    binding_file = claude_accounts_file()
    if binding_file is None:
        raise ClaudeAccountRefused("claude_account_binding_missing")
    binding_facts = _facts_before_reading(binding_file, "claude_account_binding")
    binding = load_claude_account_binding(label)
    with _open_claude_directory(binding.config_dir) as directory:
        selected = os.fstat(directory)
        try:
            info = (Path.home() / ".claude").stat()
        except OSError:
            info = None
        if info is not None and (selected.st_dev, selected.st_ino) == (info.st_dev, info.st_ino):
            raise ClaudeAccountRefused("claude_account_binding_is_default")
        recorded_facts = _facts_before_reading(_LOGIN_RECORD, "claude_account_config", dir_fd=directory)
        if _claude_config_account_uuid(Path(_LOGIN_RECORD), dir_fd=directory) != binding.account_uuid:
            raise ClaudeAccountRefused("claude_account_unverified")
        entries = [(binding_file, False, binding_facts), (binding.config_dir / _LOGIN_RECORD, False, recorded_facts)]
        yield _proven(label, binding.config_dir, directory, binding.account_uuid, entries, verified)


def _fingerprint(kind: str, value: str) -> bytes:
    return hashlib.sha256(f"{kind}\0{value}".encode()).digest()


def child_env(config_dir: Path, environ: Mapping[str, str] | None = None, *, sandbox: Path) -> dict[str, str]:
    """Probe environment: inherited locale and path names, the private sandbox for
    every home, cache and config location, no CodexBar configuration, and the
    label's Claude directory."""
    env = os.environ if environ is None else environ
    child = {name: env[name] for name in _INHERITED_ENV_NAMES if env.get(name)}
    child.update(dict.fromkeys(_SANDBOX_ENV_NAMES, str(sandbox)))
    child["CODEXBAR_CONFIG"] = str(sandbox / _CODEXBAR_CONFIG_NAME)
    child["CLAUDE_CONFIG_DIR"] = str(config_dir)
    return child


def _await_exit(pid: int, deadline: float) -> None:
    """Wait for the leader to exit without reaping it, so its group id stays reserved."""
    delay = 0.005
    while os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT | os.WNOHANG) is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _ProbeFailed("timeout")
        time.sleep(min(delay, remaining))
        delay = min(delay * 2, 0.1)


def _run_codexbar(codexbar: str, env: dict[str, str], *, timeout_s: float, max_bytes: int) -> bytes:
    """Run the fixed Claude usage query without a shell, outside the repository,
    under a hard deadline and output cap.

    The child gets its own process group. Every helper it started is killed on
    every path, success included, before the leader is reaped.
    """
    try:
        proc = subprocess.Popen(
            [codexbar, *_QUERY],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            cwd="/",
            close_fds=True,
            start_new_session=True,
        )
    except OSError:
        raise _ProbeFailed("spawn_error") from None
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout_s
    chunks: list[bytes] = []
    size = 0
    selector = selectors.DefaultSelector()
    try:
        selector.register(proc.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise _ProbeFailed("timeout")
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise _ProbeFailed("oversized")
            chunks.append(chunk)
        _await_exit(proc.pid, deadline)
    finally:
        selector.close()
        # The leader is running or an unreaped zombie here, so its group id
        # cannot have been reused yet.
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        returncode = proc.wait()
        proc.stdout.close()
    if returncode != 0:
        raise _ProbeFailed("exit_nonzero")
    return b"".join(chunks)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _percent(value: Any) -> float | None:
    """A percentage from CodexBar: unknown when absent, a failure outside 0..100."""
    number = _number(value)
    if number is not None and not 0 <= number <= 100:
        raise _ProbeFailed("out_of_range")
    return number


def _timestamp(value: Any) -> datetime | None:
    """An ISO-8601 or epoch timestamp in UTC; ``None`` for anything else."""
    try:
        return _parse_resets_at_any(value)
    except OverflowError:
        return None


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def projected_leftover_pct(used: float | None, expected: float | None) -> int | None:
    """Weekly share left at reset if the burn so far continues; 0 = runs out early.

    ``expected`` is the elapsed share of the window, so ``used / expected`` is the
    projected use. Unknown when either value is missing or ``expected`` is not
    positive; otherwise clamped to 0..100.
    """
    if used is None or expected is None or expected <= 0:
        return None
    return min(100, max(0, round(100 - used * 100 / expected)))


def _pace_label(delta: float | None) -> str | None:
    """Pace text derived from the numbers; never upstream free text."""
    if delta is None:
        return None
    points = round(abs(delta))
    if points == 0:
        return "on pace"
    return f"{points}% in {'deficit' if delta > 0 else 'reserve'}"


def _window_row(usage_window: Any, pace_window: Any) -> dict[str, Any]:
    window = usage_window if isinstance(usage_window, dict) else {}
    pace = pace_window if isinstance(pace_window, dict) else {}
    used = _percent(window.get("usedPercent"))
    expected = _percent(pace.get("expectedUsedPercent"))
    delta = None if used is None or expected is None else round(used - expected, 1)
    resets_at = _timestamp(window.get("resetsAt"))
    return {
        "left_pct": None if used is None else 100 - used,
        "resets_at": None if resets_at is None else _iso(resets_at),
        "pace": _pace_label(delta),
        "pace_delta_pct": delta,
        "leftover_pct": projected_leftover_pct(used, expected),
    }


def _claude_item(payload: Any) -> dict[str, Any]:
    """The Claude entry of a CodexBar answer, checked against the pinned query."""
    item = payload
    if isinstance(payload, list):
        item = next(
            (entry for entry in payload if isinstance(entry, dict) and entry.get("provider") == "claude"),
            payload[0] if payload else None,
        )
    if not isinstance(item, dict):
        raise _ProbeFailed("bad_json")
    if item.get("provider") not in (None, "claude"):
        raise _ProbeFailed("provider_mismatch")
    if item.get("error"):
        raise _ProbeFailed("provider_error")
    # Another source, or a configured token account, means the directory did not
    # select the account.
    if item.get("source") != _SOURCE or item.get("account") is not None:
        raise _ProbeFailed("source_mismatch")
    return item


def parse_codexbar_claude(payload: Any) -> dict[str, Any]:
    """Numbers from ``codexbar usage --json --provider claude --source oauth``.

    Identity fields are dropped. Timestamps are parsed and normalised to UTC; pace
    is derived from the numbers.
    """
    item = _claude_item(payload)
    usage = item.get("usage")
    if not isinstance(usage, dict):
        raise _ProbeFailed("no_usage")
    pace = item.get("pace") if isinstance(item.get("pace"), dict) else {}
    row: dict[str, Any] = {name: _window_row(usage.get(key), pace.get(key)) for key, name in _WINDOWS}
    if row["session5h"]["left_pct"] is None and row["weekly"]["left_pct"] is None:
        raise _ProbeFailed("no_usage")
    updated = usage.get("updatedAt")
    parsed = None if updated is None else _timestamp(updated)
    if updated is not None and parsed is None:
        raise _ProbeFailed("bad_timestamp")
    row["updated"] = None if parsed is None else _iso(parsed)
    return row


def _named(kind: str, value: Any) -> tuple[str, str] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return kind, value.strip().lower()


def _named_accounts(payload: Any) -> frozenset[tuple[str, str]]:
    """Account identity CodexBar named, by namespace.

    An ``accountID`` shaped as a Claude account UUID is an ``account_id``, the
    binding's own namespace; any other ``accountID`` is an ``opaque_id`` and an
    email is an ``email``, comparable only with another label's.
    """
    usage = _claude_item(payload).get("usage")
    usage = usage if isinstance(usage, dict) else {}
    identity = usage.get("identity") if isinstance(usage.get("identity"), dict) else {}
    account_id = _named("account_id", identity.get("accountID"))
    if account_id is not None and not _CLAUDE_ACCOUNT_UUID_RE.fullmatch(account_id[1]):
        account_id = ("opaque_id", account_id[1])
    found = {account_id, _named("email", identity.get("accountEmail")), _named("email", usage.get("accountEmail"))}
    return frozenset(item for item in found if item is not None)


def _attribute(binding: _Binding, payload: Any) -> _Accounts:
    """What the sample measured, checked against its proven binding.

    Refuses an answer that names an account id other than the bound account.
    Other identity CodexBar names is not proof; it is compared across labels.
    """
    named = _named_accounts(payload)
    bound = {("account_id", binding.account)}
    if {item for item in named if item[0] == "account_id"} - bound:
        raise ClaudeAccountRefused("claude_account_unverified")
    fingerprints = frozenset(_fingerprint(kind, value) for kind, value in bound | named)
    return _Accounts(binding.watch, fingerprints, named=bool(named))


def _scratch_root() -> Path:
    """The fleet scratch root for this probe: the override, else the default.

    Never the system temp fallback the shared helper uses: a probe with no
    usable root is refused instead.
    """
    override = os.environ.get(scratch.SCRATCH_ROOT_ENV_VAR, "").strip()
    return Path(override) if override else scratch.DEFAULT_SCRATCH_ROOT


def _shared_safely(info: os.stat_result, owners: set[int], *, own_group_may_write: bool = False) -> bool:
    """A real directory of an allowed owner that no other user can rename entries in.

    A sticky directory lets others create but not rename or remove what is ours.
    ``own_group_may_write`` also accepts group write when the group is this
    user's own primary group, as on the host's default scratch root.
    """
    if not stat.S_ISDIR(info.st_mode) or info.st_uid not in owners:
        return False
    writable = info.st_mode & 0o022
    if own_group_may_write and info.st_gid == os.getgid():
        writable &= ~stat.S_IWGRP
    return not writable or bool(info.st_mode & stat.S_ISVTX)


def _git_tree(directory: Path) -> bool:
    """True when ``directory`` is a Git directory or the top of a Git checkout."""
    if directory.name == ".git" or os.path.lexists(directory / ".git"):
        return True
    return (directory / "HEAD").is_file() and (directory / "objects").is_dir() and (directory / "refs").is_dir()


def _inside_git(path: Path) -> bool:
    """True when ``path`` (resolved) is inside a Git checkout or a Git directory."""
    return any(_git_tree(directory) for directory in (path, *path.parents))


def _create_sandbox() -> Path:
    """Create one private (0700) directory for a probe, or raise ``_ProbeFailed``.

    The scratch root may be shared with this user's own primary group (the host
    default is): it must be a real directory, not a link, owned by this user or
    root and not writable by anyone else unless sticky. Sandboxes go into
    ``_SANDBOX_PARENT`` below it, a real directory owned by this user and not
    group- or world-writable unless sticky. Neither may be inside a Git
    checkout or Git directory. Each directory is created and checked through
    the descriptor of the one above it, and the path handed to the child must
    name what was created. Every failure is the value-free
    ``sandbox_unavailable``; there is no fallback location.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    root_fd = parent_fd = None
    try:
        root = _scratch_root()
        if not root.is_absolute():
            raise _ProbeFailed("sandbox_unavailable")
        with contextlib.suppress(FileExistsError):
            os.mkdir(root, 0o700)
        root_fd = os.open(root, flags)
        if not _shared_safely(os.fstat(root_fd), {0, os.getuid()}, own_group_may_write=True):
            raise _ProbeFailed("sandbox_unavailable")
        parent = Path(os.path.realpath(root)) / _SANDBOX_PARENT
        if _inside_git(parent):
            raise _ProbeFailed("sandbox_unavailable")
        with contextlib.suppress(FileExistsError):
            os.mkdir(_SANDBOX_PARENT, 0o700, dir_fd=root_fd)
        parent_fd = os.open(_SANDBOX_PARENT, flags, dir_fd=root_fd)
        parent_info = os.fstat(parent_fd)
        if not _shared_safely(parent_info, {os.getuid()}) or not _same_file(parent, parent_info):
            raise _ProbeFailed("sandbox_unavailable")
        for _ in range(100):
            name = f"{_SANDBOX_PREFIX}{secrets.token_hex(8)}"
            try:
                os.mkdir(name, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            sandbox = parent / name
            if not _same_file(sandbox, os.stat(name, dir_fd=parent_fd, follow_symlinks=False)):
                os.rmdir(name, dir_fd=parent_fd)
                raise _ProbeFailed("sandbox_unavailable")
            return sandbox
        raise _ProbeFailed("sandbox_unavailable")
    except (OSError, ValueError):
        raise _ProbeFailed("sandbox_unavailable") from None
    finally:
        for fd in (parent_fd, root_fd):
            if fd is not None:
                os.close(fd)


def _same_file(path: Path, info: os.stat_result) -> bool:
    """True when ``path``, its final link not followed, is the file ``info`` describes."""
    found = os.stat(path, follow_symlinks=False)
    return (found.st_dev, found.st_ino) == (info.st_dev, info.st_ino)


def _grant_owner(path: str) -> None:
    """Give the owner back read, write and search on a real directory it owns.

    Opened without following a link, so a link or a link's target is never
    changed; anything other than this user's directory is left alone.
    """
    try:
        fd = os.open(path, os.O_PATH | os.O_NOFOLLOW | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        return
    try:
        info = os.fstat(fd)
        if info.st_uid == os.getuid():
            # The descriptor's own entry: the directory opened above, not a path to it.
            os.chmod(f"/proc/self/fd/{fd}", stat.S_IMODE(info.st_mode) | stat.S_IRWXU)
    except OSError:
        pass
    finally:
        os.close(fd)


def _remove_sandbox(sandbox: Path) -> None:
    """Remove a probe sandbox, repairing directories the probe locked.

    Links inside it are removed, never followed. What cannot be removed is
    counted and logged without a value; the probe's result is unaffected.
    """
    global _sandbox_residue
    top = str(sandbox)
    repaired: set[str] = set()

    def retry(_func: Any, path: str | os.PathLike[str], exc: BaseException) -> None:
        path = os.fspath(path)
        if not isinstance(exc, PermissionError) or path in repaired:
            return
        repaired.add(path)
        if path != top:
            _grant_owner(os.path.dirname(path))
        _grant_owner(path)
        try:
            if stat.S_ISDIR(os.lstat(path).st_mode):
                shutil.rmtree(path, onexc=retry)
            else:
                os.unlink(path)
        except OSError:
            return

    with contextlib.suppress(OSError):
        shutil.rmtree(top, onexc=retry)
    if os.path.lexists(top):
        with _lock:
            _sandbox_residue += 1
        _log.warning("claude account usage: a probe sandbox could not be removed")


def probe_sandbox_residue() -> int:
    """How many probe sandboxes this process could not remove."""
    with _lock:
        return _sandbox_residue


@contextlib.contextmanager
def _probe_sandbox() -> Iterator[Path]:
    """A private (0700) directory under the fleet scratch root for one probe,
    removed when the probe ends, however it ends."""
    sandbox = _create_sandbox()
    try:
        yield sandbox
    finally:
        _remove_sandbox(sandbox)


def probe_account(label: str, *, timeout_s: float = PROBE_TIMEOUT_S) -> tuple[dict[str, Any], _Accounts]:
    """One bounded probe for one label: its row and what the row is attributed to.

    The label's directory is held open through the probe, and the binding must
    validate again afterwards to the same generation: a directory or account
    replaced in between refuses the sample, and credentials rewritten in between
    must be proven the bound account's. The sample is served under the
    validation made after the probe. Raises ``ClaudeAccountRefused`` or
    ``_ProbeFailed``.
    """
    with account_binding(label) as binding:
        codexbar = _codexbar_bin()
        if not codexbar:
            raise _ProbeFailed("missing_binary")
        started = time.time()
        with _probe_sandbox() as sandbox:
            env = child_env(binding.config_dir, sandbox=sandbox)
            raw = _run_codexbar(codexbar, env, timeout_s=timeout_s, max_bytes=MAX_OUTPUT_BYTES)
        # The held directory cannot be freed and its identity reused, so the same
        # generation means the directory and account the probe ended on are the
        # ones validated before it started.
        with account_binding(label, verified=binding.watch) as after:
            if after.generation != binding.generation:
                raise ClaudeAccountRefused("claude_account_unverified")
    try:
        payload = json.loads(raw)
    except ValueError:
        raise _ProbeFailed("bad_json") from None
    row = parse_codexbar_claude(payload)
    if row["updated"] is None:
        row["updated"] = _iso(datetime.fromtimestamp(started, UTC))
    return row, _attribute(after, payload)


def _record(
    label: str,
    row: dict[str, Any] | None,
    failure: str | None,
    *,
    accounts: _Accounts | None = None,
    forget: bool = False,
) -> None:
    with _lock:
        if row is not None:
            if accounts is None:
                raise TypeError("a sample needs its attribution")
            observed = time.time()
            measured = _timestamp(row.get("updated"))
            # The state cannot be newer than the moment it was observed.
            source_at = observed if measured is None else min(measured.timestamp(), observed)
            windows = {name: dict(row[name]) for _key, name in _WINDOWS}
            _last_good[label] = _Sample(source_at, windows, accounts)
            _last_failure.pop(label, None)
            return
        if forget:
            _last_good.pop(label, None)
        _last_failure[label] = failure or "probe_error"


def _refresh_one(label: str, timeout_s: float) -> None:
    try:
        row, accounts = probe_account(label, timeout_s=timeout_s)
    except ClaudeAccountRefused as exc:
        # The binding no longer names a usable directory: its old numbers are
        # not this label's numbers any more.
        _record(label, None, exc.code, forget=True)
    except _ProbeFailed as exc:
        _record(label, None, exc.code)
    except Exception:  # a probe defect leaves the row stale or unknown, never breaks refresh
        _record(label, None, "probe_error")
    else:
        _record(label, row, None, accounts=accounts)


def refresh_claude_account_usage(*, timeout_s: float = PROBE_TIMEOUT_S) -> None:
    """Probe every registered label in parallel. Background refresh only."""
    with ThreadPoolExecutor(max_workers=len(CLAUDE_ACCOUNT_LABELS)) as executor:
        list(executor.map(lambda label: _refresh_one(label, timeout_s), CLAUDE_ACCOUNT_LABELS))


def _ambiguous(samples: Mapping[str, _Sample]) -> bool:
    """True when the served labels cannot be attributed to distinct accounts."""
    if len(samples) < 2:
        return False
    attributions = [sample.accounts for sample in samples.values()]
    if len({accounts.named for accounts in attributions}) > 1:
        return True  # one answer named its account and another did not
    fingerprints = [accounts.fingerprints for accounts in attributions]  # each holds its proven account
    return any(
        fingerprints[i] & fingerprints[j] for i in range(len(fingerprints)) for j in range(i + 1, len(fingerprints))
    )


def _unchanged(label: str, watch: _Watch) -> bool:
    """True while every file the sample's validation read keeps its stat facts.

    The serve-time check: a few ``lstat`` calls, never an open, read or parse.
    """
    try:
        if _root_paths(label) != watch.roots:
            return False
        return all(_facts(path, directory=directory) == facts for path, directory, facts in watch.entries)
    except Exception:  # an unreadable path withholds the row, never breaks the endpoint
        return False


def _replace_sample(label: str, old: _Sample, new: _Sample | None, failure: str | None = None) -> None:
    """Re-arm or forget ``old`` unless a newer sample was recorded meanwhile."""
    with _lock:
        if _last_good.get(label) is not old:
            return
        if new is not None:
            _last_good[label] = new
            return
        del _last_good[label]
        _last_failure[label] = failure or "probe_error"


def _revalidate_one(label: str, sample: _Sample) -> None:
    """Re-arm a sample whose files changed while its binding keeps its generation; else forget it."""
    watch = sample.accounts.watch
    try:
        with account_binding(label, verified=watch) as binding:
            current = binding.watch
    except ClaudeAccountRefused as exc:
        _replace_sample(label, sample, None, exc.code)
        return
    except Exception:  # a validation defect withholds the row, never breaks the revalidation
        _replace_sample(label, sample, None, "probe_error")
        return
    if current.generation != watch.generation:
        _replace_sample(label, sample, None, "not_probed")
        return
    _replace_sample(label, sample, replace(sample, accounts=replace(sample.accounts, watch=current)))


def revalidate_claude_accounts() -> None:
    """Re-check every cached sample whose validated files changed. Background only; never probes."""
    with _lock:
        cached = dict(_last_good)
    for label, sample in cached.items():
        if not _unchanged(label, sample.accounts.watch):
            _revalidate_one(label, sample)


def _schedule_revalidation() -> None:
    """Start one background revalidation unless one is running; never waits for it."""
    global _revalidation
    with _revalidation_lock:
        if _revalidation is not None and _revalidation.is_alive():
            return
        _revalidation = threading.Thread(
            target=revalidate_claude_accounts, name="account-usage-revalidation", daemon=True
        )
        _revalidation.start()


def _unknown_row(reason: str) -> dict[str, Any]:
    return {
        **{name: dict.fromkeys(_WINDOW_FIELDS) for _key, name in _WINDOWS},
        "updated": None,
        "age_s": None,
        "stale": False,
        "status": "unknown",
        "reason": reason,
    }


def claude_accounts_snapshot(*, ttl_s: float | None = None, now: float | None = None) -> dict[str, dict[str, Any]]:
    """Rows keyed ``claude:<label>``, aged at call time; never starts a probe.

    Never opens, reads or parses a file, so it is safe on the event loop. A
    cached sample is served only while every file its validation read keeps its
    stat facts; otherwise the row is ``not_probed`` and one background
    revalidation is scheduled, after which a changed binding gives ``not_probed``
    and a refused one its refusal code.

    ``ok``: the measured state is younger than the cache TTL and no probe failed since.
    ``stale``: a last good sample that is older or followed by a failure.
    ``unknown``: no usable sample, or numbers withheld as ``account_ambiguous``.
    """
    ttl = _codexbar_cache_ttl_s() if ttl_s is None else ttl_s
    moment = time.time() if now is None else now
    with _lock:
        cached = {label: _last_good[label] for label in CLAUDE_ACCOUNT_LABELS if label in _last_good}
        failures = dict(_last_failure)
    samples = {label: sample for label, sample in cached.items() if _unchanged(label, sample.accounts.watch)}
    if len(samples) < len(cached):
        _schedule_revalidation()
    withheld = _ambiguous(samples)
    rows: dict[str, dict[str, Any]] = {}
    for label in CLAUDE_ACCOUNT_LABELS:
        sample = samples.get(label)
        failure = failures.get(label)
        if sample is None:
            rows[row_key(label)] = _unknown_row("not_probed" if label in cached else failure or "not_probed")
            continue
        if withheld:
            rows[row_key(label)] = _unknown_row(ACCOUNT_AMBIGUOUS)
            continue
        age = max(0.0, moment - sample.source_at)
        stale = failure is not None or age >= ttl
        rows[row_key(label)] = {
            **{name: dict(window) for name, window in sample.windows.items()},
            "updated": _iso(datetime.fromtimestamp(sample.source_at, UTC)),
            "age_s": round(age, 1),
            "stale": stale,
            "status": "stale" if stale else "ok",
            "reason": failure if failure is not None else ("expired" if stale else None),
        }
    return rows


def preferred_claude_account(rows: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Label with the larger projected weekly leftover; display hint only.

    ``None`` unless every registered row is ``ok`` with a known weekly leftover
    and one is strictly larger: an unknown account cannot be ranked against.
    """
    leftovers: dict[str, float] = {}
    for label in CLAUDE_ACCOUNT_LABELS:
        row = rows.get(row_key(label))
        if not isinstance(row, Mapping) or row.get("status") != "ok":
            return None
        weekly = row.get("weekly")
        leftover = _number(weekly.get("leftover_pct")) if isinstance(weekly, Mapping) else None
        if leftover is None:
            return None
        leftovers[label] = leftover
    best = max(leftovers.values())
    winners = [label for label, value in leftovers.items() if value == best]
    return winners[0] if len(winners) == 1 else None


def routing_budget_fields() -> dict[str, Any]:
    """Additive routing-budget keys, aged now: per-account rows and the balancing hint."""
    rows = claude_accounts_snapshot()
    return {"claude_accounts": rows, "preferred_claude_account": preferred_claude_account(rows)}


def _reset_for_tests() -> None:
    global _sandbox_residue
    thread = _revalidation
    if thread is not None:
        thread.join(timeout=60)
    with _lock:
        _last_good.clear()
        _last_failure.clear()
        _sandbox_residue = 0
