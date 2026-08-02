"""Provider-neutral CLI for the body-free context-link projection.

Phase-1 commands: ``status``, ``lookup``, ``explain``, ``rebuild``, ``admit``.
Phase-2 commands: ``bootstrap-git``, ``bootstrap-acp``, ``search``,
``explain-change``, ``handoff``. Live commands: ``reconcile-acp``,
``record-use``, and explicit ``refresh-provider-status``.

Recall and projection commands are local-only: none calls Entire, GitHub,
Fleet, ACP providers, Monitor, or the network. The explicit provider-status
refresh is the sole Entire CLI call and writes an allowlisted cache. Resolution
uses read-only local ``git`` plumbing and the body-free ACP terminal receipt
verifier. A missing or
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
from .paths import ENV_ACP_ROOT, acp_root, projection_path
from .provider import refresh_provider_status
from .recall import (
    MAX_RESULTS,
    MAX_SCAN_ROWS,
    RecallInputError,
    explain_change,
    prepare_handoff,
    search_past_work,
)
from .reconcile import MAX_RECONCILE_ROWS, reconcile_terminal_acp_receipts
from .resolvers import (
    DEFAULT_GATE_KIND,
    REASON_SOURCE_MISSING,
    ResolutionError,
    default_fleet_root,
    default_issue_cache,
    default_monitor_root,
    resolve_acp_conversation,
    resolve_fleet_receipt,
    resolve_formal_review,
    resolve_git_commit,
    resolve_github_issue,
    resolve_github_pr,
    resolve_monitor_run,
    resolve_rollover,
)
from .store import AdmitOutcome, ContextLinkStore

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_REFUSED = 2

ENV_DISABLED = "ENTIRE_CONTEXT_DISABLED"
ENV_ROLLOVER_ROOT = "ENTIRE_CONTEXT_ROLLOVER_ROOT"
ENV_FLEET_ROOT = "ENTIRE_CONTEXT_FLEET_ROOT"
ENV_MONITOR_ROOT = "ENTIRE_CONTEXT_MONITOR_ROOT"
ENV_ISSUE_CACHE = "ENTIRE_CONTEXT_ISSUE_CACHE"


def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _resolve_db(args: argparse.Namespace) -> Path:
    return projection_path(Path.cwd(), getattr(args, "db", None))


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


def _resolve_acp_root(args: argparse.Namespace) -> Path:
    return acp_root(_resolve_repo(args), getattr(args, "acp_root", None))


def _resolve_rollover_root(args: argparse.Namespace) -> Path | None:
    explicit = getattr(args, "rollover_root", None)
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_ROLLOVER_ROOT)
    return Path(env) if env else None


def _resolve_fleet_root(args: argparse.Namespace) -> Path | None:
    explicit = getattr(args, "fleet_root", None)
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_FLEET_ROOT)
    if env:
        return Path(env)
    return default_fleet_root(_resolve_repo(args))


def _resolve_monitor_root(args: argparse.Namespace) -> Path | None:
    explicit = getattr(args, "monitor_root", None)
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_MONITOR_ROOT)
    if env:
        return Path(env)
    return default_monitor_root(_resolve_repo(args))


def _resolve_issue_cache(args: argparse.Namespace) -> Path | None:
    explicit = getattr(args, "issue_cache", None)
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_ISSUE_CACHE)
    if env:
        return Path(env)
    return default_issue_cache(_resolve_repo(args))


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


def cmd_bootstrap_rollover(args: argparse.Namespace) -> int:
    """Resolve an exact (agent, lineage, rollover) triple through the registry verifier."""
    db_path = _resolve_db(args)
    if _disabled():
        return _refused("projection_disabled")
    rollover_root = _resolve_rollover_root(args)
    if rollover_root is None:
        return _refused(REASON_SOURCE_MISSING)
    try:
        resolution = resolve_rollover(
            args.agent,
            args.lineage_id,
            args.rollover_id,
            state_root=rollover_root,
        )
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


def _admit_typed_resolution(args: argparse.Namespace, resolution) -> int:
    """Admit a completed local typed resolution using the normal idempotent gate."""
    try:
        result = ContextLinkStore(_resolve_db(args)).admit(
            resolution.link,
            resolution.verification,
            actor=args.actor,
        )
    except (SchemaError, sqlite3.Error, KeyError, TypeError, ValueError):
        _emit(_unavailable_payload(_resolve_db(args), "projection_unreadable"))
        return EXIT_REFUSED
    payload = result.to_dict()
    if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED):
        payload["excerpt"] = resolution.excerpt
    _emit(payload)
    return EXIT_OK if result.outcome in (AdmitOutcome.PROMOTED, AdmitOutcome.ALREADY_PROMOTED) else EXIT_REFUSED


def cmd_bootstrap_github_issue(args: argparse.Namespace) -> int:
    """Resolve an exact open issue through the fresh local membership cache."""
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_github_issue(
            args.issue_number,
            cache_path=_resolve_issue_cache(args),
            repo=_resolve_repo(args),
            namespace=args.namespace,
        )
    except ResolutionError as exc:
        return _refused(exc.reason)
    return _admit_typed_resolution(args, resolution)


def cmd_bootstrap_github_pr(args: argparse.Namespace) -> int:
    """Resolve an exact reviewed local PR head and its durable publication."""
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_github_pr(
            args.repository,
            args.pr_number,
            args.head_sha,
            gate_kind=args.gate_kind,
            fleet_root=_resolve_fleet_root(args),
            repo=_resolve_repo(args),
        )
    except ResolutionError as exc:
        return _refused(exc.reason)
    return _admit_typed_resolution(args, resolution)


def cmd_bootstrap_formal_review(args: argparse.Namespace) -> int:
    """Resolve one completed, sealed local formal-review job."""
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_formal_review(args.review_id, fleet_root=_resolve_fleet_root(args))
    except ResolutionError as exc:
        return _refused(exc.reason)
    return _admit_typed_resolution(args, resolution)


def cmd_bootstrap_fleet_receipt(args: argparse.Namespace) -> int:
    """Resolve one terminal Fleet request row without reading its body fields."""
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_fleet_receipt(args.request_id, fleet_root=_resolve_fleet_root(args))
    except ResolutionError as exc:
        return _refused(exc.reason)
    return _admit_typed_resolution(args, resolution)


def cmd_bootstrap_monitor_run(args: argparse.Namespace) -> int:
    """Resolve one terminal Agent Process Monitor lease locally."""
    if _disabled():
        return _refused("projection_disabled")
    try:
        resolution = resolve_monitor_run(args.lease_token, monitor_root=_resolve_monitor_root(args))
    except ResolutionError as exc:
        return _refused(exc.reason)
    return _admit_typed_resolution(args, resolution)


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
            rollover_root=_resolve_rollover_root(args),
            fleet_root=_resolve_fleet_root(args),
            monitor_root=_resolve_monitor_root(args),
            issue_cache_path=_resolve_issue_cache(args),
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
            rollover_root=_resolve_rollover_root(args),
            fleet_root=_resolve_fleet_root(args),
            monitor_root=_resolve_monitor_root(args),
            issue_cache_path=_resolve_issue_cache(args),
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
                rollover_root=_resolve_rollover_root(args),
                fleet_root=_resolve_fleet_root(args),
                monitor_root=_resolve_monitor_root(args),
                issue_cache_path=_resolve_issue_cache(args),
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
            rollover_root=_resolve_rollover_root(args),
            fleet_root=_resolve_fleet_root(args),
            monitor_root=_resolve_monitor_root(args),
            issue_cache_path=_resolve_issue_cache(args),
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


def cmd_record_use(args: argparse.Namespace) -> int:
    """Persist an explicit agent attestation after verified recall informed work."""
    db_path, early = _guard(args)
    if early is not None:
        _emit(early)
        return EXIT_REFUSED
    try:
        receipt = ContextLinkStore(db_path).record_use(
            task_id=args.task_id,
            consumer=args.consumer,
            purpose=args.purpose,
            locator_ids=args.locator_id,
        )
    except (SchemaError, sqlite3.Error, KeyError, TypeError, ValueError):
        _emit({"outcome": "refused", "reason": "use_receipt_invalid"})
        return EXIT_REFUSED
    _emit({"outcome": "recorded", **receipt})
    return EXIT_OK


def cmd_reconcile_acp(args: argparse.Namespace) -> int:
    """Recover complete ACP terminal receipts missed by the live callback."""
    acp_root = _resolve_acp_root(args)
    payload = reconcile_terminal_acp_receipts(
        acp_root=acp_root,
        repo_root=_resolve_repo(args),
        db_path=_resolve_db(args),
        limit=args.limit,
        actor=args.actor,
    )
    _emit(payload)
    return EXIT_OK if payload["outcome"] == "reconciled" else EXIT_REFUSED


def cmd_refresh_provider_status(args: argparse.Namespace) -> int:
    """Explicitly refresh the sanitized Entire CLI cache used by Monitor."""
    payload = refresh_provider_status(_resolve_repo(args))
    _emit(payload)
    return EXIT_OK if payload.get("available") is True else EXIT_REFUSED


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
            help="Projection SQLite path (default: shared primary batch_state projection)",
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
            help=f"ACP receipt plane root (default: {ENV_ACP_ROOT}, then canonical Fleet root)",
        )
        command.add_argument(
            "--rollover-root",
            default=None,
            help=(
                f"Rollover registry state root (default: {ENV_ROLLOVER_ROOT}); "
                "required to resolve and re-verify rollover links"
            ),
        )
        command.add_argument(
            "--fleet-root",
            default=None,
            help=f"Fleet Comms root (default: {ENV_FLEET_ROOT} or shared primary batch_state)",
        )
        command.add_argument(
            "--monitor-root",
            default=None,
            help=f"Agent Monitor state root (default: {ENV_MONITOR_ROOT} or shared primary batch_state)",
        )
        command.add_argument(
            "--issue-cache",
            default=None,
            help=f"Issue-stream audit cache (default: {ENV_ISSUE_CACHE} or shared primary batch_state)",
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
        help=f"ACP receipt plane root (default: {ENV_ACP_ROOT}, then canonical Fleet root)",
    )
    bootstrap_acp.set_defaults(func=cmd_bootstrap_acp)

    bootstrap_rollover = sub.add_parser(
        "bootstrap-rollover",
        help="Resolve an exact (agent, lineage, rollover) triple through the registry verifier",
    )
    bootstrap_rollover.add_argument("--agent", required=True, help="Exact registry agent identifier")
    bootstrap_rollover.add_argument("--lineage-id", required=True, help="Exact registry lineage identifier")
    bootstrap_rollover.add_argument("--rollover-id", required=True, help="Exact registry rollover identifier")
    bootstrap_rollover.add_argument(
        "--rollover-root",
        default=None,
        help=f"Rollover registry state root (default: {ENV_ROLLOVER_ROOT})",
    )
    bootstrap_rollover.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_rollover)
    bootstrap_rollover.set_defaults(func=cmd_bootstrap_rollover)

    bootstrap_issue = sub.add_parser(
        "bootstrap-github-issue",
        help="Resolve one exact open issue from the fresh local membership cache",
    )
    bootstrap_issue.add_argument("issue_number", type=int, help="Exact positive GitHub issue number")
    bootstrap_issue.add_argument("--namespace", default=None, help="Canonical GitHub namespace override")
    bootstrap_issue.add_argument("--repo", default=None, help="Local git repository (default: cwd)")
    bootstrap_issue.add_argument("--issue-cache", default=None, help="Fresh local issue-stream-audit JSON cache")
    bootstrap_issue.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_issue)
    bootstrap_issue.set_defaults(func=cmd_bootstrap_github_issue)

    bootstrap_pr = sub.add_parser(
        "bootstrap-github-pr",
        help="Resolve an exact reviewed local PR head and durable publication receipt",
    )
    bootstrap_pr.add_argument("pr_number", type=int, help="Exact positive pull-request number")
    bootstrap_pr.add_argument("--head-sha", required=True, help="Exact local 40-hex reviewed commit")
    bootstrap_pr.add_argument("--repository", required=True, help="Exact owner/repository identity")
    bootstrap_pr.add_argument("--gate-kind", default=DEFAULT_GATE_KIND, help="Formal-review gate kind")
    bootstrap_pr.add_argument("--fleet-root", default=None, help="Fleet Comms root")
    bootstrap_pr.add_argument("--repo", default=None, help="Local git repository (default: cwd)")
    bootstrap_pr.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_pr)
    bootstrap_pr.set_defaults(func=cmd_bootstrap_github_pr)

    bootstrap_review = sub.add_parser(
        "bootstrap-formal-review",
        help="Resolve one completed sealed local formal-review job",
    )
    bootstrap_review.add_argument("review_id", help="Exact formal-review identifier")
    bootstrap_review.add_argument("--fleet-root", default=None, help="Fleet Comms root")
    bootstrap_review.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_review)
    bootstrap_review.set_defaults(func=cmd_bootstrap_formal_review)

    bootstrap_receipt = sub.add_parser(
        "bootstrap-fleet-receipt",
        help="Resolve one exact terminal Fleet request receipt",
    )
    bootstrap_receipt.add_argument("request_id", help="Exact Fleet request identifier")
    bootstrap_receipt.add_argument("--fleet-root", default=None, help="Fleet Comms root")
    bootstrap_receipt.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_receipt)
    bootstrap_receipt.set_defaults(func=cmd_bootstrap_fleet_receipt)

    bootstrap_monitor = sub.add_parser(
        "bootstrap-monitor-run",
        help="Resolve one exact terminal Agent Process Monitor lease",
    )
    bootstrap_monitor.add_argument("lease_token", help="Exact monitor lease token")
    bootstrap_monitor.add_argument("--monitor-root", default=None, help="Agent Monitor state root")
    bootstrap_monitor.add_argument("--actor", default="cli", help="Body-free actor identity")
    add_db_flag(bootstrap_monitor)
    bootstrap_monitor.set_defaults(func=cmd_bootstrap_monitor_run)

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

    record_use = sub.add_parser(
        "record-use",
        help="Record an explicit body-free attestation that verified recall informed a task",
    )
    record_use.add_argument("--task-id", required=True, help="Exact path-safe task identity")
    record_use.add_argument("--consumer", required=True, help="Harness identity (codex, kimi, glm, ...)")
    record_use.add_argument(
        "--purpose",
        required=True,
        help="Path-safe use category such as intake, architecture, implementation, or handoff",
    )
    record_use.add_argument(
        "--locator-id",
        action="append",
        required=True,
        help="Verified promoted locator that informed the task (repeatable, max 10)",
    )
    add_db_flag(record_use)
    record_use.set_defaults(func=cmd_record_use)

    reconcile_acp = sub.add_parser(
        "reconcile-acp",
        help="Idempotently project terminal COMPLETE ACP receipts missed by the live callback",
    )
    reconcile_acp.add_argument(
        "--acp-root",
        default=None,
        help=f"ACP receipt plane root (default: {ENV_ACP_ROOT}, then canonical Fleet root)",
    )
    reconcile_acp.add_argument("--repo", default=None, help="Repository/worktree used to resolve shared state")
    reconcile_acp.add_argument("--actor", default="acp-reconcile", help="Body-free actor identity")
    reconcile_acp.add_argument("--limit", type=int, default=MAX_RECONCILE_ROWS, help="Max receipts (cap 500)")
    add_db_flag(reconcile_acp)
    reconcile_acp.set_defaults(func=cmd_reconcile_acp)

    provider_status = sub.add_parser(
        "refresh-provider-status",
        help="Explicit bounded Entire 0.8.42 status probe; writes a sanitized local cache",
    )
    provider_status.add_argument("--repo", default=None, help="Source repository (default: cwd)")
    provider_status.set_defaults(func=cmd_refresh_provider_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
