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

``--registered SLOT...`` prints only accepted names, in input order, so
launcher help can check every stream key with one interpreter process.

Exit codes for ``--slot``: 0 registered, 3 not registered, 2 the registry
could not be read (fail closed: an unreadable roster is not a registered one).
Any other code (for example 1 from an interpreter that cannot import this
module) means the check could not run and callers must treat it as unverified.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as a file: put the repository root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.ai_agent_bridge import _channels

# This package's import name, from the unresolved file location: never from __package__, which a
# short import spelling (orchestration.x with scripts/ on sys.path) shortens. Its dotted parts
# are also its directories in checkout-relative paths.
_PACKAGE = f"{Path(os.path.abspath(__file__)).parents[1].name}.{Path(os.path.abspath(__file__)).parent.name}"
_MACHINERY = _PACKAGE.partition(".")[0]
_MODULE = f"{_PACKAGE}.{Path(__file__).stem}"


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
    slots = [slot for slot in _channels._load_registry_slots(assignments_path) if slot.startswith(prefix)]
    slots += [
        f"{prefix}{area}"
        for area in _channels._load_empty_slot_areas(assignments_path, provider=provider)
        if f"{prefix}{area}" not in slots and is_registered_slot(f"{prefix}{area}", assignments_path=assignments_path)
    ]
    return slots


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check launcher handoff slots against the fleet roster.\n"
            "Use from launcher validation or help; do not infer registration from a selector name."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  .venv/bin/python -m {_MODULE} --slot claude-infra\n"
            f"  .venv/bin/python -m {_MODULE} --list claude\n"
            f"  .venv/bin/python -m {_MODULE} --registered claude-infra claude-devops\n"
            "Outputs: registered slot names on stdout for --list/--registered; writes no files.\n"
            "Exit codes: 0 accepted/listed; 2 unreadable roster or invalid arguments; 3 unregistered --slot.\n"
            f"Related: {_MACHINERY}/config/area_assignments.yaml and {_MACHINERY}/lib/handoff_identity.sh."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slot", help="check one slot, e.g. claude-infra")
    group.add_argument("--list", metavar="PROVIDER", help="print the registered slots for one provider, e.g. claude")
    group.add_argument(
        "--registered",
        nargs="+",
        metavar="SLOT",
        help="print accepted slots from a batch in input order, e.g. claude-infra claude-devops",
    )
    parser.add_argument(
        "--assignments",
        type=Path,
        default=None,
        help=f"roster YAML path; default: {_MACHINERY}/config/area_assignments.yaml",
    )
    args = parser.parse_args(argv)
    if not registry_readable(args.assignments):
        print(f"handoff slot registry unreadable: {_MACHINERY}/config/area_assignments.yaml", file=sys.stderr)
        return 2
    if args.list:
        print("\n".join(registered_slots(args.list, assignments_path=args.assignments)))
        return 0
    if args.registered:
        for slot in args.registered:
            if is_registered_slot(slot, assignments_path=args.assignments):
                print(slot)
        return 0
    return 0 if is_registered_slot(args.slot, assignments_path=args.assignments) else 3


if __name__ == "__main__":
    raise SystemExit(main())
