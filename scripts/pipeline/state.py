"""Pipeline v5 state management.

Handles loading, saving, and migrating pipeline state files.
State file: state.json (plain phase keys, mode: "v5").
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict

logger = logging.getLogger(__name__)


class PhaseExecutor(TypedDict):
    """Provenance info for the agent/script that executed a pipeline phase.

    Attributes:
        type: "llm" | "script" | "deterministic" (always required)
        agent: LLM agent name (e.g. "gemini", "claude") — for type="llm"
        model: Exact model ID — for type="llm"
        name: Script/component name — for type="script" | "deterministic"
    """

    type: str                    # "llm", "script", or "deterministic"
    agent: NotRequired[str]      # e.g. "gemini", "claude"
    model: NotRequired[str]      # e.g. "gemini-3-flash-preview", "claude-opus-4-6"
    name: NotRequired[str]       # e.g. "vesum_sandbox", "mdx_generator"


def executor_llm(agent: str, model: str) -> PhaseExecutor:
    """Create an LLM executor dict."""
    return PhaseExecutor(type="llm", agent=agent, model=model)


def executor_script(name: str) -> PhaseExecutor:
    """Create a script executor dict."""
    return PhaseExecutor(type="script", name=name)


def executor_deterministic(name: str) -> PhaseExecutor:
    """Create a deterministic executor dict."""
    return PhaseExecutor(type="deterministic", name=name)


def detect_self_review(state: dict) -> bool:
    """Check if the same LLM agent did both content and review phases."""
    phases = state.get("phases", {})
    content_exec = phases.get("content", {}).get("executor", {})
    review_exec = phases.get("review", {}).get("executor", {})
    if not content_exec or not review_exec:
        return False
    if content_exec.get("type") != "llm" or review_exec.get("type") != "llm":
        return False
    return content_exec.get("agent") == review_exec.get("agent")

# Late imports to avoid circular dependency
_pipeline_lib = None


def _get_pipeline_lib():
    global _pipeline_lib
    if _pipeline_lib is None:
        import pipeline_lib as _pl
        _pipeline_lib = _pl
    return _pipeline_lib


def _state_file(ctx) -> Path:
    return ctx.orch_dir / "state.json"


def load_state(ctx) -> dict:
    """Load v5 state with fallback: state.json -> state-v5.json -> state-v4.json -> fresh.

    v3/v2 states are ignored -- those modules start fresh in v5.
    """
    pl = _get_pipeline_lib()

    # 1. state.json -- authoritative
    sf = _state_file(ctx)
    if sf.exists():
        try:
            data = json.loads(sf.read_text("utf-8"))
            if data.get("mode") == "v5":
                return data
            legacy_backup = sf.with_suffix(".legacy.json")
            sf.rename(legacy_backup)
            logger.debug("state.json mode=%s (not v5) -- moved to %s",
                         data.get("mode"), legacy_backup.name)
        except Exception as e:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = sf.with_suffix(f".corrupted.{ts}.json")
            sf.rename(backup)
            logger.warning(
                "state.json corrupted for %s/%s -- backed up to %s, resetting. Error: %s",
                ctx.track, ctx.slug, backup.name, e,
            )

    # 2. state-v5.json -- migrate (rename to state.json)
    sf_v5_legacy = ctx.orch_dir / "state-v5.json"
    if sf_v5_legacy.exists():
        try:
            data = json.loads(sf_v5_legacy.read_text("utf-8"))
            sf_v5_legacy.unlink()
            pl.log("  State migration: state-v5.json -> state.json (old file removed)")
            return data
        except Exception as e:
            logger.warning("state-v5.json unreadable for %s/%s: %s -- trying v4",
                           ctx.track, ctx.slug, e)

    # 3. state-v4.json -- migrate (strip "v4-" prefixes from phase keys)
    sf_v4 = ctx.orch_dir / "state-v4.json"
    if sf_v4.exists():
        try:
            v4_data = json.loads(sf_v4.read_text("utf-8"))
            return _migrate_v4_to_v5(v4_data, ctx)
        except Exception as e:
            logger.warning("state-v4.json unreadable for %s/%s: %s -- starting fresh",
                           ctx.track, ctx.slug, e)

    # 4. Anything else -- fresh state
    return _fresh_state(ctx)


def _fresh_state(ctx) -> dict:
    return {"track": ctx.track, "slug": ctx.slug, "mode": "v5", "phases": {}}


def _migrate_v4_to_v5(v4_data: dict, ctx) -> dict:
    """Strip 'v4-' prefixes from phase keys to produce v5 state."""
    pl = _get_pipeline_lib()
    v5_state = {
        "track": v4_data.get("track", ctx.track),
        "slug": v4_data.get("slug", ctx.slug),
        "mode": "v5",
        "phases": {},
    }
    v4_phases = v4_data.get("phases", {})
    for key, value in v4_phases.items():
        clean_key = key[3:] if key.startswith("v4-") else key
        v5_state["phases"][clean_key] = value

    n_migrated = len(v5_state["phases"])
    if n_migrated > 0:
        pl.log(f"  State migration: v4->v5 -- migrated {n_migrated} phase(s)")
    return v5_state


def save_state(ctx, state: dict) -> None:
    """Atomically write state.json."""
    sf = _state_file(ctx)
    sf.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=sf.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(sf)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def is_complete(state: dict, phase_id: str) -> bool:
    """Check if a phase is marked complete in v5 state."""
    info = state.get("phases", {}).get(phase_id, {})
    return info.get("status") == "complete"


def _mark_phase(state: dict, phase_id: str, ctx, status: str, **extra: Any) -> None:
    """Mark a phase status in v5 state (thread-safe via file lock)."""
    pl = _get_pipeline_lib()
    lock = pl._state_lock or pl.FileLock(str(_state_file(ctx)) + ".lock")
    with lock:
        phases = state.setdefault("phases", {})
        phases[phase_id] = {"status": status, "ts": pl._now_iso(), **extra}
        save_state(ctx, state)


def mark_complete(state: dict, phase_id: str, ctx, **extra: Any) -> None:
    """Mark a phase as complete in v5 state."""
    _mark_phase(state, phase_id, ctx, "complete", **extra)


def mark_failed(state: dict, phase_id: str, ctx, **extra: Any) -> None:
    """Mark a phase as failed in v5 state."""
    _mark_phase(state, phase_id, ctx, "failed", **extra)
