"""Provider-neutral CLI for the body-free context-link projection.

Phase-1 commands: ``status``, ``lookup``, ``explain``, ``rebuild``, ``admit``.
Phase-2 commands: ``bootstrap-git``, ``bootstrap-acp``, ``search``,
``explain-change``, ``handoff``.

Every command is local-only: none of them calls Entire, GitHub, Fleet, ACP
providers, Monitor, or the network. Resolution uses read-only local ``git``
plumbing and the body-free ACP terminal receipt verifier. A missing or
disabled projection is reported as a body-free status payload, never as a
traceback, and read commands never create local state. Query text and
consumer labels are accepted but never persisted or echoed, so Codex, Kimi,
GLM, and other harnesses receive byte-identical results for identical
invocations.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .model import (
    ContextLink,
    SchemaError,
    VerificationEvidence,
    canonical_json,
    validate_identity,
)
from .recall import (
    MAX_RESULTS,
    MAX_SCAN_ROWS,
    RecallInputError,
    explain_change,
    prepare_handoff,
    search_past_work,
)
from .resolvers import (
    ResolutionError,
    resolve_acp_conversation,
    resolve_git_commit,
)
from .store import AdmitOutcome, ContextLinkStore

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_REFUSED = 2

DEFAULT_DB_RELATIVE = Path("batch_state") / "entire-context" / "v1" / "context-links.sqlite3"
ENV_DB = "ENTIRE_CONTEXT_DB"
ENV_DISABLED = "ENTIRE_CONTEXT_DISABLED"
ENV_ACP_ROOT = "ENTIRE_CONTEXT_ACP_ROOT"


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
    except (sqlite3.Error, KeyError, TypeError, ValueError):
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
    except (sqlite3.Error, KeyError, TypeError, ValueError):
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
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    if detail is None:
        _emit({"found": False, "locator_id": args.locator_id})
        return EXIT_NOT_FOUND
    _emit({"found": True, **detail})
    return EXIT_OK


def cmd_rebuild(args: argparse.Namespace) -> int:
    """Replay projection state, refusing corrupt input because this command mutates state.

    Observational commands report an unreadable optional projection with a
    successful body-free status payload. Rebuild is a recovery mutation: if
    the event log cannot be read, no repair was applied and callers receive
    ``EXIT_REFUSED``.
    """
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    try:
        result = ContextLinkStore(db_path).rebuild()
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_REFUSED
    _emit({"available": True, "projection_path": str(db_path), **result})
    return EXIT_OK


def _load_json_file(path: str, label: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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
    try:
        result = ContextLinkStore(db_path).admit(link, verification, actor=args.actor)
    except SchemaError as exc:
        _emit({"outcome": AdmitOutcome.REFUSED.value, "reason": "schema_invalid", "detail": str(exc)})
        return EXIT_REFUSED
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_REFUSED
    _emit(result.to_dict())
    return EXIT_OK if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED) else EXIT_REFUSED


# ── Phase-2: explicit bootstrap, recall, explain, handoff ────────────────────


def _resolve_repo(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "repo", None) or Path.cwd())


def _resolve_acp_root(args: argparse.Namespace) -> Path | None:
    explicit = getattr(args, "acp_root", None)
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_ACP_ROOT)
    return Path(env) if env else None


def _consumer_error(args: argparse.Namespace) -> dict[str, Any] | None:
    """Validate the optional consumer label; it is never persisted or echoed."""
    consumer = getattr(args, "consumer", None)
    if consumer is None:
        return None
    try:
        validate_identity(consumer, field_name="consumer")
    except SchemaError:
        return {"error": "consumer_invalid"}
    return None


def _refused(reason: str) -> int:
    _emit({"outcome": AdmitOutcome.REFUSED.value, "reason": reason})
    return EXIT_REFUSED


def cmd_bootstrap_git(args: argparse.Namespace) -> int:
    """Resolve an exact commit SHA locally and admit its body-free projection."""
    db_path = _resolve_db(args)
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_git_commit(args.sha, repo=_resolve_repo(args), namespace=args.namespace)
    except ResolutionError as exc:
        return _refused(exc.reason)
    try:
        result = ContextLinkStore(db_path).admit(resolution.link, resolution.verification, actor=args.actor)
    except (SchemaError, sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_REFUSED
    payload = result.to_dict()
    if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED):
        payload["excerpt"] = resolution.excerpt
    _emit(payload)
    return EXIT_OK if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED) else EXIT_REFUSED


def cmd_bootstrap_acp(args: argparse.Namespace) -> int:
    """Resolve an exact ACP conversation ID via the terminal receipt verifier."""
    db_path = _resolve_db(args)
    if _disabled():
        return _refused("projection_disabled")
    acp_root = _resolve_acp_root(args)
    if acp_root is None:
        return _refused("source_missing")
    try:
        resolution = resolve_acp_conversation(args.conversation_id, acp_root=acp_root, git_sha=args.git_sha)
    except ResolutionError as exc:
        return _refused(exc.reason)
    try:
        result = ContextLinkStore(db_path).admit(resolution.link, resolution.verification, actor=args.actor)
    except (SchemaError, sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_REFUSED
    payload = result.to_dict()
    if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED):
        payload["excerpt"] = resolution.excerpt
    _emit(payload)
    return EXIT_OK if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED) else EXIT_REFUSED


def cmd_search(args: argparse.Namespace) -> int:
    """search-past-work: ranked, re-verified, body-free locator cards."""
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    consumer_error = _consumer_error(args)
    if consumer_error is not None:
        _emit(consumer_error)
        return EXIT_REFUSED
    try:
        payload = search_past_work(
            ContextLinkStore(db_path),
            args.query,
            repo=_resolve_repo(args),
            acp_root=_resolve_acp_root(args),
            limit=args.limit,
            scan_limit=args.scan_limit,
        )
    except RecallInputError as exc:
        _emit({"error": str(exc)})
        return EXIT_REFUSED
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    payload.update({"enabled": True, "available": True})
    _emit(payload)
    return EXIT_OK


def cmd_explain_change(args: argparse.Namespace) -> int:
    """explain-change: typed provenance traversal from an exact seed ID."""
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    consumer_error = _consumer_error(args)
    if consumer_error is not None:
        _emit(consumer_error)
        return EXIT_REFUSED
    try:
        payload = explain_change(
            ContextLinkStore(db_path),
            locator_id=args.locator_id,
            canonical_id=args.canonical_id,
            git_sha=args.sha,
            repo=_resolve_repo(args),
            acp_root=_resolve_acp_root(args),
        )
    except RecallInputError as exc:
        _emit({"error": str(exc)})
        return EXIT_REFUSED
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    if not payload["found"]:
        _emit({"found": False})
        return EXIT_NOT_FOUND
    payload.update({"enabled": True, "available": True})
    _emit(payload)
    return EXIT_OK


def cmd_handoff(args: argparse.Namespace) -> int:
    """prepare-handoff: a bounded capsule of verified locators and excerpts."""
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_OK
    consumer_error = _consumer_error(args)
    if consumer_error is not None:
        _emit(consumer_error)
        return EXIT_REFUSED
    store = ContextLinkStore(db_path)
    locator_ids = list(args.locator_id or [])
    try:
        if args.query is not None:
            search = search_past_work(
                store,
                args.query,
                repo=_resolve_repo(args),
                acp_root=_resolve_acp_root(args),
                limit=MAX_RESULTS,
            )
            locator_ids.extend(card["locator_id"] for card in search["results"])
        if not locator_ids:
            raise RecallInputError("seed_invalid")
        capsule = prepare_handoff(
            store,
            locator_ids,
            repo=_resolve_repo(args),
            acp_root=_resolve_acp_root(args),
        )
    except RecallInputError as exc:
        _emit({"error": str(exc)})
        return EXIT_REFUSED
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(db_path, "projection_unreadable"))
        return EXIT_OK
    # The capsule is emitted as canonical JSON so the emitted serialization is
    # exactly the byte-capped one (<= 8 KiB) and always valid JSON.
    sys.stdout.write(canonical_json(capsule) + "\n")
    return EXIT_OK


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

    rebuild = sub.add_parser(
        "rebuild",
        help="Replay the event log; refuse unreadable input because rebuild mutates projection state",
    )
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

    def add_resolution_flags(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--repo",
            default=None,
            help="Local git repository used for commit re-resolution (default: cwd)",
        )
        command.add_argument(
            "--acp-root",
            default=None,
            help=f"ACP receipt plane root (default: {ENV_ACP_ROOT}); required to verify ACP links",
        )
        command.add_argument(
            "--consumer",
            default=None,
            help="Optional harness label (codex, kimi, glm, ...); validated, never persisted or echoed",
        )

    bootstrap_git = sub.add_parser(
        "bootstrap-git",
        help="Resolve an exact commit SHA locally and admit its body-free projection",
    )
    bootstrap_git.add_argument("sha", help="Full 40-hex commit SHA")
    bootstrap_git.add_argument(
        "--namespace",
        default=None,
        help="Canonical namespace override (default: derived from remote.origin.url)",
    )
    bootstrap_git.add_argument("--repo", default=None, help="Local git repository (default: cwd)")
    bootstrap_git.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_git)
    bootstrap_git.set_defaults(func=cmd_bootstrap_git)

    bootstrap_acp = sub.add_parser(
        "bootstrap-acp",
        help="Resolve an exact ACP conversation ID through the terminal receipt verifier",
    )
    bootstrap_acp.add_argument("conversation_id", help="Canonical conversation_<32 hex> ID")
    bootstrap_acp.add_argument(
        "--git-sha",
        default=None,
        help=(
            "Optional exact commit SHA; admitted only when it matches the ACP "
            "conversation's canonical correlation digest"
        ),
    )
    bootstrap_acp.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_acp)
    bootstrap_acp.add_argument(
        "--acp-root",
        default=None,
        help=f"ACP receipt plane root (default: {ENV_ACP_ROOT})",
    )
    bootstrap_acp.set_defaults(func=cmd_bootstrap_acp)

    search = sub.add_parser(
        "search",
        help="search-past-work: ranked, re-verified, body-free locator cards (query never echoed)",
    )
    search.add_argument("--query", required=True, help="Bounded ranking needle (<= 256 UTF-8 bytes)")
    search.add_argument("--limit", type=int, default=MAX_RESULTS, help="Max results (cap 10)")
    search.add_argument(
        "--scan-limit",
        type=int,
        default=MAX_SCAN_ROWS,
        help="Max promoted rows scanned (cap 500)",
    )
    add_resolution_flags(search)
    add_db_flag(search)
    search.set_defaults(func=cmd_search)

    explain_cmd = sub.add_parser(
        "explain-change",
        help="explain-change: typed provenance traversal from an exact seed identifier",
    )
    seed = explain_cmd.add_mutually_exclusive_group(required=True)
    seed.add_argument("--locator-id", default=None, help="Deterministic clink_<sha256> locator ID")
    seed.add_argument("--canonical-id", default=None, help="Exact canonical identifier")
    seed.add_argument("--sha", default=None, help="Exact full 40-hex commit SHA")
    add_resolution_flags(explain_cmd)
    add_db_flag(explain_cmd)
    explain_cmd.set_defaults(func=cmd_explain_change)

    handoff = sub.add_parser(
        "handoff",
        help="prepare-handoff: bounded capsule of verified locators/excerpts (<= 5 items, <= 8 KiB)",
    )
    handoff.add_argument(
        "--locator-id",
        action="append",
        default=None,
        help="Promoted locator ID to include (repeatable, max 5 used)",
    )
    handoff.add_argument(
        "--query",
        default=None,
        help="Optional bounded ranking needle; top verified results seed the capsule",
    )
    add_resolution_flags(handoff)
    add_db_flag(handoff)
    handoff.set_defaults(func=cmd_handoff)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
