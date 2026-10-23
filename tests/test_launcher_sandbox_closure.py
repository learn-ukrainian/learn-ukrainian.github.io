"""Sandbox closure must include bytecode that lives under PYTHONPYCACHEPREFIX.

Defect class: a compatibility shim such as ``scripts/fleet_comms/contracts.py``
is opened only as prefix bytecode, then replaces its own ``sys.modules`` entry.
Dropping that path leaves every launcher sandbox without the shim, so the
handoff-slot gate refuses before provider logic.
"""

from __future__ import annotations

from tests.launcher_sandbox import slot_registry_sources


def test_slot_registry_closure_includes_fleet_comms_contracts_shim() -> None:
    sources = {path.as_posix() for path in slot_registry_sources()}
    assert "scripts/fleet_comms/contracts.py" in sources
