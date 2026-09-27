"""Answer "is this handoff slot registered?" for launchers (#8303).

A launcher mints ``SESSION_HANDOFF_AGENT`` as ``<provider>-<lane>``.  A name
that is not in the fleet roster cannot receive inbox mail, fails the dispatch
lane self-test and lets rollover detection fall back to another lane's packet
pool, so the launcher must refuse it before it starts a session.

There is deliberately no roster parser here: the registry is
``scripts/config/area_assignments.yaml`` and the only readers are the bridge
helpers in ``scripts.ai_agent_bridge._channels`` -- the same ones that build
the ``--for`` choices.  A slot is registered when the bridge accepts it as a
recipient, either as a roster slot or as the ``<provider>-<empty-roster-area>``
alias of a bare provider (``claude-monitor`` -> ``claude``, #7597).

Exit codes for ``--slot``: 0 registered, 3 not registered, 2 the registry
could not be read (fail closed: an unreadable roster is not a registered one).
Any other code (for example 1 from an interpreter that cannot import this
module) means the check could not run and callers must treat it as unverified.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.ai_agent_bridge import _channels


def registry_readable(assignments_path: Path | None = None) -> bool:
    """True when the roster loaded at least one slot beyond the static identities."""
    return bool(_channels._load_registry_slots(assignments_path))


def is_registered_slot(slot: str, *, assignments_path: Path | None = None) -> bool:
    if not slot:
        return False
    alias = _channels.resolve_recipient_alias(slot, assignments_path=assignments_path)
    return alias in _channels.get_valid_agents(assignments_path=assignments_path)


def registered_slots(provider: str, *, assignments_path: Path | None = None) -> list[str]:
    """Roster slots for one provider, plus its empty-roster area aliases."""
    prefix = f"{provider}-"
    slots = [
        slot
        for slot in _channels._load_registry_slots(assignments_path)
        if slot.startswith(prefix)
    ]
    slots += [
        f"{prefix}{area}"
        for area in _channels._load_empty_slot_areas(assignments_path)
        if f"{prefix}{area}" not in slots
    ]
    return slots


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slot", help="slot to check, e.g. claude-infra")
    group.add_argument("--list", metavar="PROVIDER", help="print the registered slots for a provider")
    parser.add_argument("--assignments", type=Path, default=None, help="area_assignments.yaml path")
    args = parser.parse_args(argv)
    if not registry_readable(args.assignments):
        print("handoff slot registry unreadable: scripts/config/area_assignments.yaml", file=sys.stderr)
        return 2
    if args.list:
        print("\n".join(registered_slots(args.list, assignments_path=args.assignments)))
        return 0
    return 0 if is_registered_slot(args.slot, assignments_path=args.assignments) else 3


if __name__ == "__main__":
    raise SystemExit(main())
