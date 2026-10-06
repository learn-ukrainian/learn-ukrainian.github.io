"""Join public sources into a normalized Work projection."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.work import SOURCE_PUBLIC
from scripts.work.attention import _pr_check_state, apply_health_and_actions, attach_merge_evidence
from scripts.work.relations import (
    annotate_cycles,
    collect_missing_blocked_by_issue_numbers,
    detect_dependency_cycles,
    extract_body_relations,
    invert_relationships,
    issue_work_id,
    make_work_id,
    pr_work_id,
    resolve_live_blockers,
    review_work_id,
    task_work_id,
)
from scripts.work.schema import admit_projection_filters
from scripts.work.sources_public import (
    GH_ENUM_LIMIT,
    SectionResult,
    admit_public_repository_id,
    allowlist_stream_names,
    collect_public_sections,
    fetch_issue_states_batched,
    filter_public_delegate_tasks,
    private_capability_seam,
    private_source_envelope,
    public_source_envelope,
    registry_stream_names,
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


_AUDIT_MEMBERSHIP_KEYS = ("membership_complete", "incomplete_nodes", "effective_membership")
_SOURCE_HARD_FAIL = frozenset({"unavailable", "timeout"})
_PROJECTION_STALE_REASON = "projection_cache_past_freshness"


def _label_names(raw: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(raw, list):
        return names
    for entry in raw:
        if isinstance(entry, dict) and entry.get("name"):
            names.append(str(entry["name"]))
        elif isinstance(entry, str):
            names.append(entry)
    return names


def _assignee_logins(raw: Any) -> list[str]:
    logins: list[str] = []
    if not isinstance(raw, list):
        return logins
    for entry in raw:
        if isinstance(entry, dict) and entry.get("login"):
            logins.append(str(entry["login"]))
        elif isinstance(entry, str):
            logins.append(entry)
    return logins


def _membership_observation(
    streams: dict[str, Any] | None,
    section_status: str,
) -> tuple[bool, str, bool]:
    """Return ``(current, reason, certified_inventory)``.

    A certified inventory is a complete issue→stream map. Legacy public
    fixtures that only carry the published lists stay current without that
    certification, so existing homed/orphan fixtures keep their classification.
    """
    if section_status in {"unavailable", "timeout", "error"} or not isinstance(streams, dict):
        return False, "membership_source_unavailable", False
    if section_status == "stale" or streams.get("stale") or streams.get("status") == "stale":
        return False, "membership_stale", False
    if section_status in {"degraded", "truncated"}:
        return False, "membership_incomplete", False
    if streams.get("error") or streams.get("status") in {"no-cache", "unavailable", "timeout", "error"}:
        return False, "membership_source_unavailable", False
    if "membership_certified" in streams:
        if streams.get("membership_certified") is True:
            return True, "membership_certified", True
        return False, "membership_uncertified", False
    if any(key in streams for key in _AUDIT_MEMBERSHIP_KEYS):
        from scripts.orchestration.issue_stream_audit import membership_report_is_complete

        if membership_report_is_complete(streams):
            return True, "membership_certified", True
        return False, "membership_incomplete", False
    return True, "membership_observed", False


def _stream_index(streams: dict[str, Any] | None, *, section_status: str = "ok") -> dict[str, Any]:
    current, reason, certified = _membership_observation(streams, section_status)
    if not isinstance(streams, dict):
        return {
            "orphans": set(),
            "multi": {},
            "pending": set(),
            "titles": {},
            "membership": {},
            "epic_of": {},
            "fresh": False,
            "missing": True,
            "stale": section_status == "stale",
            "generated_at": None,
            "ok": None,
            "current": False,
            "membership_reason": reason,
            "certified_inventory": False,
        }
    known = registry_stream_names(streams)
    orphans = {int(o["number"]) for o in streams.get("orphans") or [] if isinstance(o, dict) and "number" in o}
    multi: dict[int, list[str]] = {}
    for m in streams.get("multi_homed") or []:
        if not isinstance(m, dict) or "number" not in m:
            continue
        # Keep the multi_homed classification even when every name is unknown —
        # drop the bogus lanes, do not silently reclassify the issue as homed.
        multi[int(m["number"])] = allowlist_stream_names(m.get("streams"), known)
    pending_raw = streams.get("pending_native_link") or []
    pending: set[int] = set()
    for entry in pending_raw:
        if isinstance(entry, dict) and "number" in entry:
            pending.add(int(entry["number"]))
        elif isinstance(entry, int):
            pending.add(entry)
    # Public-safe open-issue→stream-names map (#6880/#6890) and the registry's
    # epic→stream map; both power stream-scoped pick lists in /next. Stream
    # names are re-allowlisted against the registry keys on every build.
    membership: dict[int, list[str]] = {}
    for key, names in (streams.get("open_stream_membership") or {}).items():
        try:
            number = int(key)
        except (TypeError, ValueError):
            continue
        clean = allowlist_stream_names(names, known)
        if clean:
            membership[number] = clean
    epic_of: dict[int, str] = {}
    registry = streams.get("streams")
    if isinstance(registry, dict):
        for name, epics in registry.items():
            if not isinstance(name, str) or not name:
                continue
            for epic in epics or []:
                try:
                    epic_of[int(epic)] = name
                except (TypeError, ValueError):
                    continue
    missing = bool(streams.get("error") or streams.get("status") == "no-cache")
    stale = bool(streams.get("stale") or section_status == "stale")
    return {
        "orphans": orphans,
        "multi": multi,
        "pending": pending,
        "membership": membership,
        "epic_of": epic_of,
        "fresh": not missing and not stale and current,
        "missing": missing,
        "stale": stale,
        "generated_at": streams.get("generated_at"),
        "ok": streams.get("ok"),
        "current": current,
        "membership_reason": reason,
        "certified_inventory": certified,
    }


def _runtime_age(task: dict[str, Any]) -> float | None:
    age = task.get("age_s")
    if isinstance(age, bool) or not isinstance(age, (int, float)):
        return None
    return float(age)


def _dispatch_from_tasks(
    tasks: list[dict[str, Any]],
    *,
    unresolved: bool,
    association_reason: str | None = None,
) -> dict[str, Any]:
    # One filtered list, so a task with no status cannot shift the alive
    # flag of a later running task onto the wrong index.
    observed_tasks = [task for task in tasks if task.get("status")]
    projection: dict[str, Any] = {
        "task_ids": [str(task.get("task_id")) for task in tasks if task.get("task_id")],
        "statuses": [str(task.get("status")) for task in observed_tasks],
        "alive": [task.get("alive") if "alive" in task else None for task in observed_tasks],
        "runtime_age_s": [_runtime_age(task) for task in tasks],
        "unresolved": unresolved,
        "agents": [str(task.get("agent")) for task in tasks if task.get("agent")],
        "accountable_owner": "unknown",
        "owner_reason": "owner_unknown",
    }
    if association_reason is not None:
        projection["association_reason"] = association_reason
    return projection


def _task_issue_links(task: dict[str, Any]) -> list[tuple[int, str]] | None:
    """DoR issue links, or None when the task has no canonical association field."""
    if "linked_issues" not in task:
        return None
    raw = task.get("linked_issues")
    links: list[tuple[int, str]] = []
    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            try:
                number = int(entry.get("issue"))
            except (TypeError, ValueError):
                continue
            repository = entry.get("repository")
            if isinstance(repository, str) and repository and number > 0:
                links.append((number, repository))
    return links


def _match_dispatch(
    tasks: list[dict[str, Any]],
    *,
    repository_id: str,
    issue_number: int | None,
) -> dict[str, Any]:
    """Attach tasks only by the DoR-checked issue association.

    Task-name suffixes are not an authority. A task whose name contains an
    issue or PR number stays unlinked until ``linked_issues`` says so.
    """
    matched: list[dict[str, Any]] = []
    if issue_number is not None:
        for task in tasks:
            links = _task_issue_links(task)
            if not links:
                continue
            if any(number == issue_number and repo == repository_id for number, repo in links):
                matched.append(task)
    return _dispatch_from_tasks(matched, unresolved=False)


def _historical_stream(number: int, stream_idx: dict[str, Any]) -> tuple[str, list[str]]:
    if number in stream_idx["multi"]:
        return "multi_homed", list(stream_idx["multi"][number])
    if number in stream_idx["orphans"]:
        return "orphan", []
    if number in stream_idx["pending"]:
        return "pending_native", list(stream_idx.get("membership", {}).get(number, []))
    if number in stream_idx.get("epic_of", {}):
        return "epic", [stream_idx["epic_of"][number]]
    if stream_idx["missing"]:
        return "unknown", []
    return "homed", list(stream_idx.get("membership", {}).get(number, []))


def _issue_stream_view(number: int, stream_idx: dict[str, Any]) -> dict[str, Any]:
    """Current membership, or unknown with the reason the map cannot be used."""
    historical_status, historical_streams = _historical_stream(number, stream_idx)
    view: dict[str, Any] = {
        "fresh": bool(stream_idx.get("fresh", False)),
        "authority_missing": bool(stream_idx.get("missing", False)),
        "stale": bool(stream_idx.get("stale") or not stream_idx.get("current")),
    }
    certified = bool(stream_idx.get("certified_inventory"))
    absent = certified and historical_status == "homed" and number not in stream_idx.get("membership", {})
    if not stream_idx.get("current") or absent:
        view["status"] = "unknown"
        view["streams"] = []
        view["membership_reason"] = (
            "absent_from_certified_inventory" if absent else stream_idx.get("membership_reason") or "membership_unknown"
        )
        view["historical_status"] = historical_status
        view["historical_streams"] = historical_streams
        view["fresh"] = False
        return view
    view["status"] = historical_status
    view["streams"] = historical_streams
    return view


def _match_reviews(reviews: list[dict[str, Any]], *, pr_number: int | None, repository_id: str) -> dict[str, Any]:
    if pr_number is None:
        return {
            "review_ids": [],
            "states": [],
            "sealed_verdict_available": False,
            "review_decision": None,
        }
    # Exact repository match only — never suffix/owner-agnostic matching, and
    # never treat a missing repository as public.
    matched = [
        r
        for r in reviews
        if int(r.get("pr_number") or 0) == pr_number and str(r.get("repository") or "") == repository_id
    ]
    return {
        "review_ids": [str(r.get("review_id")) for r in matched if r.get("review_id")],
        "states": [str(r.get("state")) for r in matched if r.get("state")],
        "sealed_verdict_available": any(bool(r.get("sealed_verdict_available")) for r in matched),
        "latest_attempt_states": [str(r.get("latest_attempt_state")) for r in matched if r.get("latest_attempt_state")],
    }


def _authority(
    domain: str,
    *,
    observed_at: str | None,
    age_s: float | None,
    stale: bool,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "observed_at": observed_at,
        "age_s": age_s,
        "stale": stale,
    }


def _authority_from_section(domain: str, section: SectionResult | None) -> dict[str, Any]:
    """Section observation age. A missing section is stale with a null age, never ``0``."""
    if section is None:
        return _authority(domain, observed_at=None, age_s=None, stale=True)
    return _authority(
        domain,
        observed_at=section.observed_at,
        age_s=section.age_s,
        stale=section.status not in {"ok", "truncated"},
    )


def _section_source_ok(section: SectionResult | None) -> bool:
    return section is not None and section.status not in _SOURCE_HARD_FAIL


def _build_issue_item(
    raw: dict[str, Any],
    *,
    repository_id: str,
    stream_idx: dict[str, Any],
    tasks: list[dict[str, Any]],
    section_times: dict[str, SectionResult],
) -> dict[str, Any]:
    number = int(raw["number"])
    body = raw.get("body") if isinstance(raw.get("body"), str) else None
    relations = extract_body_relations(body, repository_id=repository_id, self_number=number)
    # Body is used only for relation extraction; never retained.
    # Native sub-issue migration that is still pending keeps the epic-body
    # lane when the membership observation is current. A stale or uncertified
    # map never classifies the issue, including as orphan or multi-homed.
    stream_view = _issue_stream_view(number, stream_idx)
    dispatch = _match_dispatch(tasks, repository_id=repository_id, issue_number=number)
    issues_section = section_times.get("issues")
    streams_section = section_times.get("streams")
    delegate_section = section_times.get("delegate_tasks")
    return {
        "work_id": issue_work_id(repository_id, number),
        "source_id": SOURCE_PUBLIC,
        "repository_id": repository_id,
        "resource_kind": "issue",
        "remote_id": str(number),
        "title": str(raw.get("title") or ""),
        "lifecycle": str(raw.get("state") or "open").lower(),
        "labels": _label_names(raw.get("labels")),
        "assignees": _assignee_logins(raw.get("assignees")),
        "urls": {"html": raw.get("url")},
        "timestamps": {
            "created_at": raw.get("createdAt"),
            "updated_at": raw.get("updatedAt"),
        },
        "projections": {
            "stream": stream_view,
            "dispatch": dispatch,
            "review": {
                "review_ids": [],
                "states": [],
                "sealed_verdict_available": False,
            },
            "verification": {"kind": "none", "state": "n/a"},
        },
        "relationships": relations,
        "health": "UNKNOWN",
        "attention_rank": 0,
        "safe_next_action": {"code": "NONE", "reason_codes": []},
        "authority": [
            _authority_from_section("github", issues_section),
            _authority_from_section("streams", streams_section),
            _authority_from_section("delegate", delegate_section),
        ],
        "omissions": [],
        "flags": {
            # Provisional — `resolve_live_blockers` (post-inversion, in
            # `build_projection`) overwrites this once closed targets are
            # known and inferred inbound `blocks` edges have landed.
            "has_blocker": any(r["type"] == "blocked_by" for r in relations),
            "is_duplicate": any(r["type"] == "duplicate_of" for r in relations),
            "is_superseded": any(r["type"] == "superseded_by" for r in relations),
        },
    }


def _build_pr_item(
    raw: dict[str, Any],
    *,
    repository_id: str,
    tasks: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    section_times: dict[str, SectionResult],
) -> dict[str, Any]:
    number = int(raw["number"])
    is_draft = bool(raw.get("isDraft"))
    lifecycle = "draft" if is_draft else str(raw.get("state") or "open").lower()
    ci_state = _pr_check_state(raw)
    review_proj = _match_reviews(reviews, pr_number=number, repository_id=repository_id)
    review_proj["review_decision"] = raw.get("reviewDecision")
    # Task rows stay on the call so the builder signature is unchanged. A PR
    # number inside a task name is not an association.
    if not isinstance(tasks, list):
        tasks = []
    del tasks
    dispatch = _dispatch_from_tasks([], unresolved=False)
    prs_section = section_times.get("prs")
    reviews_section = section_times.get("fleet_reviews")
    return {
        "work_id": pr_work_id(repository_id, number),
        "source_id": SOURCE_PUBLIC,
        "repository_id": repository_id,
        "resource_kind": "pr",
        "remote_id": str(number),
        "title": str(raw.get("title") or ""),
        "lifecycle": lifecycle,
        "labels": _label_names(raw.get("labels")),
        "assignees": _assignee_logins(raw.get("assignees")),
        "urls": {"html": raw.get("url")},
        "timestamps": {
            "created_at": raw.get("createdAt"),
            "updated_at": raw.get("updatedAt"),
        },
        "projections": {
            "stream": {"status": "n/a", "fresh": True, "authority_missing": False},
            "dispatch": dispatch,
            "review": review_proj,
            "verification": {
                "kind": "gh_checks",
                "state": ci_state,
                "ci_state": ci_state,
                "merge_state_status": raw.get("mergeStateStatus"),
                "head_sha": raw.get("headRefOid"),
                "head_ref": raw.get("headRefName"),
            },
        },
        "relationships": [],
        "health": "UNKNOWN",
        "attention_rank": 0,
        "safe_next_action": {"code": "NONE", "reason_codes": []},
        "authority": [
            _authority_from_section("github", prs_section),
            _authority_from_section("fleet_reviews", reviews_section),
        ],
        "omissions": [],
        "flags": {
            "is_draft": is_draft,
            "has_blocker": False,
        },
    }


def _build_unlinked_tasks(
    tasks: list[dict[str, Any]],
    *,
    repository_id: str,
    linked_task_ids: set[str],
    section: SectionResult | None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        if not task_id or task_id in linked_task_ids:
            continue
        links = _task_issue_links(task)
        association_reason = "no_canonical_issue_association" if links is None else "unmatched_issue_association"
        items.append(
            {
                "work_id": task_work_id(repository_id, task_id),
                "source_id": SOURCE_PUBLIC,
                "repository_id": repository_id,
                "resource_kind": "task",
                "remote_id": task_id,
                "title": f"delegate:{task_id}",
                "lifecycle": str(task.get("status") or "unknown"),
                "labels": [],
                "assignees": [str(task["agent"])] if task.get("agent") else [],
                "urls": {"html": None},
                "timestamps": {
                    "created_at": task.get("started_at"),
                    "updated_at": task.get("started_at"),
                },
                "projections": {
                    "stream": {"status": "n/a", "authority_missing": False, "fresh": True},
                    "dispatch": _dispatch_from_tasks(
                        [task],
                        unresolved=True,
                        association_reason=association_reason,
                    ),
                    "review": {
                        "review_ids": [],
                        "states": [],
                        "sealed_verdict_available": False,
                    },
                    "verification": {"kind": "none", "state": "n/a"},
                },
                "relationships": [],
                "health": "UNKNOWN",
                "attention_rank": 0,
                "safe_next_action": {"code": "NONE", "reason_codes": []},
                "authority": [_authority_from_section("delegate", section)],
                "omissions": [
                    {
                        "class": "github_relation",
                        "reason": association_reason,
                        "count": 1,
                    }
                ],
                "flags": {"unresolved_github_relation": True},
            }
        )
    return items


def _build_unlinked_reviews(
    reviews: list[dict[str, Any]],
    *,
    repository_id: str,
    linked_review_ids: set[str],
    open_pr_numbers: set[int],
    section: SectionResult | None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for review in reviews:
        review_id = str(review.get("review_id") or "")
        if not review_id or review_id in linked_review_ids:
            continue
        # Public projection admits only the exact configured repository; never
        # emit a supplied non-public repository_id from an unlinked review row.
        if str(review.get("repository") or "") != repository_id:
            continue
        pr_number = review.get("pr_number")
        # Still surface formal-review jobs whose PR is not in the open list
        # (merged residual path uses R1 only for foundation).
        if pr_number is not None and int(pr_number) in open_pr_numbers:
            continue
        items.append(
            {
                "work_id": review_work_id(repository_id, review_id),
                "source_id": SOURCE_PUBLIC,
                "repository_id": repository_id,
                "resource_kind": "review",
                "remote_id": review_id,
                "title": f"formal-review:{review_id}",
                "lifecycle": str(review.get("state") or "unknown"),
                "labels": [str(review["gate_kind"])] if review.get("gate_kind") else [],
                "assignees": [],
                "urls": {"html": None},
                "timestamps": {
                    "created_at": review.get("created_at"),
                    "updated_at": review.get("created_at"),
                },
                "projections": {
                    "stream": {"status": "n/a", "authority_missing": False, "fresh": True},
                    "dispatch": {
                        "task_ids": [],
                        "statuses": [],
                        "unresolved": False,
                    },
                    "review": {
                        "review_ids": [review_id],
                        "states": [str(review.get("state") or "")],
                        "sealed_verdict_available": bool(review.get("sealed_verdict_available")),
                        "pr_number": pr_number,
                        "head_sha": review.get("head_sha"),
                    },
                    "verification": {
                        "kind": "formal_review",
                        "state": str(review.get("latest_attempt_state") or review.get("state") or ""),
                    },
                },
                "relationships": (
                    [
                        {
                            "type": "related",
                            "target_id": pr_work_id(repository_id, int(pr_number)),
                            "evidence": "fleet_review_pr_number",
                        }
                    ]
                    if pr_number is not None
                    else []
                ),
                "health": "UNKNOWN",
                "attention_rank": 0,
                "safe_next_action": {"code": "NONE", "reason_codes": []},
                "authority": [_authority_from_section("fleet_reviews", section)],
                "omissions": [],
                "flags": {},
            }
        )
    return items


def apply_filters(items: list[dict[str, Any]], filters: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not filters:
        return items
    out = items
    if "health" in filters:
        allowed = set(filters["health"])
        out = [i for i in out if i.get("health") in allowed]
    if "resource_kind" in filters:
        allowed = set(filters["resource_kind"])
        out = [i for i in out if i.get("resource_kind") in allowed]
    if "lifecycle" in filters:
        allowed = set(filters["lifecycle"])
        out = [i for i in out if i.get("lifecycle") in allowed]
    if "repository_id" in filters:
        allowed = set(filters["repository_id"])
        out = [i for i in out if i.get("repository_id") in allowed]
    if "source_id" in filters:
        allowed = set(filters["source_id"])
        out = [i for i in out if i.get("source_id") in allowed]
    if "orphan" in filters:
        want = bool(filters["orphan"])
        out = [
            i for i in out if bool(((i.get("projections") or {}).get("stream") or {}).get("status") == "orphan") is want
        ]
    return out


def build_projection(
    sections: dict[str, SectionResult],
    *,
    repository_id: str | None = None,
    filters: dict[str, Any] | None = None,
    cache_age_s: float = 0.0,
    target_lifecycle_lookup: Callable[..., dict[str | int, str]] | dict[str | int, str] | None = None,
    gh_runner: Callable[[list[str], float], tuple[int, str, str]] | None = None,
    lifecycle_ledgers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    repo = admit_public_repository_id(repository_id)
    # Projection boundary: every filter path (HTTP, direct call, cache key) must
    # re-enter the shared saved-view admission gate before filter/echo.
    canonical_filters = admit_projection_filters(filters)
    issues_section = sections.get("issues") or SectionResult("issues", "unavailable")
    prs_section = sections.get("prs") or SectionResult("prs", "unavailable")
    streams_section = sections.get("streams") or SectionResult("streams", "unavailable")
    active_section = sections.get("delegate_active") or SectionResult("delegate_active", "unavailable")
    tasks_section = sections.get("delegate_tasks") or SectionResult("delegate_tasks", "unavailable")
    reviews_section = sections.get("fleet_reviews") or SectionResult("fleet_reviews", "unavailable")

    stream_idx = _stream_index(
        streams_section.payload if streams_section.status != "unavailable" else None,
        section_status=streams_section.status,
    )
    tasks_payload = (tasks_section.payload or {}) if tasks_section.payload else {}
    active_payload = (active_section.payload or {}) if active_section.payload else {}
    # Prefer the broader inventory; merge active IDs that might not yet be in the list.
    # Re-admit at normalize so injected/bypass section payloads cannot attach
    # foreign or unclassified task IDs to public issues/PRs.
    raw_task_rows = list(tasks_payload.get("tasks") or [])
    seen_task_ids = {str(t.get("task_id")) for t in raw_task_rows if isinstance(t, dict) and t.get("task_id")}
    for row in active_payload.get("tasks") or []:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("task_id") or "")
        if tid and tid not in seen_task_ids:
            raw_task_rows.append(row)
            seen_task_ids.add(tid)
    task_rows, _task_total, _task_truncated = filter_public_delegate_tasks(raw_task_rows, repository_id=repo)
    review_rows = list((reviews_section.payload or {}).get("reviews") or [])

    items: list[dict[str, Any]] = []
    if isinstance(issues_section.payload, list):
        for raw in issues_section.payload:
            if isinstance(raw, dict) and raw.get("number") is not None:
                items.append(
                    _build_issue_item(
                        raw,
                        repository_id=repo,
                        stream_idx=stream_idx,
                        tasks=task_rows,
                        section_times=sections,
                    )
                )
    open_pr_numbers: set[int] = set()
    if isinstance(prs_section.payload, list):
        for raw in prs_section.payload:
            if isinstance(raw, dict) and raw.get("number") is not None:
                open_pr_numbers.add(int(raw["number"]))
                items.append(
                    _build_pr_item(
                        raw,
                        repository_id=repo,
                        tasks=task_rows,
                        reviews=review_rows,
                        section_times=sections,
                    )
                )

    linked_task_ids: set[str] = set()
    linked_review_ids: set[str] = set()
    for item in items:
        for tid in ((item.get("projections") or {}).get("dispatch") or {}).get("task_ids") or []:
            linked_task_ids.add(str(tid))
        for rid in ((item.get("projections") or {}).get("review") or {}).get("review_ids") or []:
            linked_review_ids.add(str(rid))

    items.extend(
        _build_unlinked_tasks(
            task_rows,
            repository_id=repo,
            linked_task_ids=linked_task_ids,
            section=tasks_section,
        )
    )
    items.extend(
        _build_unlinked_reviews(
            review_rows,
            repository_id=repo,
            linked_review_ids=linked_review_ids,
            open_pr_numbers=open_pr_numbers,
            section=reviews_section,
        )
    )

    invert_relationships(items)
    cycles = detect_dependency_cycles(items)
    annotate_cycles(items, cycles)
    # A closed target is not a live blocker (#7177/#7185) — must run after
    # inversion (covers inferred edges) and before health/action derivation.
    missing_numbers = collect_missing_blocked_by_issue_numbers(items, repository_id=repo)
    resolved_lifecycles: dict[str | int, str] = {}
    if target_lifecycle_lookup is not None:
        if isinstance(target_lifecycle_lookup, dict):
            resolved_lifecycles = target_lifecycle_lookup
        elif callable(target_lifecycle_lookup):
            try:
                resolved_lifecycles = target_lifecycle_lookup(missing_numbers, repo)
            except TypeError:
                resolved_lifecycles = target_lifecycle_lookup(missing_numbers)
    elif missing_numbers:
        resolved_lifecycles = fetch_issue_states_batched(
            missing_numbers,
            repository_id=repo,
            runner=gh_runner,
        )
    resolve_live_blockers(items, target_lifecycle_by_id=resolved_lifecycles)

    # Each row is qualified by its own section. A healthy PR section must not
    # make an unavailable issue look current, and a down GitHub must not erase
    # a live delegate observation. A missing flag fails closed.
    for item in items:
        kind = item.get("resource_kind")
        if kind == "issue":
            row_ok = _section_source_ok(issues_section)
        elif kind == "pr":
            row_ok = _section_source_ok(prs_section)
        elif kind == "task":
            row_ok = _section_source_ok(tasks_section)
        elif kind == "review":
            row_ok = _section_source_ok(reviews_section)
        else:
            row_ok = False
        item.setdefault("flags", {})["source_ok"] = row_ok
    # None means this build has no ledgers. Disk scans happen only in the
    # public wrapper, and a scan failure is an empty list rather than a 500.
    attach_merge_evidence(items, [] if lifecycle_ledgers is None else lifecycle_ledgers)
    attention = apply_health_and_actions(items, source_ok=False)
    filtered_items = apply_filters(items, canonical_filters or None)
    filtered_ids = {i["work_id"] for i in filtered_items}
    attention = [row for row in attention if row["work_id"] in filtered_ids]
    # Re-rank after filter for a dense attention list.
    for rank, row in enumerate(attention):
        row["attention_rank"] = rank
        for item in filtered_items:
            if item["work_id"] == row["work_id"]:
                item["attention_rank"] = rank
                break

    omissions: list[dict[str, Any]] = []
    if issues_section.truncated:
        omissions.append({"class": "issues", "reason": "enumeration_cap", "count": GH_ENUM_LIMIT})
    if prs_section.truncated:
        omissions.append({"class": "prs", "reason": "enumeration_cap", "count": GH_ENUM_LIMIT})
    if issues_section.status in {"unavailable", "timeout", "degraded"}:
        omissions.append(
            {
                "class": "issues",
                "reason": issues_section.reason or issues_section.status,
                "count": 0,
            }
        )
    if prs_section.status in {"unavailable", "timeout", "degraded"}:
        omissions.append(
            {
                "class": "prs",
                "reason": prs_section.reason or prs_section.status,
                "count": 0,
            }
        )
    if streams_section.status in {"unavailable", "timeout", "degraded", "stale"}:
        omissions.append(
            {
                "class": "streams",
                "reason": streams_section.reason or streams_section.status,
                "count": 0,
            }
        )
    if not stream_idx.get("current"):
        membership_reason = str(stream_idx.get("membership_reason") or "membership_unknown")
        unknown_issues = sum(
            1
            for item in items
            if item.get("resource_kind") == "issue"
            and ((item.get("projections") or {}).get("stream") or {}).get("status") == "unknown"
        )
        if not any(
            omission.get("class") == "streams" and omission.get("reason") == membership_reason for omission in omissions
        ):
            omissions.append(
                {
                    "class": "streams",
                    "reason": membership_reason,
                    "count": unknown_issues,
                }
            )
    for name, section in (
        ("delegate_active", active_section),
        ("delegate_tasks", tasks_section),
        ("fleet_reviews", reviews_section),
    ):
        if section.status not in {"ok", "truncated"}:
            omissions.append(
                {
                    "class": name,
                    "reason": section.reason or section.status,
                    "count": 0,
                }
            )
    omissions.append(
        {
            "class": "private_adapter",
            "reason": "not_configured",
            "count": 0,
        }
    )

    issues_open = issues_section.count if issues_section.status not in {"unavailable", "timeout"} else 0
    prs_open = prs_section.count if prs_section.status not in {"unavailable", "timeout"} else 0

    payload: dict[str, Any] = {
        "schema_version": "work-projection.v1",
        "generated_at": _iso_now(),
        "cache_age_s": float(cache_age_s),
        "budget": {"warm_target_s": 2, "timeout_s": 5},
        "sources": [
            public_source_envelope(sections),
            private_source_envelope(),
        ],
        "items": filtered_items,
        "attention": attention,
        "denominator": {
            "issues_open": issues_open,
            "prs_open": prs_open,
            "streams_complete": bool(
                streams_section.status == "ok" and stream_idx.get("current") and not stream_idx.get("stale")
            ),
            "class4": {
                "delegate_active": active_section.status in {"ok", "truncated"},
                "delegate_tasks": tasks_section.status in {"ok", "truncated"},
                "fleet_reviews": reviews_section.status in {"ok", "truncated"},
            },
            "omissions": omissions,
        },
        "capabilities": {
            "mutation": False,
            "private_source": private_capability_seam(),
        },
        "foundation_status": "FOUNDATION_COMPLETE",
    }
    if canonical_filters:
        payload["filters_applied"] = canonical_filters
    return payload


def build_public_projection(
    *,
    repository_id: str | None = None,
    filters: dict[str, Any] | None = None,
    cache_age_s: float = 0.0,
    target_lifecycle_lookup: Callable[..., dict[str | int, str]] | dict[str | int, str] | None = None,
    **collect_kwargs: Any,
) -> dict[str, Any]:
    # Admit filters at this entry point too so collect-only callers cannot
    # skip the shared saved-view gate when they only reach build_projection
    # after an expensive collect (fail closed early on foreign keys).
    canonical_filters = admit_projection_filters(filters)
    gh_runner = collect_kwargs.get("gh_runner")
    sections = collect_public_sections(repository_id=repository_id, **collect_kwargs)
    repo = admit_public_repository_id(repository_id)
    return build_projection(
        sections,
        repository_id=repository_id,
        filters=canonical_filters or None,
        cache_age_s=cache_age_s,
        target_lifecycle_lookup=target_lifecycle_lookup,
        gh_runner=gh_runner,
        lifecycle_ledgers=load_persisted_lifecycle_ledgers(repo),
    )


def load_persisted_lifecycle_ledgers(repository_id: str) -> list[dict[str, Any]]:
    """Read persisted lifecycle JSON for one repository.

    This is a local file read. It does not call the live observer, GitHub,
    ``reconcile``, or ``write_lifecycle``. Any failure yields no ledgers, and
    merge advice then stays unknown.
    """
    try:
        from scripts.orchestration.task_lifecycle import canonical_state_root

        root = canonical_state_root(Path(__file__).resolve().parents[2])
        digest = hashlib.sha256(repository_id.encode("utf-8")).hexdigest()[:16]
        directory = root / ".agent" / "task-lifecycle" / digest
        if not directory.is_dir():
            return []
        ledgers: list[dict[str, Any]] = []
        for path in sorted(directory.glob("issue-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                ledgers.append(payload)
        return ledgers
    except Exception:
        return []


def downgrade_expired_projection(payload: dict[str, Any], *, age_s: float, freshness_s: float) -> dict[str, Any]:
    """Copy a cached projection and, past the freshness bound, drop decision fields.

    The cache object is not mutated. Within the bound the copy only refreshes
    ``cache_age_s``. Past it, health, next action, membership, CI, review, and
    merge evidence become unknown with an age reason. The row may stay visible
    as history.
    """
    out = copy.deepcopy(payload)
    out["cache_age_s"] = float(age_s)
    if age_s <= freshness_s:
        return out
    unknown_action = {
        "code": "INSPECT_UNKNOWN",
        "reason_codes": [_PROJECTION_STALE_REASON],
        "state": "unknown",
    }
    for item in out.get("items") or []:
        if not isinstance(item, dict):
            continue
        item["health"] = "UNKNOWN"
        item["safe_next_action"] = dict(unknown_action)
        flags = item.get("flags")
        if not isinstance(flags, dict):
            flags = {}
            item["flags"] = flags
        flags["attention"] = False
        projections = item.get("projections") if isinstance(item.get("projections"), dict) else {}
        stream = projections.get("stream") if isinstance(projections.get("stream"), dict) else None
        if stream is not None:
            status = stream.get("status")
            if status not in {None, "n/a", "unknown"}:
                stream.setdefault("historical_status", status)
            streams = stream.get("streams")
            if isinstance(streams, list) and streams:
                stream.setdefault("historical_streams", list(streams))
            stream["status"] = "unknown"
            stream["streams"] = []
            stream["membership_reason"] = _PROJECTION_STALE_REASON
            stream["fresh"] = False
            stream["stale"] = True
        verification = projections.get("verification") if isinstance(projections.get("verification"), dict) else None
        if verification is not None:
            if "ci_state" in verification:
                verification["ci_state"] = "unknown"
            if verification.get("kind") not in {None, "none"}:
                verification["state"] = "unknown"
            verification["merge_evidence"] = {"state": "unknown", "reason": _PROJECTION_STALE_REASON}
        review = projections.get("review") if isinstance(projections.get("review"), dict) else None
        if review is not None and "review_decision" in review:
            review["review_decision"] = "UNKNOWN"
        dispatch = projections.get("dispatch") if isinstance(projections.get("dispatch"), dict) else None
        if dispatch is not None and isinstance(dispatch.get("alive"), list):
            dispatch["alive"] = [None for _flag in dispatch["alive"]]
        for entry in item.get("authority") or []:
            if isinstance(entry, dict):
                entry["stale"] = True
    for row in out.get("attention") or []:
        if isinstance(row, dict):
            row["health"] = "UNKNOWN"
            row["safe_next_action"] = dict(unknown_action)
    denominator = out.get("denominator")
    if isinstance(denominator, dict):
        denominator["streams_complete"] = False
    return out


# Re-export identity helper for tests/docs.
__all__ = [
    "apply_filters",
    "build_projection",
    "build_public_projection",
    "downgrade_expired_projection",
    "load_persisted_lifecycle_ledgers",
    "make_work_id",
]
