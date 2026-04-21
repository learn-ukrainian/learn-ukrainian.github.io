"""Sticky API cooldown for the Gemini adapter (#1384 Phase 1).

When the Gemini API returns a 429 / quota-exceeded response, we set a
timestamp on disk. For the next ``DEFAULT_COOLDOWN_S`` seconds (1h), any
caller in ``auto`` auth mode resolves to subscription instead of API —
without sending any probe calls to Gemini. Cooldown is driven ONLY by
real rate-limit responses, never by a liveness check, because the Gemini
API has a small daily budget (~150 calls) that we refuse to waste.

Design choices:

- **One cooldown, not per-model.** A 429 on any model is treated as a
  signal that the whole API key is near-budget. The simpler model beats
  per-model accounting for a daily-limit-bounded key.
- **File-based state, not in-process.** Multiple scripts hit the same
  key (bridge, v6_build, wiki compile). A 429 in one must immediately
  steer the others. File atime/mtime is enough — no DB needed.
- **Project-local path.** State lives under ``batch_state/`` so it
  moves with the checkout and doesn't need a separate cleanup step.
- **Clock is time.time() not monotonic.** Cooldown spans process
  lifetimes; we need a wall clock.

No network calls, no subprocess, no imports outside stdlib. Safe to
import from any adapter during ``build_invocation``.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from pathlib import Path

#: Default cooldown window after a 429. 1h matches Gemini API's typical
#: per-minute recovery profile and is long enough to batch many wiki
#: articles under subscription without flapping, short enough that a
#: transient 429 doesn't lock out API for the rest of the day.
DEFAULT_COOLDOWN_S: int = 3600

#: Project-local state file. Resolved relative to the repo root (the
#: parent of ``scripts/``), which keeps multiple checkouts isolated.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_PATH = _REPO_ROOT / "batch_state" / "gemini_api_cooldown.json"

#: Env var override for the state path. Primarily for tests — prod code
#: uses the default. Exposing it as an env var (not just a function arg)
#: means subprocess-spawned adapters inherit the override automatically.
_COOLDOWN_PATH_ENV = "LU_GEMINI_COOLDOWN_PATH"


def _state_path() -> Path:
    """Resolve the current cooldown state file path."""
    override = os.environ.get(_COOLDOWN_PATH_ENV)
    if override:
        return Path(override)
    return _DEFAULT_STATE_PATH


def set_api_cooldown(duration_s: int = DEFAULT_COOLDOWN_S) -> float:
    """Mark the API as cooling down until ``now + duration_s``.

    Returns the expiry timestamp (wall clock, seconds since epoch) so
    callers can log it. Idempotent: calling twice extends the cooldown
    to whichever is later.
    """
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    new_expires_at = now + max(0, duration_s)

    # If cooldown is already set further in the future, keep that.
    # Prevents a later 429 with a shorter duration from shortening the
    # window.
    existing = _read_expires_at(path)
    expires_at = max(new_expires_at, existing or 0.0)

    payload = {
        "expires_at": expires_at,
        "set_at": now,
        "duration_s": duration_s,
        "reason": "gemini-api-429",
    }
    # Atomic write: write to temp, rename. Avoids readers seeing a
    # partial file under concurrent writes.
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), "utf-8")
    os.replace(tmp, path)
    return expires_at


def clear_api_cooldown() -> None:
    """Remove the cooldown state file. Idempotent."""
    with contextlib.suppress(FileNotFoundError):
        _state_path().unlink()


def is_api_cooldown_active(now: float | None = None) -> bool:
    """Return True iff the API is currently in cooldown.

    ``now`` is injectable for tests; production code leaves it as None
    to use the real wall clock.
    """
    expires_at = _read_expires_at(_state_path())
    if expires_at is None:
        return False
    current = time.time() if now is None else now
    return current < expires_at


def cooldown_remaining_s(now: float | None = None) -> int:
    """Return seconds remaining on cooldown, or 0 if inactive."""
    expires_at = _read_expires_at(_state_path())
    if expires_at is None:
        return 0
    current = time.time() if now is None else now
    return max(0, int(expires_at - current))


def _read_expires_at(path: Path) -> float | None:
    """Read the cooldown expiry. Returns None if absent or unreadable.

    Corrupt / unparseable files are treated as absent — better to
    attempt one API call and learn the real state than to wedge on a
    bad state file.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("expires_at")
    if isinstance(value, (int, float)):
        return float(value)
    return None
