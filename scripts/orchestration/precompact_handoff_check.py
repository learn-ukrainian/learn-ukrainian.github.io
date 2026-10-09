"""Read-only, anchored proof of this Claude session's prepared handoff (#9790).

Only a successful check emits ``prepared``. Missing or unsafe evidence is silent;
the shell hook refuses driver compaction regardless of this result. Evidence
only selects the handoff instruction in that refusal.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from scripts.common.safe_open import safe_open_below
from scripts.lib.session_record import _validate_record, validate_session_id
from scripts.orchestration.thread_handoff import (
    _BundleReconcileTree,
    default_state_path,
    lineage_id_for,
    normalize_agent_name,
    normalize_lineage_id,
    validate_live_lease,
)


def _read_text(tree: _BundleReconcileTree, path: str) -> str:
    """Read only the regular file opened beneath held no-follow directories."""
    with tree.parent(path) as (parent, name):
        fd = safe_open_below(parent, name, os.O_RDONLY)
        with os.fdopen(fd, encoding="utf-8") as handle:
            return handle.read()


def has_prepared_handoff(state_root: Path, *, agent: str, session_id: str) -> bool:
    """Prove the mode, predecessor identity, canonical lease and readable handoff.

    Lineages survive replacement sessions, so discover them through the held agent
    directory rather than assuming the current session created its lineage. The
    validator receives decoded descriptor-read bytes and a lexical canonical path;
    it performs no file reads. Never resolve a state or handoff pathname.
    """
    try:
        agent = normalize_agent_name(agent)
        if not (agent == "claude" or agent.startswith("claude-")) or not validate_session_id(session_id):
            return False
        with _BundleReconcileTree(state_root, agent, lineage_id_for(agent, session_id)) as tree:
            record = _validate_record(
                json.loads(_read_text(tree, f".agent/sessions/{session_id}.json")),
                expected_session_id=session_id,
            )
            if record.get("rollover_mode") != "operator_restart":
                return False
            with tree.parent(f".agent/thread-rollovers/{agent}/lease.json") as (agent_fd, _):
                lineages = os.listdir(agent_fd)
            for lineage in lineages:
                if not lineage.startswith("lineage-") or normalize_lineage_id(lineage) != lineage:
                    continue
                state_path = default_state_path(agent, lineage)
                state = json.loads(_read_text(tree, state_path.as_posix()))
                if not isinstance(state, dict):
                    return False
                active = state.get("active")
                if not isinstance(active, dict) or active.get("thread_id") != session_id:
                    continue
                replacement, error = validate_live_lease(state, agent=agent, state_path=state_root / state_path)
                if error or replacement is None or replacement["status"] not in {"pending_start", "resumed"}:
                    return False
                return bool(_read_text(tree, replacement["handoff_path"]).strip())
    except Exception:
        # Evidence failures select the shell hook's generic refusal instruction.
        # The shell bounds this entire process, including stdin and filesystem reads.
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--agent", default="claude")
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreCompact":
            return 0
        if payload.get("trigger") != "auto":
            return 0
        session_id = payload.get("session_id")
        if isinstance(session_id, str) and has_prepared_handoff(
            args.state_root, agent=args.agent, session_id=session_id
        ):
            print("prepared")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
