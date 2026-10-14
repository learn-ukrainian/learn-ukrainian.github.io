"""Per-account Claude usage rows for the routing budget (#10630).

One bounded CodexBar probe per registered Claude account label, run only by
the background usage refresh. ``claude_accounts_snapshot`` reads the cache and
never starts a probe. Rows carry numbers and freshness, never identity: no
account id, email, organization or directory appears in any row.

Label ``a`` is the host's default Claude directory. Every other label takes its
directory from the private binding read by ``load_claude_account_binding``; a
missing or refused binding makes that row unknown, never an endpoint error.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import selectors
import signal
import subprocess
import threading
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.attempt_boundary import (
    CLAUDE_ACCOUNT_LABELS,
    DEFAULT_CLAUDE_ACCOUNT,
    ClaudeAccountRefused,
    _open_claude_directory,
    load_claude_account_binding,
)
from scripts.api.subscription_usage import _codexbar_bin, _codexbar_cache_ttl_s

PROBE_TIMEOUT_S = 60.0
MAX_OUTPUT_BYTES = 1024 * 1024
_SUMMARY_MAX_CHARS = 200
# The child gets these names from the API process and nothing else. Credential
# variables (ANTHROPIC_*, CLAUDE_CODE_OAUTH_TOKEN, ...) never reach it, so the
# probe reads only the selected label's Claude directory.
_CHILD_ENV_NAMES = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
    "TMPDIR",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
)
_WINDOWS = (("primary", "session5h"), ("secondary", "weekly"))
_WINDOW_FIELDS = ("left_pct", "resets_at", "pace", "pace_delta_pct", "leftover_pct")

_lock = threading.Lock()
# label -> (monotonic observation time, row numbers without freshness fields)
_last_good: dict[str, tuple[float, dict[str, Any]]] = {}
# label -> failure code of the newest probe; absent after a success
_last_failure: dict[str, str] = {}


class _ProbeFailed(Exception):
    """A probe failure; the code names no value or location."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def row_key(label: str) -> str:
    return f"claude:{label}"


def account_config_dir(label: str) -> Path:
    """The Claude directory a label's probe reads.

    Raises ``ClaudeAccountRefused`` for a missing, invalid or unsafe binding,
    or one that names the default directory (that would count one account twice).
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
        return binding.config_dir
    if (selected.st_dev, selected.st_ino) == (info.st_dev, info.st_ino):
        raise ClaudeAccountRefused("claude_account_binding_is_default")
    return binding.config_dir


def child_env(config_dir: Path, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Minimal probe environment: the allowlisted names plus ``CLAUDE_CONFIG_DIR``."""
    env = os.environ if environ is None else environ
    child = {name: env[name] for name in _CHILD_ENV_NAMES if env.get(name)}
    child["CLAUDE_CONFIG_DIR"] = str(config_dir)
    return child


def _run_codexbar(codexbar: str, env: dict[str, str], *, timeout_s: float, max_bytes: int) -> bytes:
    """Run the fixed Claude usage query without a shell, outside the repository,
    under a hard deadline and output cap.

    The child gets its own process group, so a timeout or oversized output kills
    any helper it started as well.
    """
    try:
        proc = subprocess.Popen(
            [codexbar, "usage", "--json", "--provider", "claude"],
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
    reaped = False
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
        try:
            returncode = proc.wait(timeout=max(deadline - time.monotonic(), 0.0))
        except subprocess.TimeoutExpired:
            raise _ProbeFailed("timeout") from None
        reaped = True
    finally:
        selector.close()
        if not reaped:
            # The leader is running or an unreaped zombie, so its group id
            # cannot have been reused yet.
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        proc.stdout.close()
    if returncode != 0:
        raise _ProbeFailed("exit_nonzero")
    return b"".join(chunks)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _text(value: Any, limit: int = _SUMMARY_MAX_CHARS) -> str | None:
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        return None
    return value[:limit]


def projected_leftover_pct(used: float | None, expected: float | None) -> int | None:
    """Weekly share left at reset if the burn so far continues; 0 = runs out early.

    ``expected`` is the elapsed share of the window, so ``used / expected`` is the
    projected use. Unknown when either value is missing or ``expected`` is not
    positive.
    """
    if used is None or expected is None or expected <= 0:
        return None
    return max(0, round(100 - used * 100 / expected))


def _window_row(usage_window: Any, pace_window: Any) -> dict[str, Any]:
    window = usage_window if isinstance(usage_window, dict) else {}
    pace = pace_window if isinstance(pace_window, dict) else {}
    used = _number(window.get("usedPercent"))
    return {
        "left_pct": None if used is None else 100 - used,
        "resets_at": _text(window.get("resetsAt"), 64),
        "pace": _text(pace.get("summary")),
        "pace_delta_pct": _number(pace.get("deltaPercent")),
        "leftover_pct": projected_leftover_pct(used, _number(pace.get("expectedUsedPercent"))),
    }


def parse_codexbar_claude(payload: Any) -> dict[str, Any]:
    """Numbers from ``codexbar usage --json --provider claude``; identity fields are dropped."""
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
    usage = item.get("usage")
    if not isinstance(usage, dict):
        raise _ProbeFailed("no_usage")
    pace = item.get("pace") if isinstance(item.get("pace"), dict) else {}
    row: dict[str, Any] = {name: _window_row(usage.get(key), pace.get(key)) for key, name in _WINDOWS}
    if row["session5h"]["left_pct"] is None and row["weekly"]["left_pct"] is None:
        raise _ProbeFailed("no_usage")
    row["updated"] = _text(usage.get("updatedAt"), 64)
    return row


def probe_account(label: str, *, timeout_s: float = PROBE_TIMEOUT_S) -> dict[str, Any]:
    """One bounded probe for one label; raises ``ClaudeAccountRefused`` or ``_ProbeFailed``."""
    config_dir = account_config_dir(label)
    codexbar = _codexbar_bin()
    if not codexbar:
        raise _ProbeFailed("missing_binary")
    raw = _run_codexbar(codexbar, child_env(config_dir), timeout_s=timeout_s, max_bytes=MAX_OUTPUT_BYTES)
    try:
        payload = json.loads(raw)
    except ValueError:
        raise _ProbeFailed("bad_json") from None
    row = parse_codexbar_claude(payload)
    if row["updated"] is None:
        row["updated"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return row


def _record(label: str, row: dict[str, Any] | None, failure: str | None, *, forget: bool = False) -> None:
    with _lock:
        if row is not None:
            _last_good[label] = (time.monotonic(), row)
            _last_failure.pop(label, None)
            return
        if forget:
            _last_good.pop(label, None)
        _last_failure[label] = failure or "unavailable"


def _refresh_one(label: str, timeout_s: float) -> None:
    try:
        row = probe_account(label, timeout_s=timeout_s)
    except ClaudeAccountRefused as exc:
        # The binding no longer names a usable directory: its old numbers are
        # not this label's numbers any more.
        _record(label, None, exc.code, forget=True)
    except _ProbeFailed as exc:
        _record(label, None, exc.code)
    except Exception:  # a probe defect leaves the row stale or unknown, never breaks refresh
        _record(label, None, "probe_error")
    else:
        _record(label, row, None)


def refresh_claude_account_usage(*, timeout_s: float = PROBE_TIMEOUT_S) -> None:
    """Probe every registered label in parallel. Background refresh only."""
    with ThreadPoolExecutor(max_workers=len(CLAUDE_ACCOUNT_LABELS)) as executor:
        list(executor.map(lambda label: _refresh_one(label, timeout_s), CLAUDE_ACCOUNT_LABELS))


def _unknown_windows() -> dict[str, dict[str, Any]]:
    return {name: dict.fromkeys(_WINDOW_FIELDS) for _key, name in _WINDOWS}


def claude_accounts_snapshot(*, ttl_s: float | None = None) -> dict[str, dict[str, Any]]:
    """Cached rows keyed ``claude:<label>``; never starts a probe.

    ``ok``: a sample within the cache TTL and no failed probe since.
    ``stale``: a last good sample that is older or followed by a failure.
    ``unknown``: no usable sample.
    """
    ttl = _codexbar_cache_ttl_s() if ttl_s is None else ttl_s
    now = time.monotonic()
    rows: dict[str, dict[str, Any]] = {}
    with _lock:
        for label in CLAUDE_ACCOUNT_LABELS:
            failure = _last_failure.get(label)
            good = _last_good.get(label)
            if good is None:
                rows[row_key(label)] = {
                    **_unknown_windows(),
                    "updated": None,
                    "age_s": None,
                    "stale": False,
                    "status": "unknown",
                    "reason": failure or "not_probed",
                }
                continue
            observed, sample = good
            age = now - observed
            stale = failure is not None or age >= ttl
            rows[row_key(label)] = {
                "session5h": dict(sample["session5h"]),
                "weekly": dict(sample["weekly"]),
                "updated": sample["updated"],
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
    """Additive routing-budget keys: per-account rows and the balancing hint."""
    rows = claude_accounts_snapshot()
    return {"claude_accounts": rows, "preferred_claude_account": preferred_claude_account(rows)}


def _reset_for_tests() -> None:
    with _lock:
        _last_good.clear()
        _last_failure.clear()
