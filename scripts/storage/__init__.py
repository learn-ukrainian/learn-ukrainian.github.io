"""Approved bulk-source storage topology (SMB mirror + Drive fallback).

Public entry points:

- ``resolve_topology`` / ``resolve_bulk_root`` — deterministic bulk-root choice
- ``python -m scripts.storage status`` — read-only status report
- ``hold_database`` / ``lift_database`` — db and companion permission changes
- ``get_companion_paths`` / ``inspect_database_permissions`` — permission inspection

See ``docs/runbooks/storage-topology.md`` and the shared rule
``agents_extensions/shared/rules/storage-topology.md``.
"""

from __future__ import annotations

from scripts.storage.topology import (
    BulkRootResolution,
    TopologyStatus,
    resolve_active_sources_db,
    resolve_bulk_root,
    resolve_topology,
)
from scripts.storage.wal_permissions import (
    get_companion_paths,
    hold_database,
    inspect_database_permissions,
    lift_database,
)

__all__ = [
    "BulkRootResolution",
    "TopologyStatus",
    "get_companion_paths",
    "hold_database",
    "inspect_database_permissions",
    "lift_database",
    "resolve_active_sources_db",
    "resolve_bulk_root",
    "resolve_topology",
]
