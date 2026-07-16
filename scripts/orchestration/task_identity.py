"""Fleet-wide task identity and rollover title state machine."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

IDENTITY_SCHEMA_VERSION = "task-identity.v1"
TITLE_TRANSITION_SCHEMA_VERSION = "rollover-title-transition.v1"
VISIBLE_TITLE_MAX_CHARS = 60
DEFAULT_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
TERMINAL_GOALS = frozenset({"merge", "deploy", "certify"})
LEGACY_TERMINAL_GOAL = "unknown"
FALLBACK_CARRIERS = (
    "dispatch_record",
    "brief",
    "ledger",
    "inbox",
    "monitor_api",
    "final_receipt",
)
NATIVE_TITLE_HARNESSES = frozenset({"codex-app"})

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = _ROOT / "agents_extensions" / "shared" / "schemas" / "task-identity.v1.schema.json"
_IDENTITY_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_IDENTITY_VALIDATOR = Draft202012Validator(_IDENTITY_SCHEMA, format_checker=FormatChecker())

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
_RAW_RUNTIME_ID_RE = re.compile(r"^(?:lineage|rollover)-[a-z0-9-]+$", re.I)
_GENERATION_RE = re.compile(r"^(?:generation\s*|g)\d+$", re.I)
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_LINEAGE_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_GENERIC_TITLES = frozenset(
    {
        "replacement task",
        "resume rollover",
        "resume codex rollover",
        "codex continuation",
        "rollover",
    }
)


def _clean_text(value: str | None, label: str, *, maximum: int) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    if len(cleaned) > maximum:
        raise ValueError(f"{label} exceeds {maximum} characters")
    if any(ord(character) < 32 for character in cleaned):
        raise ValueError(f"{label} contains control characters")
    return cleaned


def _is_generic_or_identifier(value: str) -> bool:
    folded = value.casefold()
    return (
        folded in _GENERIC_TITLES
        or bool(_UUID_RE.fullmatch(value))
        or bool(_RAW_RUNTIME_ID_RE.fullmatch(value))
        or bool(_GENERATION_RE.fullmatch(value))
    )


def validate_semantic_title(value: str) -> str:
    title = _clean_text(value, "semantic title", maximum=240)
    if _is_generic_or_identifier(title):
        raise ValueError("semantic title must describe the task, not a generic label or runtime identifier")
    return title


def _bounded_visible_title(prefix: str, semantic_title: str) -> str:
    available = VISIBLE_TITLE_MAX_CHARS - len(prefix)
    if available < 2:
        raise ValueError("visible title prefix leaves no room for semantic context")
    rendered = semantic_title
    if len(rendered) > available:
        rendered = f"{rendered[: available - 1].rstrip()}…"
    return f"{prefix}{rendered}"


def visible_title(*, semantic_title: str, github_issue_number: int | None, task_family: str) -> str:
    semantic = validate_semantic_title(semantic_title)
    if not _SLUG_RE.fullmatch(task_family):
        raise ValueError("task family must be a lowercase hyphenated slug")
    prefix = f"#{github_issue_number} — " if github_issue_number is not None else f"{task_family} — "
    title = _bounded_visible_title(prefix, semantic)
    if _is_generic_or_identifier(title):
        raise ValueError("visible title is generic or identifier-only")
    return title


def _github_url(repository: str, kind: str, number: int | None) -> str | None:
    return f"https://github.com/{repository}/{kind}/{number}" if number is not None else None


def _check_exact_url(label: str, supplied: str | None, expected: str | None) -> str | None:
    if supplied is None:
        return expected
    cleaned = _clean_text(supplied, label, maximum=500)
    if cleaned != expected:
        raise ValueError(f"{label} does not match the repository and exact number")
    return cleaned


def build_identity(
    *,
    repository: str,
    stream_epic: int | None,
    stream_epic_url: str | None,
    github_issue_number: int | None,
    github_issue_url: str | None,
    semantic_title: str,
    task_family: str,
    role: str,
    predecessor_task_id: str,
    replacement_task_id: str | None,
    lineage_id: str,
    generation: int,
    terminal_goal: str,
    lifecycle_state: str = "prepared",
    migration_source: str = "explicit",
    legacy_fallback: bool = False,
) -> dict[str, Any]:
    repo = _clean_text(repository, "repository", maximum=200)
    semantic = validate_semantic_title(semantic_title)
    if stream_epic is not None and stream_epic < 1:
        raise ValueError("stream epic must be positive")
    if github_issue_number is not None and github_issue_number < 1:
        raise ValueError("GitHub issue number must be positive")
    if not isinstance(lineage_id, str) or not _LINEAGE_RE.fullmatch(lineage_id):
        raise ValueError("lineage ID must start with a lowercase letter and contain only lowercase letters, digits, or hyphens")
    epic_url = _check_exact_url("stream epic URL", stream_epic_url, _github_url(repo, "issues", stream_epic))
    issue_url = _check_exact_url(
        "GitHub issue URL", github_issue_url, _github_url(repo, "issues", github_issue_number)
    )
    rendered = visible_title(
        semantic_title=semantic,
        github_issue_number=github_issue_number,
        task_family=task_family,
    )
    carriers = {carrier: rendered for carrier in FALLBACK_CARRIERS}
    cleaned_terminal_goal = _clean_text(terminal_goal, "terminal goal", maximum=32).lower()
    allowed_terminal_goals = TERMINAL_GOALS | ({LEGACY_TERMINAL_GOAL} if legacy_fallback else set())
    if cleaned_terminal_goal not in allowed_terminal_goals:
        expected = ", ".join(sorted(allowed_terminal_goals))
        raise ValueError(f"terminal goal must be one of: {expected}")
    identity = {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "repository": repo,
        "stream_epic": stream_epic,
        "stream_epic_url": epic_url,
        "github_issue_number": github_issue_number,
        "github_issue_url": issue_url,
        "semantic_title": semantic,
        "visible_title": rendered,
        "task_family": task_family,
        "role": _clean_text(role, "role", maximum=100),
        "predecessor_task_id": _clean_text(predecessor_task_id, "predecessor task ID", maximum=256),
        "replacement_task_id": (
            _clean_text(replacement_task_id, "replacement task ID", maximum=256)
            if replacement_task_id is not None
            else None
        ),
        "lineage_id": lineage_id,
        "generation": generation,
        "terminal_goal": cleaned_terminal_goal,
        "lifecycle_state": lifecycle_state,
        "carriers": carriers,
        "migration": {
            "source": _clean_text(migration_source, "migration source", maximum=100),
            "legacy_fallback": legacy_fallback,
        },
    }
    validate_identity(identity)
    return identity


def validate_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    errors = sorted(_IDENTITY_VALIDATOR.iter_errors(identity), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise ValueError(f"task identity schema violation at {location}: {first.message}")
    expected = visible_title(
        semantic_title=str(identity["semantic_title"]),
        github_issue_number=identity.get("github_issue_number"),
        task_family=str(identity["task_family"]),
    )
    if identity["visible_title"] != expected:
        raise ValueError("visible title does not match the canonical semantic-title rendering")
    if any(value != expected for value in identity["carriers"].values()):
        raise ValueError("every task identity carrier must preserve the exact same visible title")
    if identity.get("github_issue_number") is None and identity.get("github_issue_url") is not None:
        raise ValueError("GitHub issue URL requires an issue number")
    if identity.get("github_issue_number") is not None and identity.get("stream_epic") is None:
        raise ValueError("a GitHub issue identity requires exactly one stream epic")
    if identity.get("stream_epic") is None and identity.get("stream_epic_url") is not None:
        raise ValueError("stream epic URL requires a stream epic number")
    if identity.get("terminal_goal") == LEGACY_TERMINAL_GOAL and not identity["migration"]["legacy_fallback"]:
        raise ValueError("unknown terminal goal is reserved for deterministic legacy migration")
    return deepcopy(dict(identity))


def default_harness(agent: str) -> str:
    return "codex-app" if agent in {"codex", "orchestrator"} else agent


def title_capabilities(harness: str) -> dict[str, bool]:
    normalized = _clean_text(harness, "harness", maximum=64).lower()
    if not _SLUG_RE.fullmatch(normalized):
        raise ValueError("harness must be a lowercase hyphenated slug")
    native = normalized in NATIVE_TITLE_HARNESSES
    return {"native_title_supported": native, "native_readback_supported": native}


def new_title_transition(*, harness: str, visible_title_value: str, prepared_at: str) -> dict[str, Any]:
    normalized_harness = _clean_text(harness, "harness", maximum=64).lower()
    capabilities = title_capabilities(normalized_harness)
    return {
        "schema_version": TITLE_TRANSITION_SCHEMA_VERSION,
        "harness": normalized_harness,
        **capabilities,
        "state": "awaiting_replacement_binding",
        "visible_title": visible_title_value,
        "replacement_task_id": None,
        "binding_receipt": None,
        "mutation_receipt": None,
        "readback_receipt": None,
        "fallback_receipt": None,
        "events": [
            {
                "kind": "identity_prepared",
                "at": prepared_at,
                "visible_title": visible_title_value,
            }
        ],
    }


def validate_title_transition(transition: Mapping[str, Any], identity: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "harness",
        "native_title_supported",
        "native_readback_supported",
        "state",
        "visible_title",
        "replacement_task_id",
        "binding_receipt",
        "mutation_receipt",
        "readback_receipt",
        "fallback_receipt",
        "events",
    }
    if set(transition) != required:
        raise ValueError("title transition has missing or unexpected fields")
    if transition["schema_version"] != TITLE_TRANSITION_SCHEMA_VERSION:
        raise ValueError("title transition schema version is unsupported")
    capabilities = title_capabilities(str(transition["harness"]))
    if transition["native_title_supported"] != capabilities["native_title_supported"]:
        raise ValueError("title transition overclaims native title support")
    if transition["native_readback_supported"] != capabilities["native_readback_supported"]:
        raise ValueError("title transition overclaims native readback support")
    if transition["visible_title"] != identity["visible_title"]:
        raise ValueError("title transition visible title does not match task identity")
    if transition["replacement_task_id"] != identity["replacement_task_id"]:
        raise ValueError("title transition replacement ID does not match task identity")
    if not isinstance(transition["events"], list):
        raise ValueError("title transition events must be a list")
    return deepcopy(dict(transition))


def _event_once(transition: dict[str, Any], *, kind: str, at: str, details: Mapping[str, Any]) -> None:
    if any(event.get("kind") == kind for event in transition["events"] if isinstance(event, dict)):
        return
    transition["events"].append({"kind": kind, "at": at, **dict(details)})


def _identity_lifecycle(identity: Mapping[str, Any], state: str) -> dict[str, Any]:
    updated = deepcopy(dict(identity))
    updated["lifecycle_state"] = state
    validate_identity(updated)
    return updated


def bind_replacement(
    identity: Mapping[str, Any],
    transition: Mapping[str, Any],
    *,
    replacement_task_id: str,
    evidence: str,
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_identity = validate_identity(identity)
    current_transition = validate_title_transition(transition, current_identity)
    task_id = _clean_text(replacement_task_id, "replacement task ID", maximum=256)
    proof = _clean_text(evidence, "replacement binding evidence", maximum=500)
    existing = current_identity.get("replacement_task_id")
    if existing is not None and existing != task_id:
        raise ValueError("replacement task ID does not match the exact persisted binding")
    if existing == task_id:
        return current_identity, current_transition
    current_identity["replacement_task_id"] = task_id
    current_transition["replacement_task_id"] = task_id
    current_transition["binding_receipt"] = {"task_id": task_id, "evidence": proof, "recorded_at": now}
    _event_once(
        current_transition,
        kind="replacement_bound",
        at=now,
        details={"replacement_task_id": task_id},
    )
    if current_transition["native_title_supported"]:
        current_transition["state"] = "awaiting_native_title"
        current_identity["lifecycle_state"] = "replacement_bound"
    else:
        current_transition["state"] = "fallback_recorded"
        current_transition["fallback_receipt"] = {
            "native_mutation_supported": False,
            "native_readback_supported": False,
            "attempted": False,
            "reason": "Harness has no exact native title mutation and readback adapter.",
            "visible_title": current_identity["visible_title"],
            "carriers": list(FALLBACK_CARRIERS),
            "recorded_at": now,
        }
        _event_once(
            current_transition,
            kind="unsupported_title_fallback_recorded",
            at=now,
            details={"replacement_task_id": task_id},
        )
        current_identity["lifecycle_state"] = "title_ready"
    validate_identity(current_identity)
    validate_title_transition(current_transition, current_identity)
    return current_identity, current_transition


def record_title_acknowledgement(
    identity: Mapping[str, Any],
    transition: Mapping[str, Any],
    *,
    replacement_task_id: str,
    succeeded: bool,
    evidence: str,
    error: str,
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_identity = validate_identity(identity)
    current_transition = validate_title_transition(transition, current_identity)
    if not current_transition["native_title_supported"]:
        raise ValueError("harness does not support native title mutation; record the honest fallback instead")
    if current_identity["replacement_task_id"] != replacement_task_id:
        raise ValueError("title acknowledgement replacement ID does not match the exact binding")
    proof = _clean_text(evidence, "native title evidence", maximum=500)
    prior = current_transition.get("mutation_receipt")
    if prior and prior.get("succeeded") is True and prior.get("task_id") == replacement_task_id:
        return current_identity, current_transition
    if prior and prior.get("succeeded") is succeeded and prior.get("task_id") == replacement_task_id:
        return current_identity, current_transition
    current_transition["mutation_receipt"] = {
        "task_id": replacement_task_id,
        "visible_title": current_identity["visible_title"],
        "succeeded": succeeded,
        "evidence": proof,
        "error": _clean_text(error, "native title error", maximum=500) if not succeeded else None,
        "recorded_at": now,
    }
    current_transition["state"] = "title_acknowledged" if succeeded else "title_mutation_failed"
    current_identity["lifecycle_state"] = "replacement_bound" if succeeded else "title_failed"
    _event_once(
        current_transition,
        kind="native_title_acknowledged" if succeeded else "native_title_failed",
        at=now,
        details={"replacement_task_id": replacement_task_id},
    )
    validate_identity(current_identity)
    validate_title_transition(current_transition, current_identity)
    return current_identity, current_transition


def record_title_readback(
    identity: Mapping[str, Any],
    transition: Mapping[str, Any],
    *,
    replacement_task_id: str,
    observed_title: str | None,
    succeeded: bool,
    evidence: str,
    error: str,
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_identity = validate_identity(identity)
    current_transition = validate_title_transition(transition, current_identity)
    if not current_transition["native_readback_supported"]:
        raise ValueError("harness does not support exact native title readback")
    if current_identity["replacement_task_id"] != replacement_task_id:
        raise ValueError("title readback replacement ID does not match the exact binding")
    observed = str(observed_title) if observed_title is not None else None
    exact = succeeded and observed == current_identity["visible_title"]
    prior = current_transition.get("readback_receipt")
    if isinstance(prior, dict) and prior.get("exact_match") is True and prior.get("task_id") == replacement_task_id:
        return current_identity, current_transition
    current_transition["readback_receipt"] = {
        "task_id": replacement_task_id,
        "expected_title": current_identity["visible_title"],
        "observed_title": observed,
        "exact_match": exact,
        "evidence": _clean_text(evidence, "title readback evidence", maximum=500),
        "error": None if exact else _clean_text(error or "exact title readback failed", "readback error", maximum=500),
        "recorded_at": now,
        "acknowledgement_present": bool(
            current_transition.get("mutation_receipt", {}).get("succeeded")
            if isinstance(current_transition.get("mutation_receipt"), dict)
            else False
        ),
    }
    current_transition["state"] = "title_reconciled" if exact else "title_readback_failed"
    current_identity["lifecycle_state"] = "title_ready" if exact else "title_failed"
    _event_once(
        current_transition,
        kind="native_title_reconciled" if exact else "native_title_readback_failed",
        at=now,
        details={"replacement_task_id": replacement_task_id},
    )
    validate_identity(current_identity)
    validate_title_transition(current_transition, current_identity)
    return current_identity, current_transition


def assert_title_ready(
    identity: Mapping[str, Any], transition: Mapping[str, Any], *, replacement_task_id: str
) -> None:
    checked_identity = validate_identity(identity)
    checked_transition = validate_title_transition(transition, checked_identity)
    if checked_identity["replacement_task_id"] != replacement_task_id:
        raise ValueError("replacement ID does not match the task identity envelope")
    if checked_transition["native_title_supported"]:
        readback = checked_transition.get("readback_receipt")
        if checked_transition["state"] != "title_reconciled" or not isinstance(readback, dict):
            raise ValueError("native title acknowledgement without exact readback is not reconciled")
        if not readback.get("exact_match") or readback.get("task_id") != replacement_task_id:
            raise ValueError("native title readback does not prove the exact replacement and title")
    else:
        fallback = checked_transition.get("fallback_receipt")
        if checked_transition["state"] != "fallback_recorded" or not isinstance(fallback, dict):
            raise ValueError("unsupported harness has no honest title fallback receipt")
        if fallback.get("attempted") is not False or fallback.get("carriers") != list(FALLBACK_CARRIERS):
            raise ValueError("unsupported title fallback overclaims mutation or omits required carriers")


def mark_resumed(
    identity: Mapping[str, Any], transition: Mapping[str, Any], *, replacement_task_id: str
) -> dict[str, Any]:
    assert_title_ready(identity, transition, replacement_task_id=replacement_task_id)
    return _identity_lifecycle(identity, "resumed")


def mark_confirmed(
    identity: Mapping[str, Any], transition: Mapping[str, Any], *, replacement_task_id: str
) -> dict[str, Any]:
    assert_title_ready(identity, transition, replacement_task_id=replacement_task_id)
    return _identity_lifecycle(identity, "confirmed")


def _legacy_semantic_title(display: Mapping[str, Any]) -> tuple[str, str]:
    goal = " ".join(str(display.get("goal") or "").split())
    if goal and not _is_generic_or_identifier(goal):
        return goal, "legacy-v2-display-goal"
    existing = " ".join(str(display.get("title") or "").split())
    if (
        existing
        and not _is_generic_or_identifier(existing)
        and "lineage-" not in existing.casefold()
        and "rollover-" not in existing.casefold()
        and not _UUID_RE.search(existing)
    ):
        return existing, "legacy-v2-display-title"
    return "Recover predecessor task context", "legacy-v2-deterministic-fallback"


def backfill_legacy_identity(
    state: Mapping[str, Any], *, agent: str, repository: str, now: str
) -> tuple[dict[str, Any], bool]:
    replacement = state.get("replacement")
    if not isinstance(replacement, dict):
        return deepcopy(dict(state)), False
    if isinstance(replacement.get("identity"), dict) and isinstance(replacement.get("title_transition"), dict):
        validate_identity(replacement["identity"])
        validate_title_transition(replacement["title_transition"], replacement["identity"])
        return deepcopy(dict(state)), False

    active = state.get("active") or {}
    predecessor = str(active.get("thread_id") or "").strip()
    lineage_id = str(replacement.get("lineage_id") or state.get("lineage_id") or "").strip()
    generation = replacement.get("generation")
    if not predecessor or not lineage_id or not isinstance(generation, int) or generation < 1:
        raise ValueError("legacy rollover lacks the exact predecessor, lineage, or generation for identity backfill")
    display = replacement.get("display") if isinstance(replacement.get("display"), dict) else {}
    semantic, source = _legacy_semantic_title(display)
    native = replacement.get("native_lifecycle") if isinstance(replacement.get("native_lifecycle"), dict) else None
    replacement_id = (
        (native or {}).get("replacement_thread_id")
        or replacement.get("resumed_thread_id")
        or replacement.get("thread_id")
    )
    harness = f"{default_harness(agent)}-legacy"
    identity = build_identity(
        repository=repository,
        stream_epic=None,
        stream_epic_url=None,
        github_issue_number=None,
        github_issue_url=None,
        semantic_title=semantic,
        task_family="thread-rollover",
        role=agent,
        predecessor_task_id=predecessor,
        replacement_task_id=None,
        lineage_id=lineage_id,
        generation=generation,
        terminal_goal=LEGACY_TERMINAL_GOAL,
        migration_source=source,
        legacy_fallback=True,
    )
    transition = new_title_transition(
        harness=harness,
        visible_title_value=identity["visible_title"],
        prepared_at=str(replacement.get("prepared_at") or now),
    )
    if replacement_id:
        identity, transition = bind_replacement(
            identity,
            transition,
            replacement_task_id=str(replacement_id),
            evidence="Deterministic backfill from legacy lease replacement identity.",
            now=now,
        )
    updated = deepcopy(dict(state))
    updated_replacement = deepcopy(replacement)
    updated_replacement["identity"] = identity
    updated_replacement["title_transition"] = transition
    updated_replacement["display"] = {
        **dict(display),
        "title": identity["visible_title"],
        "title_source": source,
    }
    updated_replacement["identity_migrated_at"] = now
    updated["replacement"] = updated_replacement
    return updated, True


def safe_recommended_resolution(transition: Mapping[str, Any], *, rollover_id: str) -> str:
    state = transition.get("state")
    replacement_id = transition.get("replacement_task_id")
    if state == "awaiting_replacement_binding":
        return f"Bind the exact replacement for {rollover_id}; do not create or select by title."
    if state == "awaiting_native_title":
        return f"Request the exact native title action for {replacement_id}, then record and read back it."
    if state == "title_acknowledged":
        return f"Read back only the exact title for {replacement_id}; do not repeat the acknowledged mutation."
    if state in {"title_mutation_failed", "title_readback_failed"}:
        return f"Repair the exact title boundary for {replacement_id}; preserve every other rollover."
    if state in {"title_reconciled", "fallback_recorded"}:
        return f"Resume only {rollover_id} with exact replacement {replacement_id}."
    return f"Inspect the exact receipt for {rollover_id}; no automatic supersession is safe."


def candidate_diagnostic(
    state: Mapping[str, Any], replacement: Mapping[str, Any], *, state_file: str
) -> dict[str, Any]:
    identity = validate_identity(replacement["identity"])
    transition = validate_title_transition(replacement["title_transition"], identity)
    return {
        "repository": identity["repository"],
        "semantic_title": identity["semantic_title"],
        "visible_title": identity["visible_title"],
        "task_family": identity["task_family"],
        "role": identity["role"],
        "terminal_goal": identity["terminal_goal"],
        "identity_lifecycle_state": identity["lifecycle_state"],
        "issue": {
            "number": identity["github_issue_number"],
            "url": identity["github_issue_url"],
        },
        "stream_epic": {
            "number": identity["stream_epic"],
            "url": identity["stream_epic_url"],
        },
        "lineage_id": identity["lineage_id"],
        "generation": identity["generation"],
        "rollover_id": replacement.get("rollover_id"),
        "predecessor_task_id": identity["predecessor_task_id"],
        "replacement_task_id": identity["replacement_task_id"],
        "created_at": replacement.get("prepared_at"),
        "updated_at": state.get("updated_at") or replacement.get("resumed_at") or replacement.get("prepared_at"),
        "confirmation_state": replacement.get("status"),
        "title_confirmation_state": transition["state"],
        "identity_source": identity["migration"]["source"],
        "state_file": state_file,
        "safe_recommended_resolution": safe_recommended_resolution(
            transition, rollover_id=str(replacement.get("rollover_id") or "unknown")
        ),
    }


def receipt_payload(state: Mapping[str, Any]) -> dict[str, Any]:
    replacement = state.get("replacement") or {}
    identity = validate_identity(replacement["identity"])
    transition = validate_title_transition(replacement["title_transition"], identity)
    return {
        "schema_version": "rollover-identity-receipt.v1",
        "identity": identity,
        "title_transition": transition,
        "rollover_id": replacement.get("rollover_id"),
        "confirmation_state": replacement.get("status"),
        "updated_at": state.get("updated_at") or replacement.get("prepared_at"),
    }
