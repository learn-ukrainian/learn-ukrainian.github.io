"""One-off reproducer for OPSEC seam counts in monitor-api-router-inventory.md.

Run from repo root:
  /path/to/.venv/bin/python docs/design/count_opsec_fixture_seams.py
"""

from __future__ import annotations

import importlib
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import (
    epics_router,
    issues_router,
    site_router,
    work_router,
    worktrees_router,
)
from scripts.api import main as api_main
from scripts.orchestration import reap_worktrees
from scripts.wiki import sources_db  # noqa: F401 — same import as isolated_fixture

GLOBAL_SEAMS = frozenset(
    {
        "subprocess.run",
        "subprocess.Popen",
        "socket.create_connection",
        "sqlite3.connect",
    }
)


class _FixtureSessionStore:
    def load_digest(self, *_args, **_kwargs):
        return type("D", (), {"pinned": (), "recent": ()})()


class _FixtureHandoff:
    def __init__(self, stream_id: str) -> None:
        self.stream_id = stream_id


class MonkeypatchRecorder:
    def __init__(self) -> None:
        self.invocations: list[str] = []
        self.unique: dict[str, bool] = {}

    def setattr(self, target, name, value) -> None:
        mod = target.__name__ if hasattr(target, "__name__") else type(target).__name__
        key = f"{mod}.{name}"
        self.invocations.append(key)
        self.unique[key] = True

    def setenv(self, key: str, value: str) -> None:
        os.environ[key] = value


def replay_isolated_fixture(monkeypatch: MonkeypatchRecorder, root: Path) -> None:
    """Mirror isolated_fixture setattr side effects (no pytest tmp_path wrapper)."""
    monkeypatch.setattr(work_router, "_IN_FLIGHT_BUILDS", {})
    epics_store = SessionStreamStore(SessionStreamDatabase(root / "stores" / "epics.sqlite3"))
    monkeypatch.setattr(epics_router, "_store", lambda: epics_store)
    handoff_path = root / "batch_state" / "session-handoff.md"
    handoff_path.write_text("fixture handoff\n", encoding="utf-8")
    monkeypatch.setattr(api_main, "_health_instance_identity", lambda: {})
    monkeypatch.setenv("MONITOR_OCCUPANCY_HOST_IDS", "opsec-host-alias=opsec-host-id")
    monkeypatch.setenv("LU_MONITOR_HOST_ID", "opsec-host-id")
    monkeypatch.setenv("AGENT_NO_TELEMETRY_FOOTER", "1")
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(root / "batch_state" / "atlas-jobs"))

    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("scripts.api") or module is None:
            continue
        for name, value in tuple(vars(module).items()):
            if not isinstance(value, Path) or not value.is_absolute():
                continue
            replacement = root / "seams" / module_name.replace(".", "_") / name.lower()
            replacement.parent.mkdir(parents=True, exist_ok=True)
            if value.is_dir() or value.suffix == "":
                replacement.mkdir(parents=True, exist_ok=True)
            monkeypatch.setattr(module, name, replacement)
        if "_run_command" in vars(module):
            monkeypatch.setattr(
                module,
                "_run_command",
                lambda *args, **_kwargs: subprocess.CompletedProcess(
                    args=args[0] if args else [],
                    returncode=0,
                    stdout="",
                    stderr="",
                ),
            )

    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(socket, "create_connection", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        worktrees_router,
        "_run",
        lambda *_args, **_kwargs: (127, "", "fixture git unavailable"),
    )
    monkeypatch.setattr(
        issues_router,
        "_run_gh",
        lambda *_args, **_kwargs: (127, "", "fixture gh unavailable"),
    )
    monkeypatch.setattr(
        site_router,
        "_run",
        lambda args, **_kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=127,
            stderr="fixture command unavailable",
            stdout="",
        ),
    )
    # NOTE (#7269 step 12c): collect_adr_governance short-circuits on fixture
    # context; no sweep stub.
    monkeypatch.setattr(reap_worktrees, "_run", lambda *_args, **_kwargs: (0, "", ""))

    # Keep ``wiki.sources_db`` loaded so the wiki-prefix external-store
    # loop still owns that module's Path globals (step 12d). Step 10
    # deleted the RAG-specific setattr copies, not the wiki loop.
    importlib.import_module("rag.query")
    importlib.import_module("scripts.fleet_comms.legacy_broker_report")
    importlib.import_module("scripts.telemetry.legacy_bridge")
    importlib.import_module("wiki.state")
    for module_name, module in tuple(sys.modules.items()):
        if module is None or not module_name.startswith(("scripts.ai_agent_bridge", "scripts.telemetry", "wiki")):
            continue
        for name, value in tuple(vars(module).items()):
            if not isinstance(value, Path) or not value.is_absolute():
                continue
            if not any(token in name.upper() for token in ("DB", "PROGRESS", "STATE")):
                continue
            replacement = root / "stores" / module_name.replace(".", "_") / name.lower()
            replacement.parent.mkdir(parents=True, exist_ok=True)
            if value.is_dir() or value.suffix == "":
                replacement.mkdir(parents=True, exist_ok=True)
            monkeypatch.setattr(module, name, replacement)

    broker_report = importlib.import_module("scripts.fleet_comms.legacy_broker_report")
    monkeypatch.setattr(broker_report, "main_checkout_root", lambda _repo_root: root)
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: sqlite3.connect(*args, **kwargs))

    dashboards_root = root / "dashboards"
    monkeypatch.setattr(api_main, "DASHBOARDS_DIR", dashboards_root)

    isolated_plane_root = root / "stores" / "fleet-comms"
    isolated_plane_root.mkdir(parents=True, exist_ok=True)

    def isolated_plane_resolver(repo_root: Path | None = None) -> Path:
        del repo_root
        return isolated_plane_root

    monkeypatch.setenv("FLEET_COMMS_ROOT", str(isolated_plane_root))
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("scripts.api") or module is None:
            continue
        if "default_plane_root" in vars(module):
            monkeypatch.setattr(module, "default_plane_root", isolated_plane_resolver)


def main() -> None:
    mp = MonkeypatchRecorder()
    root = Path(tempfile.mkdtemp())
    (root / "batch_state").mkdir(parents=True)
    (root / "stores").mkdir(parents=True)
    replay_isolated_fixture(mp, root)

    global_unique = sum(1 for key in mp.unique if key in GLOBAL_SEAMS)
    router_unique = len(mp.unique) - global_unique
    global_invocations = sum(1 for key in mp.invocations if key in GLOBAL_SEAMS)
    router_invocations = len(mp.invocations) - global_invocations

    print(f"unique_logical_seams: {len(mp.unique)}")
    print(f"router_attributed_unique: {router_unique}")
    print(f"global_backstops: {global_unique}")
    print(f"setattr_invocations_total: {len(mp.invocations)}")
    print(f"router_attributed_invocations: {router_invocations}")


if __name__ == "__main__":
    main()
