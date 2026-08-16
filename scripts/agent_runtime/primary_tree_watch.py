"""Mid-dispatch primary-checkout tracked-write detector (#6818).

The spawn-time guard (``runner._ensure_write_cwd_isolated``, #4444/#4446)
proves a write-capable child STARTS in an isolated dispatch worktree, but has
no visibility afterwards. #6818's recurrence showed why that matters: during
dispatch ``work-6849-projection-health`` the agy harness executed
model-supplied absolute paths that resolved to the PRIMARY checkout —
``replace_file_content`` wrote the primary's ``scripts/api/fleet_router.py``
mid-run, then the worker itself reverted it minutes later. The escape window
was invisible to every existing probe: the post-exit integrity sweep only
alerts on detachment, and the transient dirty state had self-corrected by
finalize time.

Per the #5803 design-panel conclusion ("git-layer enforcement against a
same-UID process is categorically impossible"), this module is **detection +
attribution, not prevention**:

- BASELINE: at spawn, snapshot the primary checkout's tracked-dirty path set
  (``git status --porcelain -uno``) so a human already working in the primary
  never produces a false alert.
- DETECT: while the child runs (and once after it exits), re-probe and diff.
  Any tracked path that went dirty AFTER the baseline, while a write-capable
  dispatch child is running, is recorded.
- RECORD: append a ``primary_tree_write_during_dispatch`` event to the same
  attribution JSONL the primary-integrity watchdog uses
  (``<primary>/data/telemetry/primary-integrity/events.jsonl``) with the
  agent, task id, and offending paths — enough to attribute the writer even
  when the dirty state later self-corrects.
- ENFORCE (operator-gated, default OFF): ``LU_PRIMARY_TREE_WATCH_ENFORCE=1``
  lets the runner kill the child on detection. Enabling it is an operator
  decision on #6818, not a default — untracked new files at the repo root are
  already covered by the #6866 root-entry canary, and a kill mid-write can
  strand worse states than the write itself.

Untracked files are intentionally out of scope (``-uno``): this watch is for
tracked-file writes, the probe must stay cheap enough to run inside the
runner's 1s poll loop (throttled to ``LU_PRIMARY_TREE_WATCH_INTERVAL_S``,
default 20s), and the untracked class has its own canary (#6866).

Every failure path is fail-open: a broken probe disables the watch, never the
dispatch.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

# Dual-flavor import, same rationale as runner._load_worktree_containment:
# ``scripts.*`` resolves under pytest/module runs; the delegate worker puts
# only ``scripts/`` on sys.path.
try:
    from scripts.common.git_context import sanitized_git_env
except ImportError:  # scripts/ on sys.path (stripped flavor)
    from common.git_context import sanitized_git_env  # type: ignore[no-redef]

_logger = logging.getLogger(__name__)

# Must stay equal to runner._WRITE_CAPABLE_MODES; a drift tripwire test pins
# the two sets together (tests/test_primary_tree_watch.py).
WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})

_INTERVAL_ENV = "LU_PRIMARY_TREE_WATCH_INTERVAL_S"
_ENFORCE_ENV = "LU_PRIMARY_TREE_WATCH_ENFORCE"
_DEFAULT_INTERVAL_S = 20.0
# Consecutive probe failures before the watch disables itself (fail-open
# without log spam on a persistently broken primary).
_MAX_PROBE_FAILURES = 3

EVENT_NAME = "primary_tree_write_during_dispatch"


def _interval_from_env() -> float:
    raw = os.environ.get(_INTERVAL_ENV, "").strip()
    if not raw:
        return _DEFAULT_INTERVAL_S
    try:
        return float(raw)
    except ValueError:
        return _DEFAULT_INTERVAL_S


def _load_containment():
    for candidate in ("scripts.guardrails.worktree_containment", "guardrails.worktree_containment"):
        try:
            import importlib

            return importlib.import_module(candidate)
        except ImportError:
            continue
    return None


def _tracked_dirty_paths(main_root: Path) -> set[str] | None:
    """Tracked paths currently dirty in ``main_root``; None if unprobeable.

    ``-uno`` skips untracked files entirely — cheap, and untracked pollution
    is the #6866 canary's job. Rename/copy entries carry a second NUL token
    (the source path); the destination token is sufficient for attribution.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(main_root), "status", "--porcelain=v1", "-z", "-uno"],
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_git_env(),
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    paths: set[str] = set()
    parts = proc.stdout.split("\0")
    index = 0
    while index < len(parts):
        raw = parts[index]
        index += 1
        if not raw:
            continue
        xy = raw[:2]
        path = raw[3:] if len(raw) > 3 else ""
        if path:
            paths.add(path)
        if xy[:1] in {"R", "C"} or xy[1:2] in {"R", "C"}:
            index += 1
    return paths


class PrimaryTreeWatch:
    """Watches the primary checkout for tracked writes during one dispatch."""

    def __init__(
        self,
        *,
        main_root: Path,
        baseline: set[str],
        agent_name: str,
        mode: str,
        task_id: str | None,
        worktree: Path,
        interval_s: float,
        event_sink: Callable[..., None] | None,
        state_dir: Path | None = None,
    ) -> None:
        self.main_root = main_root
        self.baseline = baseline
        self.agent_name = agent_name
        self.mode = mode
        self.task_id = task_id
        self.worktree = worktree
        self.interval_s = interval_s
        self.event_sink = event_sink
        # Same location the primary-integrity watchdog records to, so one
        # events.jsonl carries the full escape-class forensic trail.
        self.state_dir = state_dir or (main_root / "data" / "telemetry" / "primary-integrity")
        self._reported: set[str] = set()
        self._next_check = time.monotonic() + interval_s
        self._probe_failures = 0

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def start(
        cls,
        *,
        cwd: Path,
        mode: str,
        agent_name: str,
        task_id: str | None,
        event_sink: Callable[..., None] | None,
        repo_tree: Path,
        interval_s: float | None = None,
        state_dir: Path | None = None,
    ) -> PrimaryTreeWatch | None:
        """Build a watch for one spawn, or None when not applicable.

        Applicable only to write-capable spawns whose cwd is a dispatch
        worktree of ``repo_tree``'s repository. Never raises: any resolution
        or probe failure returns None (fail-open — the watch is a tripwire,
        not a gate; the spawn-time guard already did the fail-closed part).
        """
        try:
            if mode not in WRITE_CAPABLE_MODES:
                return None
            interval = _interval_from_env() if interval_s is None else interval_s
            if interval <= 0:
                return None
            wc = _load_containment()
            if wc is None:
                return None
            resolved = wc.canonicalize(cwd)
            # Same cheap pre-filter as the spawn-time guard: only a cwd inside
            # this checkout's own tree can be one of its dispatch worktrees.
            if not resolved.is_relative_to(wc.canonicalize(repo_tree)):
                return None
            if wc.classify_repo_path(resolved, cwd=resolved) != "dispatch_worktree":
                return None
            main_root = wc.resolve_main_root(resolved)
            baseline = _tracked_dirty_paths(main_root)
            if baseline is None:
                return None
            return cls(
                main_root=main_root,
                baseline=baseline,
                agent_name=agent_name,
                mode=mode,
                task_id=task_id,
                worktree=resolved,
                interval_s=interval,
                event_sink=event_sink,
                state_dir=state_dir,
            )
        except Exception as exc:
            _logger.warning(
                "primary-tree watch unavailable for %s (%s: %s) — dispatch continues unwatched",
                agent_name,
                type(exc).__name__,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # probing
    # ------------------------------------------------------------------

    @property
    def enforce(self) -> bool:
        """Operator-gated kill switch (#6818 decision list). Default OFF."""
        return os.environ.get(_ENFORCE_ENV, "").strip() == "1"

    def maybe_check(self, *, force: bool = False) -> list[str]:
        """Probe (throttled) and return newly-escaped tracked paths.

        Returns only paths not in the spawn baseline and not yet reported this
        dispatch, so each escape is recorded exactly once. Never raises.
        """
        try:
            now = time.monotonic()
            if not force and now < self._next_check:
                return []
            self._next_check = now + self.interval_s
            if self._probe_failures >= _MAX_PROBE_FAILURES:
                return []
            current = _tracked_dirty_paths(self.main_root)
            if current is None:
                self._probe_failures += 1
                if self._probe_failures == _MAX_PROBE_FAILURES:
                    _logger.warning(
                        "primary-tree watch: %d consecutive probe failures on %s — watch disabled for this dispatch",
                        self._probe_failures,
                        self.main_root,
                    )
                return []
            self._probe_failures = 0
            new_paths = sorted(current - self.baseline - self._reported)
            if not new_paths:
                return []
            self._reported.update(new_paths)
            self._record(new_paths)
            return new_paths
        except Exception as exc:  # pragma: no cover - defensive fail-open
            _logger.warning(
                "primary-tree watch check failed (%s: %s)", type(exc).__name__, exc
            )
            return []

    def final_check(self) -> list[str]:
        """One unthrottled probe after the child exits (last-interval writes)."""
        return self.maybe_check(force=True)

    # ------------------------------------------------------------------
    # recording
    # ------------------------------------------------------------------

    def _record(self, new_paths: list[str]) -> None:
        fields = {
            "agent": self.agent_name,
            "task_id": self.task_id,
            "mode": self.mode,
            "worktree": str(self.worktree),
            "main_root": str(self.main_root),
            "paths": new_paths,
            "baseline_dirty_count": len(self.baseline),
            "enforce": self.enforce,
        }
        _logger.error(
            "PRIMARY-TREE WRITE DURING DISPATCH: agent=%s task=%s wrote tracked "
            "primary path(s) %s while its worktree is %s — recorded to %s (#6818)",
            self.agent_name,
            self.task_id,
            ", ".join(new_paths),
            self.worktree,
            self.state_dir / "events.jsonl",
        )
        payload = {"ts": datetime.now(UTC).isoformat(), "event": EVENT_NAME, **fields}
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            with open(self.state_dir / "events.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            _logger.warning(
                "primary-tree watch: failed to append event (%s: %s)",
                type(exc).__name__,
                exc,
            )
        if self.event_sink is not None:
            with contextlib.suppress(Exception):
                self.event_sink(EVENT_NAME, **fields)
