"""Legacy worker exports derived from the child task, after credential admission (B6)."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.agent_runtime.attribution import resolve_invocation_attribution
from scripts.agent_runtime.env_sanitize import without_unneeded_secrets
from scripts.common.repo_root import resolve_repo_root
from scripts.dispatcher.types import TaskSpec
from scripts.orchestration.worktree_paths import normalize_task_id as _normalize_task_id

_REPO_ROOT = resolve_repo_root(Path(__file__), 2)

def _x_agent_task_id(agent: str, task_id: str) -> str:
    normalized = _normalize_task_id(agent, task_id)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip(".-")
    return safe or "task"


def _x_agent_trailer(agent: str, task_id: str) -> str:
    return f"X-Agent: {agent}/{_x_agent_task_id(agent, task_id)}"


def _worker_tool_cache_env(runtime_tmp_root: Path) -> dict[str, str]:
    """Point tool caches at the task scratch lease instead of the worktree (#10777).

    The lease is reaped when the worker exits; a cache in the worktree stays
    until the tree is removed. Measured 2026-10-16 on old dispatch trees:
    ``__pycache__`` 61-126MB and ``.mypy_cache`` 33MB per tree. The bytecode
    prefix also holds compiled interpreter libraries for the task, so they
    are compiled once per lease. ``.ruff_cache`` is about 1MB.

    Left in the worktree: ``.pytest_cache`` (at most 2MB) has no environment
    override, and setting it through ``PYTEST_ADDOPTS`` would reach the
    nested pytest runs that tests start; ``.pytest_breadcrumbs`` names the
    test that hung and must survive the worker for diagnosis.
    """
    cache_root = runtime_tmp_root / "tool-cache"
    return {
        "MYPY_CACHE_DIR": str(cache_root / "mypy"),
        "PYTHONPYCACHEPREFIX": str(cache_root / "pycache"),
        "RUFF_CACHE_DIR": str(cache_root / "ruff"),
    }


def _build_worker_env(
    *,
    task_id: str,
    dispatch_agent: str,
    attribution: Any | None = None,
    run_nonce: str = "",
    runtime_tmp_root: Path | str | None = None,
    runtime_tmp_namespace_root: Path | str | None = None,
    worktree_path: Path | None = None,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Add the legacy metadata to an already allowlisted provider environment.

    Never import the ambient environment here: parent secrets, slot ownership,
    arbitrary plugins, Python paths and pool overrides must stay excluded.
    """
    worker_env = dict(base_env or {})
    if attribution is not None:
        worker_env["LU_RUNTIME_INITIATOR"] = getattr(attribution, "initiator", str(attribution))
        worker_env["LU_RUNTIME_INITIATOR_SOURCE"] = getattr(attribution, "source", "")
    if run_nonce:
        worker_env["LU_RUNTIME_RUN_NONCE"] = run_nonce
    # Explicit dispatch-worker identity (#7827): the SessionStart gate uses
    # this marker to skip the per-agent thread lease, which belongs to the
    # orchestrator of the agent family, never to a headless worker. Both
    # names are allowlisted in agent_runtime/env_sanitize.py (name and
    # value lists — a task id containing "sk-" must survive the secret
    # redactor), so the marker reaches the harness CLI's SessionStart hook.
    # The marker is the primary signal: a read-only dispatch without
    # --worktree runs from the primary checkout, so the
    # .worktrees/dispatch/<agent>/<task>/ path is only the fallback.
    worker_env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = task_id
    worker_env["LEARN_UKRAINIAN_DISPATCH_AGENT"] = dispatch_agent
    worker_env["LU_X_AGENT_TRAILER"] = _x_agent_trailer(dispatch_agent, task_id)
    # #8645 part B: CI's `--override-ini addopts=-v` drops the pyproject
    # `-p ci.pytest_dispatch_cap`. Load it from the environment instead.
    _dispatch_cap_plugin = "ci.pytest_dispatch_cap"
    _pytest_plugins = [part.strip() for part in worker_env.get("PYTEST_PLUGINS", "").split(",") if part.strip()]
    if _dispatch_cap_plugin not in _pytest_plugins:
        _pytest_plugins.append(_dispatch_cap_plugin)
    worker_env["PYTEST_PLUGINS"] = ",".join(_pytest_plugins)
    # #8795: "ci.pytest_dispatch_cap" only resolves via pyproject.toml's
    # `pythonpath = ["scripts"]`, which is rootdir-relative and inactive for a
    # pytest process started elsewhere (e.g. a test's own `pytester` subprocess
    # in a temp dir). PYTHONPATH is an interpreter-level env var, so it makes
    # the import resolve regardless of that nested pytest's rootdir.
    _worker_scripts_dir = str((worktree_path if worktree_path is not None else _REPO_ROOT) / "scripts")
    _worker_pythonpath = [part for part in worker_env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if _worker_scripts_dir not in _worker_pythonpath:
        worker_env["PYTHONPATH"] = os.pathsep.join([_worker_scripts_dir, *_worker_pythonpath])
    if runtime_tmp_root is not None:
        worker_env["TMPDIR"] = str(runtime_tmp_root)
        worker_env["LU_RUNTIME_TMP_ROOT"] = str(runtime_tmp_root)
        worker_env["LU_TASK_EVIDENCE_DIR"] = str(Path(runtime_tmp_root) / "evidence")
        worker_env.update(_worker_tool_cache_env(Path(runtime_tmp_root)))
    if runtime_tmp_namespace_root is not None:
        worker_env["LU_RUNTIME_TMP_BASE_ROOT"] = str(Path(runtime_tmp_namespace_root).parent)
    return without_unneeded_secrets(worker_env, dispatch_agent)


def worker_exports(spec: TaskSpec, record: dict | None = None, *, base_env: Mapping[str, str]) -> dict[str, str]:
    """Bind the exports to persisted run identity; a dry-run creates no lease."""
    record = record or {}
    attribution = resolve_invocation_attribution(explicit=spec.options.get("initiator"), task_id=spec.task_id)
    if record.get("initiator_source") is not None:
        from scripts.agent_runtime.attribution import InvocationAttribution

        attribution = InvocationAttribution(record["initiator"], record["initiator_source"], spec.task_id)
    exports = _build_worker_env(
        task_id=spec.task_id, dispatch_agent=spec.agent, attribution=attribution,
        run_nonce=record.get("run_nonce", ""), runtime_tmp_root=record.get("runtime_tmp_root"),
        runtime_tmp_namespace_root=record.get("runtime_tmp_namespace_root"),
        worktree_path=spec.worktree,
    )
    # V2's selected-provider allowlist also supports seats absent from the legacy
    # runtime sanitizer (Muse, OpenCode and Hermes). Sanitize derived exports,
    # then combine them with those already admitted credentials and context.
    return {**base_env, **exports}


def prepare_worker_record(spec: TaskSpec, record: dict) -> None:
    """Resolve caller attribution before launch, then create the legacy scratch lease."""
    from scripts.dispatcher.runtime_tmp import _create_runtime_tmp_lease, _reap_runtime_tmp_lease

    attribution = resolve_invocation_attribution(explicit=spec.options.get("initiator"), task_id=spec.task_id)
    lease, namespace = _create_runtime_tmp_lease(spec.task_id)
    record.update(
        initiator=attribution.initiator, initiator_source=attribution.source,
        runtime_tmp_root=str(lease), runtime_tmp_namespace_root=str(namespace),
        tmp_bytes_freed=None, tmp_reap_error=None,
    )
    try:
        (lease / "evidence").mkdir(mode=0o700)
    except OSError:
        _reap_runtime_tmp_lease(lease, namespace, task_record=record, response="")
        raise


def reap_worker_record(record: dict, response: str | None = None) -> None:
    """Preserve evidence and record cleanup failures without failing the worker."""
    from scripts.dispatcher.runtime_tmp import _reap_runtime_tmp_lease

    if record.get("runtime_tmp_root") is not None:
        record.update(_reap_runtime_tmp_lease(
            record["runtime_tmp_root"], record.get("runtime_tmp_namespace_root"),
            task_record=record, response=response,
        ))
