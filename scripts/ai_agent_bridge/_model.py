"""Model availability checking."""

import os
import subprocess
from pathlib import Path

from agent_runtime.adapters.agy import (
    _AGY_MODEL_BY_NORMALIZED,
    AgyAdapter,
    _normalize_model,
)

from ._config import _MODEL_CACHE, _MODEL_CACHE_TTL, _PARENT_ENV, AGY_CLI

GROK_BUILD_DEFAULT_MODEL = "grok-4.5"
GROK_BUILD_DEFAULT_EFFORT = "high"

DEFAULT_CHECK_MODEL_TIMEOUT = int(os.environ.get("AB_CHECK_MODEL_TIMEOUT", "90"))

_AGY_ADAPTER = AgyAdapter()
_REPO_ROOT = Path(__file__).parent.parent.parent


def _resolve_requested_agy_model(model: str) -> str | None:
    """Map *model* to an AGY display label without default-model fallback."""
    return _AGY_MODEL_BY_NORMALIZED.get(_normalize_model(model))


def _build_agy_probe_plan(model: str, task_id: str = "check-model"):
    """Build an agy print-mode probe for *model* (slug or display name)."""
    if not _resolve_requested_agy_model(model):
        return None
    return _AGY_ADAPTER.build_invocation(
        prompt="Reply with exactly: MODEL_OK",
        mode="danger",
        cwd=_REPO_ROOT,
        model=model,
        task_id=task_id,
        session_id=None,
        tool_config=None,
    )


def check_model(model: str, timeout: int | None = None, force: bool = False) -> bool:
    """Check if an AGY model is available by sending a trivial prompt.

    Results are cached for 1 hour to avoid burning API quota.
    Returns True if the model responds, False if unavailable or errors.
    """
    import time as _time

    if timeout is None:
        timeout = DEFAULT_CHECK_MODEL_TIMEOUT

    # Check cache first (saves an API call)
    if not force and model in _MODEL_CACHE:
        available, cached_at = _MODEL_CACHE[model]
        age = _time.time() - cached_at
        if age < _MODEL_CACHE_TTL:
            status = "available" if available else "NOT available"
            print(f"🔍 Model '{model}': {status} (cached {int(age)}s ago)")
            return available

    plan = _build_agy_probe_plan(model)
    if plan is None:
        print(
            f"❌ Model '{model}' is not a recognized AGY model. "
            "Run `agy models` for supported display labels."
        )
        _MODEL_CACHE[model] = (False, _time.time())
        return False

    env = dict(_PARENT_ENV)
    env.update(plan.env_overrides)

    try:
        result = subprocess.run(
            plan.cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_REPO_ROOT),
            env=env,
        )
        if result.returncode == 0 and "MODEL_OK" in result.stdout:
            _MODEL_CACHE[model] = (True, _time.time())
            return True
        _handle_model_check_failure(result, model, _time)
        _MODEL_CACHE[model] = (False, _time.time())
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠️  Model '{model}' check timed out after {timeout}s.")
        _MODEL_CACHE[model] = (False, _time.time())
        return False
    except FileNotFoundError:
        print(f"❌ AGY CLI not found at: {AGY_CLI}")
        return False


def _handle_model_check_failure(result, model: str, _time):
    """Print appropriate error message for model check failure."""
    stderr = result.stderr or ""
    if "not found" in stderr.lower() or "not available" in stderr.lower() or "invalid model" in stderr.lower():
        print(f"❌ Model '{model}' is not available on this account.")
    elif "exhausted" in stderr.lower() or "429" in stderr or "quota" in stderr.lower():
        print(f"⚠️  Model '{model}' exists but quota is exhausted.")
    else:
        print(f"⚠️  Model '{model}' check failed (exit {result.returncode}): {stderr[:200]}")


def _detect_model_error(stderr: str, model: str) -> str | None:
    """Detect model-specific errors from AGY stderr.

    Returns a user-friendly error message, or None if not a model error.
    """
    s = stderr.lower()
    if "not found" in s or "not available" in s or "invalid model" in s:
        _MODEL_CACHE[model] = (False, __import__("time").time())
        return f"Model '{model}' is not available on this account. Switch accounts or use a different model."
    return None
