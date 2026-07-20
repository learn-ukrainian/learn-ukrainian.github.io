"""Common harness-owned supervisor library for fenced session-stream leases.

This is the PR-I contract surface.  Launchers own process creation; this module
opens or resumes a driver lease before that creation and renders the bounded
bootstrap capsule the launcher passes to the harness.  It intentionally does
not put lease actions in the capsule or allow workers to receive lease state.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.dual_write import resolve_handoff_path
from agents_extensions.shared.session_streams.hooks import clean_exit_hook, lease_from_environment
from agents_extensions.shared.session_streams.inventory import epic_handoff_map
from agents_extensions.shared.session_streams.model import (
    Lease,
    LeaseHolder,
    StreamDigest,
    canonical_json,
    entry_as_dict,
    sha256_text,
)
from agents_extensions.shared.session_streams.receipts import list_migration_state
from agents_extensions.shared.session_streams.store import SessionStreamError, SessionStreamStore

CAPSULE_SCHEMA = "session-supervisor-bootstrap.v1"
LEASE_ENV_PREFIX = "SESSION_STREAM_"


class SupervisorError(ValueError):
    """A launch request violates the common supervisor contract."""


class LaunchRole(StrEnum):
    """The only roles accepted by the launcher-supervisor boundary."""

    DRIVER = "driver"
    WORKER = "worker"


@dataclass(frozen=True, slots=True)
class BootstrapCapsule:
    """Read-only cold-start payload in the architecture's fixed order."""

    role: LaunchRole
    stream_id: str
    lease: dict[str, Any] | None
    digest: StreamDigest
    handoff_paths: tuple[str, ...]
    active_handoff_path: str | None
    dual_write_mode: str
    dual_write_drift: bool

    def as_dict(self) -> dict[str, Any]:
        """Return the stable JSON-ready capsule without executable lease actions."""
        payload = {
            "schema": CAPSULE_SCHEMA,
            "identity": {
                "role": self.role.value,
                "stream_id": self.stream_id,
                "lease": self.lease,
                "lease_credentials_exported": False,
            },
            "rollover": None,
            "digest": {
                "stream_id": self.digest.stream_id,
                "high_water_entry_id": self.digest.high_water_entry_id,
                "digest_sha256": self.digest.digest_sha256,
                "pinned": [entry_as_dict(entry) for entry in self.digest.pinned],
                "recent": [entry_as_dict(entry) for entry in self.digest.recent],
            },
            "dual_write": {
                "mode": self.dual_write_mode,
                "handoff_paths": list(self.handoff_paths),
                "active_handoff_path": self.active_handoff_path,
                "drift": self.dual_write_drift,
            },
            "diagnostics": {
                "digest_source": "supervisor-local-fallback",
                "lease_actions": "supervisor-only",
            },
        }
        payload["capsule_sha256"] = sha256_text(canonical_json(payload))
        return payload


def strip_lease_credentials(environment: Mapping[str, str]) -> dict[str, str]:
    """Return a worker-safe environment with every lease field removed."""
    return {key: value for key, value in environment.items() if not key.startswith(LEASE_ENV_PREFIX)}


class SessionSupervisor:
    """Compose the session-stream store into a launcher-owned lifecycle surface."""

    def __init__(self, store: SessionStreamStore, *, repo_root: Path) -> None:
        self.store = store
        self.repo_root = repo_root.resolve()

    @staticmethod
    def _require_driver(role: LaunchRole | str) -> None:
        try:
            resolved = LaunchRole(role)
        except ValueError as exc:
            raise SupervisorError("role must be driver or worker") from exc
        if resolved is not LaunchRole.DRIVER:
            raise SupervisorError("workers cannot acquire, resume, heartbeat, or close driver leases")

    def open_driver(
        self,
        *,
        role: LaunchRole | str,
        stream_id: str,
        holder: LeaseHolder,
        lineage_id: str,
        ttl_seconds: int,
    ) -> Lease:
        """Open one exact fenced driver lease before a harness is started."""
        self._require_driver(role)
        return self.store.open_session(
            stream_id=stream_id,
            holder=holder,
            lineage_id=lineage_id,
            ttl_seconds=ttl_seconds,
            reason="common session supervisor driver open",
        )

    def resume_driver(self, *, role: LaunchRole | str, lease: Lease) -> Lease:
        """Resume only the exact pre-existing lease envelope by heartbeating it."""
        self._require_driver(role)
        return self.store.heartbeat(lease)

    def heartbeat_driver(self, *, role: LaunchRole | str, lease: Lease) -> Lease:
        """Heartbeat only the exact fenced driver lease."""
        self._require_driver(role)
        return self.store.heartbeat(lease)

    def close_driver(self, *, role: LaunchRole | str, lease: Lease) -> str:
        """Cleanly close only the exact driver session."""
        self._require_driver(role)
        return clean_exit_hook(self.store, lease).state

    def recover_expired_driver(self, *, role: LaunchRole | str, stream_id: str) -> None:
        """Fail closed until recovery-plan receipts bind the full PR-I proof set."""
        self._require_driver(role)
        raise SupervisorError(
            "automatic recovery is unavailable: require an audited recovery-plan digest and exact receipts"
        )

    def build_capsule(
        self,
        *,
        role: LaunchRole | str,
        stream_id: str,
        lease: Lease | None = None,
        digest_limit: int = 20,
    ) -> BootstrapCapsule:
        """Render the ordered local fallback capsule for a driver or worker."""
        try:
            resolved_role = LaunchRole(role)
        except ValueError as exc:
            raise SupervisorError("role must be driver or worker") from exc
        if resolved_role is LaunchRole.WORKER and lease is not None:
            raise SupervisorError("workers cannot receive driver lease credentials")
        if resolved_role is LaunchRole.DRIVER and lease is None:
            raise SupervisorError("drivers require an exact supervisor-owned lease to build a capsule")
        if lease is not None and lease.stream_id != stream_id:
            raise SupervisorError("capsule stream_id must exactly match the lease stream_id")

        digest = self.store.load_digest(stream_id, limit=digest_limit)
        handoff_paths = tuple(epic_handoff_map(self.repo_root).get(stream_id, ()))
        active = resolve_handoff_path(stream_id, self.repo_root)
        mode, drift = self._dual_write_status(stream_id)
        lease_summary = self._lease_summary(lease) if resolved_role is LaunchRole.DRIVER and lease else None
        return BootstrapCapsule(
            role=resolved_role,
            stream_id=stream_id,
            lease=lease_summary,
            digest=digest,
            handoff_paths=handoff_paths,
            active_handoff_path=self._relative_path(active),
            dual_write_mode=mode,
            dual_write_drift=drift,
        )

    def _dual_write_status(self, stream_id: str) -> tuple[str, bool]:
        rows = list_migration_state(self.store)
        mode = next((str(row["mode"]) for row in rows if row["stream_id"] == stream_id), "unregistered")
        with self.store._read_snapshot() as connection:
            row = connection.execute(
                "SELECT status FROM legacy_projection_receipts WHERE stream_id = ? "
                "ORDER BY projection_id DESC LIMIT 1",
                (stream_id,),
            ).fetchone()
        return mode, bool(row and str(row["status"]) in {"drift", "failed"})

    def _relative_path(self, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return str(path)

    @staticmethod
    def _lease_summary(lease: Lease) -> dict[str, Any]:
        return {
            "session_id": lease.session_id,
            "lease_id": lease.lease_id,
            "generation": lease.generation,
            "fencing_token": lease.fencing_token,
            "expires_at": lease.expires_at,
        }


def build_parser() -> argparse.ArgumentParser:
    """Build the small CLI contract that future launchers invoke."""
    parser = argparse.ArgumentParser(
        prog="session-supervisor",
        description="Open and supervise fenced driver leases; workers only receive read-only capsules.",
    )
    parser.add_argument("--db", type=Path, default=None, help="Session-stream SQLite path.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root for handoff status.")
    commands = parser.add_subparsers(dest="command", required=True)

    open_driver = commands.add_parser("open", help="Open a driver lease and emit its bootstrap capsule.")
    _add_driver_identity(open_driver)
    open_driver.add_argument("--lineage-id", required=True)
    open_driver.add_argument("--ttl-seconds", type=int, default=300)
    open_driver.add_argument("--digest-limit", type=int, default=20)

    for name, help_text in (
        ("resume", "Heartbeat an exact inherited driver lease and emit a capsule."),
        ("heartbeat", "Heartbeat an exact inherited driver lease."),
        ("close", "Close an exact inherited driver lease."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--role", required=True, choices=tuple(LaunchRole))
        if name == "resume":
            command.add_argument("--digest-limit", type=int, default=20)

    capsule = commands.add_parser("capsule", help="Render a read-only bootstrap capsule.")
    capsule.add_argument("--role", required=True, choices=tuple(LaunchRole))
    capsule.add_argument("--stream", required=True)
    capsule.add_argument("--digest-limit", type=int, default=20)

    commands.add_parser("worker-env", help="Print the current environment with all lease fields stripped.")
    return parser


def _add_driver_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--role", required=True, choices=tuple(LaunchRole))
    parser.add_argument("--stream", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--process-id", required=True, type=int)
    parser.add_argument("--task-id", default=None)


def main(argv: list[str] | None = None) -> int:
    """Run one lifecycle action and render only JSON to stdout."""
    args = build_parser().parse_args(argv)
    if args.command == "worker-env":
        print(json.dumps(strip_lease_credentials(os.environ), ensure_ascii=False, sort_keys=True))
        return 0

    supervisor = SessionSupervisor(
        SessionStreamStore(SessionStreamDatabase(args.db)), repo_root=args.repo_root
    )
    try:
        if args.command == "open":
            holder = LeaseHolder(
                agent=args.agent,
                harness=args.harness,
                instance_id=args.instance_id,
                process_id=args.process_id,
                task_id=args.task_id,
            )
            lease = supervisor.open_driver(
                role=args.role,
                stream_id=args.stream,
                holder=holder,
                lineage_id=args.lineage_id,
                ttl_seconds=args.ttl_seconds,
            )
            payload = supervisor.build_capsule(
                role=args.role, stream_id=args.stream, lease=lease, digest_limit=args.digest_limit
            ).as_dict()
        elif args.command in {"resume", "heartbeat", "close"}:
            lease = lease_from_environment()
            if args.command == "resume":
                renewed = supervisor.resume_driver(role=args.role, lease=lease)
                payload = supervisor.build_capsule(
                    role=args.role,
                    stream_id=renewed.stream_id,
                    lease=renewed,
                    digest_limit=args.digest_limit,
                ).as_dict()
            elif args.command == "heartbeat":
                renewed = supervisor.heartbeat_driver(role=args.role, lease=lease)
                payload = {"action": "heartbeat", "stream_id": renewed.stream_id, "expires_at": renewed.expires_at}
            else:
                payload = {"action": "close", "stream_id": lease.stream_id, "state": supervisor.close_driver(role=args.role, lease=lease)}
        else:
            payload = supervisor.build_capsule(
                role=args.role, stream_id=args.stream, digest_limit=args.digest_limit
            ).as_dict()
    except (SessionStreamError, SupervisorError, ValueError) as exc:
        print(f"session-supervisor: {exc}", file=sys.stderr)
        return 4
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
