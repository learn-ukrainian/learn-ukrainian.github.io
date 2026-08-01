"""Provider-neutral CLI for the body-free context-link projection.

Commands: ``status``, ``lookup``, ``explain``, ``rebuild``, ``admit``.
Every command is local-only: none of them calls Entire, GitHub, Fleet, ACP,
Monitor, or the network. A missing or disabled projection is reported as a
body-free status payload, never as a traceback, and read commands never create
local state.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .model import ContextLink, SchemaError, VerificationEvidence
from .store import AdmitOutcome, ContextLinkStore

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_REFUSED = 2

DEFAULT_DB_RELATIVE = Path("batch_state") / "entire-context" / "v1" / "context-links.sqlite3"
ENV_DB = "ENTIRE_CONTEXT_DB"
ENV_DISABLED = "ENTIRE_CONTEXT_DISABLED"


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _resolve_db(args: argparse.Namespace) -> Path:
    if getattr(args, "db", None):
        return Path(args.db)
    env = os.environ.get(ENV_DB)
    if env:
        return Path(env)
    return Path.cwd() / DEFAULT_DB_RELATIVE


def _disabled() -> bool:
    return os.environ.get(ENV_DISABLED, "").strip().lower() in {"1", "true", "yes", "on"}


def _unavailable_payload(db_path: Path, reason: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "available": False,
        "reason": reason,
        "projection_path": str(db_path),
    }


def _guard(args: argparse.Namespace) -> tuple[Path, dict[str, Any] | None]:
    """Resolve the projection; return (path, early-payload) for disabled/missing."""
    db_path = _resolve_db(args)
    if _disabled():
        return db_path, {"enabled": False, "reason": "projection_disabled", "projection_path": str(db_path)}
    if not db_path.is_file():
        return db_path, _unavailable_payload(db_path, "projection_missing")
    return db_path, None


def cmd_status(args: argparse.Namespace) -> int:
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    try:
        payload = ContextLinkStore(db_path).status()
    except sqlite3.Error:
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    payload.update({"enabled": True, "available": True, "projection_path": str(db_path)})
    _emit(payload)
    return EXIT_OK


def cmd_lookup(args: argparse.Namespace) -> int:
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    try:
        link = ContextLinkStore(db_path).lookup(args.locator_id)
    except sqlite3.Error:
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    if link is None:
        _emit({"found": False, "locator_id": args.locator_id})
        return EXIT_NOT_FOUND
    _emit({"found": True, "link": link})
    return EXIT_OK


def cmd_explain(args: argparse.Namespace) -> int:
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    try:
        detail = ContextLinkStore(db_path).explain(args.locator_id)
    except sqlite3.Error:
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    if detail is None:
        _emit({"found": False, "locator_id": args.locator_id})
        return EXIT_NOT_FOUND
    _emit({"found": True, **detail})
    return EXIT_OK


def cmd_rebuild(args: argparse.Namespace) -> int:
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    try:
        result = ContextLinkStore(db_path).rebuild()
    except sqlite3.Error:
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    _emit({"available": True, "projection_path": str(db_path), **result})
    return EXIT_OK if result["parity"] else EXIT_REFUSED


def _load_json_file(path: str, label: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"{label} is not readable JSON") from exc
    if not isinstance(payload, dict):
        raise SchemaError(f"{label} must be a JSON object")
    return payload


def cmd_admit(args: argparse.Namespace) -> int:
    db_path = _resolve_db(args)
    if _disabled():
        _emit(
            {
                "enabled": False,
                "outcome": AdmitOutcome.REFUSED.value,
                "reason": "projection_disabled",
                "state": "unavailable",
            }
        )
        return EXIT_REFUSED
    try:
        link = ContextLink.from_dict(_load_json_file(args.link, "link file"))
        verification = (
            VerificationEvidence.from_dict(_load_json_file(args.verification, "verification file"))
            if args.verification
            else None
        )
    except SchemaError as exc:
        _emit({"outcome": AdmitOutcome.REFUSED.value, "reason": "schema_invalid", "detail": str(exc)})
        return EXIT_REFUSED
    result = ContextLinkStore(db_path).admit(link, verification, actor=args.actor)
    _emit(result.to_dict())
    return EXIT_OK if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED) else EXIT_REFUSED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.entire_context",
        description=(
            "Body-free, provider-neutral context-link index (ADR-018 / #6174). "
            "Local-only: no Entire, GitHub, Fleet, ACP, Monitor, or network calls."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_db_flag(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--db",
            default=None,
            help=f"Projection SQLite path (default: {ENV_DB} or {DEFAULT_DB_RELATIVE})",
        )

    status = sub.add_parser("status", help="Body-free aggregate projection status")
    add_db_flag(status)
    status.set_defaults(func=cmd_status)

    lookup = sub.add_parser("lookup", help="Known-ID lookup of a promoted context link")
    lookup.add_argument("locator_id", help="Deterministic clink_<sha256> locator ID")
    add_db_flag(lookup)
    lookup.set_defaults(func=cmd_lookup)

    explain = sub.add_parser("explain", help="Body-free lifecycle audit trail for a known locator ID")
    explain.add_argument("locator_id", help="Deterministic clink_<sha256> locator ID")
    add_db_flag(explain)
    explain.set_defaults(func=cmd_explain)

    rebuild = sub.add_parser("rebuild", help="Replay the append-only event log into the projection")
    add_db_flag(rebuild)
    rebuild.set_defaults(func=cmd_rebuild)

    admit = sub.add_parser("admit", help="Admit one claim from body-free JSON fixtures")
    admit.add_argument("--link", required=True, help="JSON file with one context-link payload")
    admit.add_argument(
        "--verification",
        default=None,
        help="JSON file with the caller-recorded canonical verification result",
    )
    admit.add_argument("--actor", default="cli", help="Body-free actor identity (default: cli)")
    add_db_flag(admit)
    admit.set_defaults(func=cmd_admit)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
