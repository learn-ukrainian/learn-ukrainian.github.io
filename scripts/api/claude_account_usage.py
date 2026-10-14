"""Per-account Claude usage rows for the routing budget (#10630).

One bounded CodexBar probe per registered Claude account label, run only by
the background usage refresh. ``claude_accounts_snapshot`` reads the cache and
never starts a probe. Rows carry numbers and freshness, never identity: no
account id, email, organization or directory appears in any row.

Label ``a`` is the host's default Claude directory. Every other label takes its
directory from the private binding read by ``load_claude_account_binding``; a
missing or refused binding makes that row unknown, never an endpoint error.

The selected directory is the only thing that selects the account. The query
pins CodexBar's Claude source to OAuth, which reads only that directory's
credentials, and the child runs with a fresh private home, cache and data
location and no CodexBar configuration, so no shared configuration, token
account or cache can substitute another account. Each sample also keeps
private fingerprints of the account it measured; they are never published.
When two labels measure one account, or a measured label cannot be told
apart from another, every measured row is withheld as ``account_ambiguous``.

Freshness is computed when a row is served, from the measured state's
timestamp, never frozen into a stored payload.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import selectors
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.attempt_boundary import (
    CLAUDE_ACCOUNT_LABELS,
    CLAUDE_ACCOUNT_REFUSAL_CODES,
    DEFAULT_CLAUDE_ACCOUNT,
    ClaudeAccountRefused,
    _claude_config_account_uuid,
    _open_claude_directory,
    load_claude_account_binding,
)
from scripts.api.subscription_usage import _codexbar_bin, _codexbar_cache_ttl_s, _parse_resets_at_any

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
        "probe_error",
    }
)
# Every ``reason`` a published row may carry.
ROW_REASON_CODES = PROBE_FAILURE_CODES | CLAUDE_ACCOUNT_REFUSAL_CODES | {"not_probed", "expired", ACCOUNT_AMBIGUOUS}


@dataclass(frozen=True)
class _Sample:
    """A label's last good measurement."""

    source_at: float  # epoch seconds of the measured state
    windows: dict[str, dict[str, Any]]
    # Private fingerprints of the measured account; never published or logged.
    accounts: frozenset[bytes] = field(default=frozenset(), repr=False)


_lock = threading.Lock()
_last_good: dict[str, _Sample] = {}
# label -> failure code of the newest probe; absent after a success
_last_failure: dict[str, str] = {}


class _ProbeFailed(Exception):
    """A probe failure; the code names no value or location."""

    def __init__(self, code: str):
        if code not in PROBE_FAILURE_CODES:
            raise AssertionError("unregistered probe failure code")
        super().__init__(code)
        self.code = code


def row_key(label: str) -> str:
    return f"claude:{label}"


def account_config_dir(label: str) -> Path:
    """The Claude directory a label's probe reads.

    Raises ``ClaudeAccountRefused`` for a missing, invalid or unsafe binding, one
    that names the default directory (that would count one account twice), or one
    whose directory does not hold the bound account.
    """
    default = Path.home() / ".claude"
    if label == DEFAULT_CLAUDE_ACCOUNT:
        return default
    binding = load_claude_account_binding(label)
    with _open_claude_directory(binding.config_dir) as directory:
        selected = os.fstat(directory)
        try:
            info = default.stat()
        except OSError:
            info = None
        if info is not None and (selected.st_dev, selected.st_ino) == (info.st_dev, info.st_ino):
            raise ClaudeAccountRefused("claude_account_binding_is_default")
        if _claude_config_account_uuid(Path(".claude.json"), dir_fd=directory) != binding.account_uuid:
            raise ClaudeAccountRefused("claude_account_unverified")
    return binding.config_dir


def _login_account(label: str, config_dir: Path) -> str | None:
    """The account Claude Code recorded at login for the directory, if readable.

    The default directory's record is the host's global config beside it; a
    selected directory keeps its own.
    """
    record = Path.home() / ".claude.json" if label == DEFAULT_CLAUDE_ACCOUNT else config_dir / ".claude.json"
    try:
        return _claude_config_account_uuid(record)
    except ClaudeAccountRefused:
        return None


def _fingerprint(kind: str, value: Any) -> bytes | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return hashlib.sha256(f"{kind}\0{value.strip().lower()}".encode()).digest()


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


def returned_account_fingerprints(payload: Any) -> frozenset[bytes]:
    """Private fingerprints of any account identity CodexBar returned."""
    usage = _claude_item(payload).get("usage")
    usage = usage if isinstance(usage, dict) else {}
    identity = usage.get("identity") if isinstance(usage.get("identity"), dict) else {}
    found = {
        _fingerprint("account_id", identity.get("accountID")),
        _fingerprint("email", identity.get("accountEmail")),
        _fingerprint("email", usage.get("accountEmail")),
    }
    return frozenset(digest for digest in found if digest is not None)


def probe_account(label: str, *, timeout_s: float = PROBE_TIMEOUT_S) -> tuple[dict[str, Any], frozenset[bytes]]:
    """One bounded probe for one label: its row and the measured account's private fingerprints.

    Raises ``ClaudeAccountRefused`` or ``_ProbeFailed``.
    """
    config_dir = account_config_dir(label)
    codexbar = _codexbar_bin()
    if not codexbar:
        raise _ProbeFailed("missing_binary")
    login = _fingerprint("login", _login_account(label, config_dir))
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="lu-claude-usage-", ignore_cleanup_errors=True) as sandbox:
        raw = _run_codexbar(
            codexbar, child_env(config_dir, sandbox=Path(sandbox)), timeout_s=timeout_s, max_bytes=MAX_OUTPUT_BYTES
        )
    try:
        payload = json.loads(raw)
    except ValueError:
        raise _ProbeFailed("bad_json") from None
    row = parse_codexbar_claude(payload)
    if row["updated"] is None:
        row["updated"] = _iso(datetime.fromtimestamp(started, UTC))
    accounts = returned_account_fingerprints(payload) | ({login} if login is not None else set())
    return row, frozenset(accounts)


def _record(
    label: str,
    row: dict[str, Any] | None,
    failure: str | None,
    *,
    accounts: frozenset[bytes] = frozenset(),
    forget: bool = False,
) -> None:
    with _lock:
        if row is not None:
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
    """True when the measured labels cannot be attributed to distinct accounts."""
    if len(samples) < 2:
        return False
    fingerprints = [sample.accounts for sample in samples.values()]
    if not all(fingerprints):
        return True
    return any(
        fingerprints[i] & fingerprints[j] for i in range(len(fingerprints)) for j in range(i + 1, len(fingerprints))
    )


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

    ``ok``: the measured state is younger than the cache TTL and no probe failed since.
    ``stale``: a last good sample that is older or followed by a failure.
    ``unknown``: no usable sample, or numbers withheld as ``account_ambiguous``.
    """
    ttl = _codexbar_cache_ttl_s() if ttl_s is None else ttl_s
    moment = time.time() if now is None else now
    with _lock:
        samples = {label: _last_good[label] for label in CLAUDE_ACCOUNT_LABELS if label in _last_good}
        failures = dict(_last_failure)
    withheld = _ambiguous(samples)
    rows: dict[str, dict[str, Any]] = {}
    for label in CLAUDE_ACCOUNT_LABELS:
        sample = samples.get(label)
        failure = failures.get(label)
        if sample is None or withheld:
            rows[row_key(label)] = _unknown_row(ACCOUNT_AMBIGUOUS if sample is not None else failure or "not_probed")
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
    with _lock:
        _last_good.clear()
        _last_failure.clear()
