"""Join public sources into a normalized Work projection."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from scripts.work import SOURCE_PUBLIC
from scripts.work.attention import _pr_check_state, apply_health_and_actions
from scripts.work.relations import (
    annotate_cycles,
    detect_dependency_cycles,
    extract_body_relations,
    invert_relationships,
    issue_work_id,
    make_work_id,
    pr_work_id,
    review_work_id,
    task_work_id,
)
from scripts.work.schema import admit_projection_filters
from scripts.work.sources_public import (
    GH_ENUM_LIMIT,
    SectionResult,
    admit_public_repository_id,
    collect_public_sections,
    filter_public_delegate_tasks,
    private_capability_seam,
    private_source_envelope,
    public_source_envelope,
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def _stream_index(streams: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(streams, dict):
        return {
            "orphans": set(),
            "multi": {},
            "pending": set(),
            "titles": {},
            "fresh": False,
            "missing": True,
            "generated_at": None,
        }
    orphans = {int(o["number"]) for o in streams.get("orphans") or [] if isinstance(o, dict) and "number" in o}
    multi = {
        int(m["number"]): list(m.get("streams") or [])
        for m in streams.get("multi_homed") or []
        if isinstance(m, dict) and "number" in m
    }
    pending_raw = streams.get("pending_native_link") or []
    pending: set[int] = set()
    for entry in pending_raw:
        if isinstance(entry, dict) and "number" in entry:
            pending.add(int(entry["number"]))
        elif isinstance(entry, int):
            pending.add(entry)
    missing = bool(streams.get("error") or streams.get("status") == "no-cache")
    stale = bool(streams.get("stale"))
    return {
        "orphans": orphans,
        "multi": multi,
        "pending": pending,
        "fresh": not missing and not stale,
        "missing": missing,
        "stale": stale,
        "generated_at": streams.get("generated_at"),
        "ok": streams.get("ok"),
    }


def _has_bounded_issue_id(hay: str, number: int) -> bool:
    """True when hay contains an explicit issue id for *number* (not a longer id).

    Supported forms match the prior contract: ``#N``, ``issue-N``, ``issue_N``,
    path ``/N``, or a trailing ``-N``. A trailing non-digit (or end) after the
    number prevents ``#1`` from matching ``#19`` and ``issue-10`` from matching
    ``issue-100``.
    """
    n = str(int(number))
    return bool(
        re.search(rf"#{n}(?!\d)", hay)
        or re.search(rf"issue[-_]{n}(?!\d)", hay)
        or re.search(rf"/{n}(?!\d)", hay)
        or hay.endswith(f"-{n}")
    )


def _has_bounded_pr_id(hay: str, number: int) -> bool:
    """True when hay contains an explicit PR id for *number* (not a longer id).

    Supported forms match the prior contract: ``pr-N``, ``pr_N``, ``pr/N``, or
    trailing ``-prN``. A trailing non-digit (or end) after the number prevents
    ``pr-10`` from matching ``pr-100``.
    """
    n = str(int(number))
    return bool(
        re.search(rf"pr[-_/]{n}(?!\d)", hay)
        or hay.endswith(f"-pr{n}")
    )


def _match_dispatch(tasks: list[dict[str, Any]], *, issue_number: int | None, pr_number: int | None) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        hay = task_id.lower()
        if issue_number is not None and _has_bounded_issue_id(hay, issue_number):
            matched.append(task)
            continue
        if pr_number is not None and _has_bounded_pr_id(hay, pr_number):
            matched.append(task)
    return {
        "task_ids": [str(t.get("task_id")) for t in matched if t.get("task_id")],
        "statuses": [str(t.get("status")) for t in matched if t.get("status")],
        "unresolved": False,
        "agents": [str(t.get("agent")) for t in matched if t.get("agent")],
    }


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
        if int(r.get("pr_number") or 0) == pr_number
        and str(r.get("repository") or "") == repository_id
    ]
    return {
        "review_ids": [str(r.get("review_id")) for r in matched if r.get("review_id")],
        "states": [str(r.get("state")) for r in matched if r.get("state")],
        "sealed_verdict_available": any(bool(r.get("sealed_verdict_available")) for r in matched),
        "latest_attempt_states": [
            str(r.get("latest_attempt_state"))
            for r in matched
            if r.get("latest_attempt_state")
        ],
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
    if number in stream_idx["multi"]:
        stream_status = "multi_homed"
        epic_streams = stream_idx["multi"][number]
    elif number in stream_idx["orphans"]:
        stream_status = "orphan"
        epic_streams = []
    elif number in stream_idx["pending"]:
        stream_status = "pending_native"
        epic_streams = []
    elif stream_idx["missing"]:
        stream_status = "unknown"
        epic_streams = []
    else:
        stream_status = "homed"
        epic_streams = []

    dispatch = _match_dispatch(tasks, issue_number=number, pr_number=None)
    streams_section = section_times.get("streams")
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
            "stream": {
                "status": stream_status,
                "streams": epic_streams,
                "fresh": stream_idx.get("fresh", False),
                "authority_missing": stream_idx.get("missing", False),
                "stale": stream_idx.get("stale", False),
            },
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
            _authority(
                "github",
                observed_at=section_times.get("issues").observed_at if section_times.get("issues") else None,
                age_s=section_times.get("issues").age_s if section_times.get("issues") else 0.0,
                stale=False,
            ),
            _authority(
                "streams",
                observed_at=streams_section.observed_at if streams_section else None,
                age_s=streams_section.age_s if streams_section else None,
                stale=bool(stream_idx.get("stale") or stream_idx.get("missing")),
            ),
            _authority(
                "delegate",
                observed_at=section_times.get("delegate_tasks").observed_at
                if section_times.get("delegate_tasks")
                else None,
                age_s=0.0,
                stale=section_times.get("delegate_tasks", SectionResult("delegate_tasks", "unavailable")).status
                not in {"ok", "truncated"},
            ),
        ],
        "omissions": [],
        "flags": {
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
    dispatch = _match_dispatch(tasks, issue_number=None, pr_number=number)
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
            _authority(
                "github",
                observed_at=section_times.get("prs").observed_at if section_times.get("prs") else None,
                age_s=section_times.get("prs").age_s if section_times.get("prs") else 0.0,
                stale=False,
            ),
            _authority(
                "fleet_reviews",
                observed_at=section_times.get("fleet_reviews").observed_at
                if section_times.get("fleet_reviews")
                else None,
                age_s=0.0,
                stale=section_times.get("fleet_reviews", SectionResult("fleet_reviews", "unavailable")).status
                not in {"ok", "truncated"},
            ),
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
                    "dispatch": {
                        "task_ids": [task_id],
                        "statuses": [str(task.get("status") or "")],
                        "unresolved": True,
                        "agents": [str(task["agent"])] if task.get("agent") else [],
                    },
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
                "authority": [
                    _authority(
                        "delegate",
                        observed_at=section.observed_at if section else None,
                        age_s=section.age_s if section else 0.0,
                        stale=False,
                    )
                ],
                "omissions": [
                    {
                        "class": "github_relation",
                        "reason": "unresolved_github_relation",
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
                "authority": [
                    _authority(
                        "fleet_reviews",
                        observed_at=section.observed_at if section else None,
                        age_s=section.age_s if section else 0.0,
                        stale=False,
                    )
                ],
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
            i
            for i in out
            if bool(((i.get("projections") or {}).get("stream") or {}).get("status") == "orphan")
            is want
        ]
    return out


def build_projection(
    sections: dict[str, SectionResult],
    *,
    repository_id: str | None = None,
    filters: dict[str, Any] | None = None,
    cache_age_s: float = 0.0,
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

    stream_idx = _stream_index(streams_section.payload if streams_section.status != "unavailable" else None)
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
    task_rows, _task_total, _task_truncated = filter_public_delegate_tasks(
        raw_task_rows, repository_id=repo
    )
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

    # Source is "ok enough" for health when GH issue/PR sections did not hard-fail.
    source_ok = issues_section.status not in {"unavailable", "timeout"} or prs_section.status not in {
        "unavailable",
        "timeout",
    }
    attention = apply_health_and_actions(items, source_ok=source_ok)
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
        omissions.append(
            {"class": "issues", "reason": "enumeration_cap", "count": GH_ENUM_LIMIT}
        )
    if prs_section.truncated:
        omissions.append(
            {"class": "prs", "reason": "enumeration_cap", "count": GH_ENUM_LIMIT}
        )
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
            "streams_complete": streams_section.status in {"ok", "stale", "truncated"},
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
    **collect_kwargs: Any,
) -> dict[str, Any]:
    # Admit filters at this entry point too so collect-only callers cannot
    # skip the shared saved-view gate when they only reach build_projection
    # after an expensive collect (fail closed early on foreign keys).
    canonical_filters = admit_projection_filters(filters)
    sections = collect_public_sections(repository_id=repository_id, **collect_kwargs)
    return build_projection(
        sections,
        repository_id=repository_id,
        filters=canonical_filters or None,
        cache_age_s=cache_age_s,
    )


# Re-export identity helper for tests/docs.
__all__ = [
    "apply_filters",
    "build_projection",
    "build_public_projection",
    "make_work_id",
]
