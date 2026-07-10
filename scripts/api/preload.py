"""Preload the import closure for API startup resilience."""

from __future__ import annotations

import importlib
import logging
import time
from pathlib import Path

logger = logging.getLogger("api.preload")

# Explicit list of static nested imports in scripts/api/**
PRELOAD_MODULES = [
    # Required standard library & third party modules
    "yaml",
    "json",
    "hashlib",
    "logging",
    "datetime",
    "os",
    "re",
    "subprocess",
    "asyncio",
    "pathlib",
    "fastapi.responses",

    # Internal required modules
    "scripts.api.state_build",
    "scripts.api.state_helpers",
    "scripts.api.rules_router",
    "scripts.api.session_router",
    "scripts.api.telemetry.response",
    "scripts.api.review_parsing",
    "scripts.orchestration",
    "audit.config",
    "audit.checks.activity_validation",
    "yaml_activities",
    "scripts.guardrails",
    "scripts.audit.check_core_bare",
    "audit.check_core_bare",
    "scripts.audit.check_self_symlinks",
    "audit.check_self_symlinks",
    "scripts.build.phase_constants",
    "agent_runtime.adapters.gemini",
]

# Heavy or optional dependencies (try/except ImportError, record skipped)
OPTIONAL_MODULES = [
    "pymupdf",
    "fitz",
    "rag.poc_pair_page",
    "rag.query",
    "research_quality",
    "ai_agent_bridge",
    "ai_agent_bridge._channels",
    "ai_agent_bridge._db",
    "scripts.ai_agent_bridge",
    "scripts.ai_agent_bridge._channels",
]

DYNAMIC_LOADERS = {
    "scripts.api.runtime_router": {
        "description": "Loads agent runtime adapters dynamically from scripts/agent_runtime/adapters/",
        "strategy": "walk_adapters",
    },
    "scripts.api.comms_router": {
        "description": "Loads broker migration files dynamically using spec_from_file_location",
        "strategy": "load_migration",
    }
}

def preload_all() -> None:
    """Preload all static and dynamic modules in the API import closure.

    Aborts startup loudly if any required module fails to load.
    """
    start_time = time.perf_counter()
    pinned_count = 0
    skipped_count = 0
    skipped_names = []

    # 1. Load required static modules
    for name in PRELOAD_MODULES:
        try:
            importlib.import_module(name)
            pinned_count += 1
        except ImportError as e:
            logger.error(f"Required module preload failed: {name}. Error: {e}")
            raise RuntimeError(f"Required module preload failed: {name}") from e

    # 2. Load optional/heavy static modules
    for name in OPTIONAL_MODULES:
        try:
            importlib.import_module(name)
            pinned_count += 1
        except ImportError:
            skipped_count += 1
            skipped_names.append(name)

    # 3. Dynamic loaders: walk scripts/agent_runtime/adapters/
    api_dir = Path(__file__).resolve().parent
    adapters_dir = api_dir.parent / "agent_runtime" / "adapters"
    if adapters_dir.exists():
        for path in sorted(adapters_dir.glob("*.py")):
            if path.stem in {"__init__", "base"} or path.stem.startswith("_"):
                continue
            module_name = f"agent_runtime.adapters.{path.stem}"
            try:
                importlib.import_module(module_name)
                pinned_count += 1
            except ImportError:
                skipped_count += 1
                skipped_names.append(module_name)

    # 4. Cover comms_router's spec_from_file_location target file
    migration_path = api_dir.parent / "migrations" / "2026-05-06-broker-indexes.py"
    if migration_path.exists():
        try:
            from importlib import util as importlib_util
            spec = importlib_util.spec_from_file_location("broker_indexes_20260506", migration_path)
            if spec is not None and spec.loader is not None:
                module = importlib_util.module_from_spec(spec)
                spec.loader.exec_module(module)
                pinned_count += 1
        except Exception:
            skipped_count += 1
            skipped_names.append("broker_indexes_20260506")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    log_msg = f"preload: {pinned_count} pinned, {skipped_count} optional-skipped, took {elapsed_ms:.1f} ms"
    print(log_msg)
    logger.info(log_msg)
